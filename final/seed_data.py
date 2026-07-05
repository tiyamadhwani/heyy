import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from app import app, db
from models import Hotel, Room, Amenity

HOTEL = dict(
    name='JHD Hotel & Bar', city='Udaipur', state='Rajasthan',
    country='India', postal_code='313001',
    address='1, Mahadev Enclave, 100 Main Road, New Bhopalpura, Opp. Nand Bhavan',
    phone='+91 8619882284', email='Hoteljhd@gmail.com',
    gst_number='08AAWFJ9722A1Z2', star_rating=4.5,
    description='Premium rooms in the heart of Udaipur, Rajasthan.',
    banner_url='/static/images/jhd-logo.png',
)

AMENITIES = ['Free WiFi','Air Conditioning','24/7 Electricity',
    'JHD Restaurant (Pure Veg)','JHD Bar & Lounge','Welcome Snacks',
    'Tea & Coffee Maker','Refrigerator','Flat-Screen TV',
    'Premium Washroom Accessories','Room Service','Pets Allowed','Parking']

NORMAL_DESC = (
    'A comfortable Normal Room with everything you need for a great stay — '
    'air conditioning, free WiFi, a flat-screen TV, welcome snacks, and a '
    'fully stocked mini fridge. Extra bed available on request.'
)
SUPER_DELUXE_DESC = (
    'A spacious Super Deluxe Room with upgraded furnishings and extra '
    'comfort — air conditioning, free WiFi, a flat-screen TV, welcome '
    'snacks, a fully stocked mini fridge, and additional living space. '
    'Extra bed available on request.'
)

def seed():
    with app.app_context():
        db.create_all()
        if Hotel.query.first():
            print('✓ Data already exists — skipping')
            return
        h = Hotel(**HOTEL)
        db.session.add(h)
        db.session.flush()

        for name in AMENITIES:
            db.session.add(Amenity(hotel_id=h.id, name=name, icon='fas fa-check'))

        # 22 Normal Rooms, numbered 101–122
        for i in range(22):
            room_no = str(101 + i)
            db.session.add(Room(
                hotel_id=h.id, room_number=room_no,
                room_name='Normal Room', room_type='Normal',
                capacity=2,
                description=NORMAL_DESC,
                has_wifi=True, has_ac=True, has_tv=True, has_fridge=True,
                has_kettle=True, has_snacks=True, has_extra_bed=True,
            ))

        # 11 Super Deluxe Rooms, numbered 201–211
        for i in range(11):
            room_no = str(201 + i)
            db.session.add(Room(
                hotel_id=h.id, room_number=room_no,
                room_name='Super Deluxe Room', room_type='Super Deluxe',
                capacity=3,
                description=SUPER_DELUXE_DESC,
                has_wifi=True, has_ac=True, has_tv=True, has_fridge=True,
                has_kettle=True, has_snacks=True, has_extra_bed=True,
            ))

        db.session.commit()
        print(f'✓ Created JHD Hotel with 22 Normal + 11 Super Deluxe rooms and {len(AMENITIES)} amenities')

if __name__ == '__main__':
    seed()
