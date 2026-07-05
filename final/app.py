from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime, date
from functools import wraps
import os, uuid, hmac, hashlib, requests as req_lib, json
from dotenv import load_dotenv
from models import (db, Hotel, Room, Booking, Guest, Payment, Amenity, Review,
                    BookingStatus, PaymentStatus, PaymentMethod)
from config import config

load_dotenv()
app = Flask(__name__)
env = os.environ.get('FLASK_ENV', 'production')
app.config.from_object(config.get(env, config['default']))
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=2, x_proto=2, x_host=1, x_prefix=1)

db.init_app(app)
mail = Mail(app)
csrf = CSRFProtect(app)

PHONE        = app.config['HOTEL_PHONE']
WHATSAPP_NUM = app.config['HOTEL_WHATSAPP']
GST_NUMBER   = app.config['HOTEL_GST']
HOTEL_EMAIL  = app.config.get('HOTEL_EMAIL', 'Hoteljhd@gmail.com')

# ─── SEASONAL PRICING ENGINE ──────────────────────────────────
def _parse_peak_ranges():
    """Parses 'MM-DD:MM-DD,MM-DD:MM-DD' into [(month,day,month,day), ...]"""
    raw = app.config.get('PEAK_SEASON_RANGES', '')
    ranges = []
    for part in raw.split(','):
        part = part.strip()
        if not part or ':' not in part:
            continue
        start_s, end_s = part.split(':')
        try:
            sm, sd = map(int, start_s.split('-'))
            em, ed = map(int, end_s.split('-'))
            ranges.append((sm, sd, em, ed))
        except ValueError:
            continue
    return ranges

def is_peak_season(check_date):
    """Returns True if the given date falls in any configured peak season range.
    Handles ranges that wrap across the calendar year (e.g. Nov -> Feb)."""
    ranges = _parse_peak_ranges()
    md = (check_date.month, check_date.day)
    for sm, sd, em, ed in ranges:
        start, end = (sm, sd), (em, ed)
        if start <= end:
            if start <= md <= end:
                return True
        else:  # range wraps the new year, e.g. Dec 1 -> Feb 28
            if md >= start or md <= end:
                return True
    return False

def get_price_for_date(check_date, room_type='Normal'):
    """The single source of truth for room pricing — automatically returns
    the peak or normal rate based on the check-in date, plus the Super
    Deluxe surcharge if applicable. No manual switching needed."""
    base = app.config['PEAK_PRICE'] if is_peak_season(check_date) else app.config['NORMAL_PRICE']
    peak = is_peak_season(check_date)
    if room_type == 'Super Deluxe':
        base += app.config['SUPER_DELUXE_EXTRA']
    return base, peak

# ─── Helpers ────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'guest_id' not in session:
            flash('Please sign in to continue.', 'info')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

def send_confirmation_email(booking):
    try:
        guest = booking.guest
        msg = Message(
            subject=f'Booking Confirmed — {booking.booking_reference} | JHD Hotel',
            recipients=[guest.email],
            html=f"""
            <div style="font-family:sans-serif;max-width:600px;margin:auto;padding:2rem;">
              <h2 style="color:#C0627A;">Booking Confirmed! 🌸</h2>
              <p>Dear {guest.first_name},</p>
              <p>Your booking at <strong>JHD Hotel &amp; Bar</strong> is confirmed.</p>
              <div style="background:#fde8ef;border-radius:8px;padding:1rem;margin:1.5rem 0;">
                <p><strong>Booking Reference:</strong> {booking.booking_reference}</p>
                <p><strong>Check-in:</strong> {booking.check_in_date.strftime('%d %b %Y')}</p>
                <p><strong>Check-out:</strong> {booking.check_out_date.strftime('%d %b %Y')}</p>
                <p><strong>Guests:</strong> {booking.num_adults} Adults, {booking.num_children} Children</p>
                <p><strong>Total Paid:</strong> ₹{booking.total_amount:,.0f} (incl. 12% GST)</p>
                <p><strong>GST No:</strong> {GST_NUMBER}</p>
              </div>
              <p>Check-in: 12:00 PM | Check-out: 11:00 AM</p>
              <p>📞 {PHONE} | WhatsApp: wa.me/{WHATSAPP_NUM}</p>
            </div>"""
        )
        mail.send(msg)
    except Exception:
        pass

# ─── PayPal Helpers ─────────────────────────────────────────
def get_paypal_token():
    mode   = app.config.get('PAYPAL_MODE', 'sandbox')
    base   = 'https://api-m.sandbox.paypal.com' if mode == 'sandbox' else 'https://api-m.paypal.com'
    cid    = app.config.get('PAYPAL_CLIENT_ID', '')
    secret = app.config.get('PAYPAL_CLIENT_SECRET', '')
    r = req_lib.post(f'{base}/v1/oauth2/token',
        auth=(cid, secret), data={'grant_type': 'client_credentials'},
        headers={'Accept': 'application/json'})
    return r.json().get('access_token'), base

