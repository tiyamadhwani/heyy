from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid, enum

db = SQLAlchemy()

def gen_id():
    return str(uuid.uuid4())

class BookingStatus(enum.Enum):
    PENDING   = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class PaymentStatus(enum.Enum):
    PENDING   = "pending"
    COMPLETED = "completed"
    FAILED    = "failed"
    REFUNDED  = "refunded"

class PaymentMethod(enum.Enum):
    PAYPAL    = "paypal"
    RAZORPAY  = "razorpay"
    CASH      = "cash"

class Hotel(db.Model):
    __tablename__ = 'hotels'
    id           = db.Column(db.String(36), primary_key=True, default=gen_id)
    name         = db.Column(db.String(200), nullable=False)
    address      = db.Column(db.Text)
    city         = db.Column(db.String(100))
    state        = db.Column(db.String(100))
    country      = db.Column(db.String(100), default='India')
    postal_code  = db.Column(db.String(20))
    phone        = db.Column(db.String(20))
    email        = db.Column(db.String(120))
    gst_number   = db.Column(db.String(20))
    star_rating  = db.Column(db.Float, default=4.5)
    description  = db.Column(db.Text)
    banner_url   = db.Column(db.String(300))
    rooms        = db.relationship('Room', backref='hotel', lazy=True)
    amenities    = db.relationship('Amenity', backref='hotel', lazy=True)

class Room(db.Model):
    """33 rooms total: 22 Normal + 11 Super Deluxe."""
    __tablename__ = 'rooms'
    id              = db.Column(db.String(36), primary_key=True, default=gen_id)
    hotel_id        = db.Column(db.String(36), db.ForeignKey('hotels.id'), nullable=False)
    room_number     = db.Column(db.String(10))
    room_name       = db.Column(db.String(100), default='Premium Room')
    room_type       = db.Column(db.String(30), default='Normal')   # 'Normal' or 'Super Deluxe'
    capacity        = db.Column(db.Integer, default=2)
    description     = db.Column(db.Text)
    image_url       = db.Column(db.String(300), default='/static/images/default-room.jpg')
    has_wifi        = db.Column(db.Boolean, default=True)
    has_ac          = db.Column(db.Boolean, default=True)
    has_tv          = db.Column(db.Boolean, default=True)
    has_fridge      = db.Column(db.Boolean, default=True)
    has_kettle      = db.Column(db.Boolean, default=True)
    has_snacks      = db.Column(db.Boolean, default=True)
    has_extra_bed   = db.Column(db.Boolean, default=True)
    is_available    = db.Column(db.Boolean, default=True)
    bookings        = db.relationship('Booking', backref='room', lazy=True)

class Guest(db.Model):
    __tablename__ = 'guests'
    id              = db.Column(db.String(36), primary_key=True, default=gen_id)
    first_name      = db.Column(db.String(100), nullable=False)
    last_name       = db.Column(db.String(100), nullable=False)
    email           = db.Column(db.String(120), nullable=False, unique=True)
    phone           = db.Column(db.String(20))
    nationality     = db.Column(db.String(100))
    id_type         = db.Column(db.String(50))
    id_number       = db.Column(db.String(100))
    street_address  = db.Column(db.String(200))
    city            = db.Column(db.String(100))
    state           = db.Column(db.String(100))
    postal_code     = db.Column(db.String(20))
    country         = db.Column(db.String(100))
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    bookings        = db.relationship('Booking', backref='guest', lazy=True)

class Booking(db.Model):
    __tablename__ = 'bookings'
    id                  = db.Column(db.String(36), primary_key=True, default=gen_id)
    booking_reference   = db.Column(db.String(20), unique=True)
    room_id             = db.Column(db.String(36), db.ForeignKey('rooms.id'), nullable=False)
    guest_id            = db.Column(db.String(36), db.ForeignKey('guests.id'), nullable=False)
    check_in_date       = db.Column(db.Date, nullable=False)
    check_out_date      = db.Column(db.Date, nullable=False)
    num_adults          = db.Column(db.Integer, default=2)
    num_children        = db.Column(db.Integer, default=0)
    extra_bed           = db.Column(db.Boolean, default=False)
    special_requests    = db.Column(db.Text)
    num_nights          = db.Column(db.Integer)
    price_per_night     = db.Column(db.Float)   # the ACTUAL price charged (auto seasonal + room type)
    room_type           = db.Column(db.String(30), default='Normal')
    is_peak_season      = db.Column(db.Boolean, default=False)
    subtotal            = db.Column(db.Float)
    gst_amount           = db.Column(db.Float)
    total_amount        = db.Column(db.Float)
    status              = db.Column(db.Enum(BookingStatus), default=BookingStatus.PENDING)
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)
    payment             = db.relationship('Payment', backref='booking', uselist=False, lazy=True)

    @staticmethod
    def generate_reference():
        import random
        return f"JHD-{datetime.now().year}-{random.randint(100000,999999)}"

    def calculate_total(self):
        nights = (self.check_out_date - self.check_in_date).days
        self.num_nights = nights
        self.subtotal = self.price_per_night * nights
        self.gst_amount = round(self.subtotal * 0.12, 2)
        self.total_amount = round(self.subtotal + self.gst_amount, 2)
        return self.total_amount

class Payment(db.Model):
    __tablename__ = 'payments'
    id              = db.Column(db.String(36), primary_key=True, default=gen_id)
    booking_id      = db.Column(db.String(36), db.ForeignKey('bookings.id'), nullable=False)
    method          = db.Column(db.Enum(PaymentMethod))
    status          = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING)
    amount          = db.Column(db.Float)
    currency        = db.Column(db.String(5), default='INR')
    paypal_order_id     = db.Column(db.String(200))
    paypal_payment_id   = db.Column(db.String(200))
    paypal_payer_id     = db.Column(db.String(200))
    razorpay_order_id   = db.Column(db.String(200))
    razorpay_payment_id = db.Column(db.String(200))
    razorpay_signature  = db.Column(db.String(300))
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)

class Amenity(db.Model):
    __tablename__ = 'amenities'
    id       = db.Column(db.String(36), primary_key=True, default=gen_id)
    hotel_id = db.Column(db.String(36), db.ForeignKey('hotels.id'), nullable=False)
    name     = db.Column(db.String(100))
    icon     = db.Column(db.String(50))

class Review(db.Model):
    __tablename__ = 'reviews'
    id         = db.Column(db.String(36), primary_key=True, default=gen_id)
    guest_id   = db.Column(db.String(36), db.ForeignKey('guests.id'))
    room_id    = db.Column(db.String(36), db.ForeignKey('rooms.id'))
    rating     = db.Column(db.Integer)
    title      = db.Column(db.String(200))
    comment    = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    guest      = db.relationship('Guest', backref='reviews')
    room       = db.relationship('Room', backref='reviews')