def create_paypal_order(amount_inr, booking_ref):
    token, base = get_paypal_token()
    r = req_lib.post(f'{base}/v2/checkout/orders',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        json={
            'intent': 'CAPTURE',
            'purchase_units': [{
                'reference_id': booking_ref,
                'amount': {'currency_code': 'INR', 'value': str(round(amount_inr, 2))},
                'description': f'JHD Hotel Booking {booking_ref}'
            }],
        })
    return r.json()

def capture_paypal_order(order_id):
    token, base = get_paypal_token()
    r = req_lib.post(f'{base}/v2/checkout/orders/{order_id}/capture',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
    return r.json()

# ─── Main Routes ─────────────────────────────────────────────
@app.route('/')
def index():
    try:
        hotel = Hotel.query.first()
    except Exception:
        hotel = None
    today_price, _  = get_price_for_date(date.today(), 'Normal')
    today_price_sd, _ = get_price_for_date(date.today(), 'Super Deluxe')
    return render_template('index.html', hotel=hotel,
        today_price=today_price, today_price_sd=today_price_sd)

@app.route('/about')
def about_page():
    return render_template('about.html')

@app.route('/skybar')
def skybar_page():
    return render_template('skybar.html')

@app.route('/reviews')
def reviews_page():
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template('reviews.html', reviews=reviews)

# ─── Search / Rooms ──────────────────────────────────────────
@app.route('/search')
def search():
    try:
        hotel = Hotel.query.first()
        rooms = Room.query.filter_by(is_available=True).order_by(Room.room_type, Room.room_number).all() if hotel else []
    except Exception:
        hotel = None
        rooms = []
    check_in  = request.args.get('check_in', '')
    check_out = request.args.get('check_out', '')
    adults    = request.args.get('adults', '2')
    children  = request.args.get('children', '0')
    room_type_filter = request.args.get('room_type', 'all')

    if room_type_filter and room_type_filter != 'all':
        rooms = [r for r in rooms if r.room_type == room_type_filter]

    try:
        price_date = datetime.strptime(check_in, '%Y-%m-%d').date() if check_in else date.today()
    except ValueError:
        price_date = date.today()

    normal_price, is_peak = get_price_for_date(price_date, 'Normal')
    sd_price, _            = get_price_for_date(price_date, 'Super Deluxe')

    return render_template('search.html',
        hotel=hotel, rooms=rooms,
        check_in=check_in, check_out=check_out,
        adults=adults, children=children,
        room_type_filter=room_type_filter,
        normal_price=normal_price, sd_price=sd_price, is_peak=is_peak)

# ─── Booking ─────────────────────────────────────────────────
@app.route('/booking/<room_id>', methods=['GET', 'POST'])
def booking(room_id):
    room  = Room.query.get_or_404(room_id)
    hotel = Hotel.query.first()

    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            guest = Guest.query.filter_by(email=email).first()
            if not guest:
                guest = Guest(
                    first_name=request.form.get('first_name',''),
                    last_name=request.form.get('last_name',''),
                    email=email,
                    phone=request.form.get('phone',''),
                    nationality=request.form.get('nationality',''),
                    id_type=request.form.get('id_type',''),
                    id_number=request.form.get('id_number',''),
                    street_address=request.form.get('address',''),
                    city=request.form.get('city',''),
                    state=request.form.get('state',''),
                    country=request.form.get('country','India'),
                )
                db.session.add(guest)
                db.session.flush()

            ci = datetime.strptime(request.form.get('check_in'), '%Y-%m-%d').date()
            co = datetime.strptime(request.form.get('check_out'), '%Y-%m-%d').date()
            if co <= ci:
                flash('Check-out date must be after check-in date.', 'danger')
                return redirect(url_for('booking', room_id=room_id))

            # ── AUTOMATIC PRICE: based on check-in date + room type ──
            nightly_price, peak_flag = get_price_for_date(ci, room.room_type)

            new_booking = Booking(
                booking_reference = Booking.generate_reference(),
                room_id     = room.id,
                guest_id    = guest.id,
                check_in_date  = ci,
                check_out_date = co,
                num_adults  = int(request.form.get('num_adults', 2)),
                num_children= int(request.form.get('num_children', 0)),
                extra_bed   = 'extra_bed' in request.form,
                special_requests = request.form.get('special_requests', ''),
                price_per_night  = nightly_price,
                room_type        = room.room_type,
                is_peak_season   = peak_flag,
                status      = BookingStatus.PENDING,
            )
            new_booking.calculate_total()
            db.session.add(new_booking)
            db.session.commit()
            session['booking_id'] = new_booking.id
            return redirect(url_for('checkout', booking_id=new_booking.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating booking: {e}', 'danger')
            return redirect(url_for('booking', room_id=room_id))

    check_in  = request.args.get('check_in', '')
    check_out = request.args.get('check_out', '')
    adults    = request.args.get('adults', '2')
    children  = request.args.get('children', '0')

    try:
        price_date = datetime.strptime(check_in, '%Y-%m-%d').date() if check_in else date.today()
    except ValueError:
        price_date = date.today()
    live_price, is_peak = get_price_for_date(price_date, room.room_type)

    return render_template('booking.html',
        room=room, hotel=hotel,
        check_in=check_in, check_out=check_out,
        adults=adults, children=children,
        live_price=live_price, is_peak=is_peak)

# ─── Checkout ────────────────────────────────────────────────
@app.route('/checkout/<booking_id>')
def checkout(booking_id):
    booking_obj = Booking.query.get_or_404(booking_id)
    return render_template('checkout.html',
        booking=booking_obj,
        paypal_client_id=app.config.get('PAYPAL_CLIENT_ID',''),
        razorpay_key_id=app.config.get('RAZORPAY_KEY_ID',''),
        gst_number=GST_NUMBER)

# ─── PayPal Routes ───────────────────────────────────────────
@csrf.exempt
@app.route('/api/create-paypal-order', methods=['POST'])
def api_create_paypal_order():
    try:
        data       = request.get_json()
        booking_id = data.get('booking_id')
        booking_obj = Booking.query.get_or_404(booking_id)
        order      = create_paypal_order(booking_obj.total_amount, booking_obj.booking_reference)
        order_id   = order.get('id')
        if not order_id:
            return jsonify({'success': False, 'error': order.get('message','PayPal order creation failed')}), 400
        payment = Payment(
            booking_id     = booking_obj.id, method = PaymentMethod.PAYPAL,
            status = PaymentStatus.PENDING, amount = booking_obj.total_amount,
            currency = 'INR', paypal_order_id = order_id,
        )
        db.session.add(payment)
        db.session.commit()
        return jsonify({'success': True, 'order_id': order_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@csrf.exempt
@app.route('/api/capture-paypal-order', methods=['POST'])
def api_capture_paypal_order():
    try:
        data     = request.get_json()
        order_id = data.get('order_id')
        booking_id = data.get('booking_id')
        result   = capture_paypal_order(order_id)

        if result.get('status') == 'COMPLETED':
            booking_obj = Booking.query.get(booking_id)
            payment = Payment.query.filter_by(paypal_order_id=order_id).first()
            if payment:
                payment.status         = PaymentStatus.COMPLETED
                payment.paypal_payment_id = result.get('id')
                payment.paypal_payer_id   = result.get('payer', {}).get('payer_id', '')
            booking_obj.status = BookingStatus.CONFIRMED
            db.session.commit()
            send_confirmation_email(booking_obj)
            return jsonify({'success': True, 'reference': booking_obj.booking_reference})
        return jsonify({'success': False, 'error': 'Payment not completed'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ─── Razorpay Routes ─────────────────────────────────────────
@csrf.exempt
@app.route('/api/create-razorpay-order', methods=['POST'])
def api_create_razorpay_order():
    try:
        import razorpay
        data       = request.get_json()
        booking_id = data.get('booking_id')
        booking_obj = Booking.query.get_or_404(booking_id)
        client     = razorpay.Client(
            auth=(app.config['RAZORPAY_KEY_ID'], app.config['RAZORPAY_KEY_SECRET']))
        order = client.order.create({
            'amount':   int(booking_obj.total_amount * 100),
            'currency': 'INR',
            'receipt':  booking_obj.booking_reference,
        })
        payment = Payment(
            booking_id = booking_obj.id, method = PaymentMethod.RAZORPAY,
            status = PaymentStatus.PENDING, amount = booking_obj.total_amount,
            currency = 'INR', razorpay_order_id = order['id'],
        )
        db.session.add(payment)
        db.session.commit()
        return jsonify({'success': True, 'order_id': order['id'], 'amount': int(booking_obj.total_amount * 100)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@csrf.exempt
@app.route('/api/verify-razorpay-payment', methods=['POST'])
def api_verify_razorpay_payment():
    try:
        data    = request.get_json()
        sig_str = f"{data['razorpay_order_id']}|{data['razorpay_payment_id']}"
        expected= hmac.new(
            app.config['RAZORPAY_KEY_SECRET'].encode(),
            sig_str.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, data.get('razorpay_signature','')):
            return jsonify({'success': False, 'error': 'Invalid signature'}), 400
        payment = Payment.query.filter_by(razorpay_order_id=data['razorpay_order_id']).first()
        booking_obj = payment.booking
        payment.status              = PaymentStatus.COMPLETED
        payment.razorpay_payment_id = data['razorpay_payment_id']
        payment.razorpay_signature  = data['razorpay_signature']
        booking_obj.status           = BookingStatus.CONFIRMED
        db.session.commit()
        send_confirmation_email(booking_obj)
        return jsonify({'success': True, 'reference': booking_obj.booking_reference})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ─── Confirmation ────────────────────────────────────────────
@app.route('/confirmation/<ref>')
def confirmation(ref):
    booking_obj = Booking.query.filter_by(booking_reference=ref).first_or_404()
    return render_template('confirmation.html', booking=booking_obj, gst=GST_NUMBER)

# ─── Auth ────────────────────────────────────────────────────
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        if Guest.query.filter_by(email=email).first():
            flash('Email already registered. Please sign in.', 'info')
            return redirect(url_for('login'))
        guest = Guest(
            first_name=request.form.get('first_name',''),
            last_name=request.form.get('last_name',''),
            email=email, phone=request.form.get('phone',''))
        db.session.add(guest)
        db.session.commit()
        session['guest_id'] = guest.id
        flash('Welcome to JHD Hotel!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        guest = Guest.query.filter_by(email=email).first()
        if guest:
            session['guest_id'] = guest.id
            flash(f'Welcome back, {guest.first_name}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Email not found. Please register.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    guest    = Guest.query.get(session['guest_id'])
    bookings = Booking.query.filter_by(guest_id=guest.id).order_by(Booking.created_at.desc()).all()
    return render_template('dashboard.html', guest=guest, bookings=bookings)

# ─── Admin ───────────────────────────────────────────────────
@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        if (request.form.get('username') == os.environ.get('ADMIN_USERNAME','admin') and
            request.form.get('password') == os.environ.get('ADMIN_PASSWORD','jhd@2025')):
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('admin_login.html')

@app.route('/admin')
@admin_required
def admin_dashboard():
    try:
        bookings  = Booking.query.order_by(Booking.created_at.desc()).limit(20).all()
        total_rev = db.session.query(db.func.sum(Booking.total_amount)).filter_by(status=BookingStatus.CONFIRMED).scalar() or 0
        total_rooms  = Room.query.count()
        total_guests = Guest.query.count()
    except Exception:
        bookings = []; total_rev = 0; total_rooms = 0; total_guests = 0
    today_price, today_peak = get_price_for_date(date.today(), 'Normal')
    today_price_sd, _       = get_price_for_date(date.today(), 'Super Deluxe')
    return render_template('admin_dashboard.html',
        bookings=bookings, total_rev=total_rev,
        total_rooms=total_rooms, total_guests=total_guests,
        today_price=today_price, today_price_sd=today_price_sd, today_peak=today_peak)

@app.route('/admin/bookings')
@admin_required
def admin_bookings():
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template('admin_bookings.html', bookings=bookings)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

# ─── API ─────────────────────────────────────────────────────
@csrf.exempt
@app.route('/api/check-email', methods=['POST'])
def api_check_email():
    email = request.get_json().get('email','').strip().lower()
    exists = Guest.query.filter_by(email=email).first() is not None
    return jsonify({'available': not exists})

@app.route('/api/price-for-date')
def api_price_for_date():
    """Used by the frontend to live-update the displayed price as the guest
    picks different check-in dates or room types."""
    date_str  = request.args.get('date', '')
    room_type = request.args.get('room_type', 'Normal')
    try:
        d = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        d = date.today()
    price, peak = get_price_for_date(d, room_type)
    return jsonify({'price': price, 'is_peak': peak})

# ─── Error Handlers ──────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

@app.route('/health')
def health_check():
    """Vercel / uptime monitors can ping this."""
    try:
        db.session.execute(db.text('SELECT 1'))
        db_ok = True
    except Exception as ex:
        db_ok = False
    return {'status': 'ok', 'db': db_ok}, 200

# ─── Context Processor ───────────────────────────────────────
@app.context_processor
def inject_globals():
    return {
        'hotel_phone':     PHONE,
        'hotel_whatsapp':  WHATSAPP_NUM,
        'hotel_gst':       GST_NUMBER,
        'hotel_email':     HOTEL_EMAIL,
        'current_year':    datetime.now().year,
        'today':           date.today(),
    }

try:
    with app.app_context():
        db.create_all()
except Exception:
    pass

if __name__ == '__main__':
    port  = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port)
