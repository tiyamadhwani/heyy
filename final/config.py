import os
from dotenv import load_dotenv
load_dotenv()

def _fix_db_url(url):
    """
    Fix the DB URL for the driver we are using:
    - Heroku/Neon/Render give  postgres://   → change to postgresql+pg8000://
    - Standard                 postgresql://  → change to postgresql+pg8000://
    - SQLite stays as-is (local dev only)
    pg8000 is a pure-Python driver — no C compilation, always works on Vercel.
    """
    if not url:
        return 'sqlite:///jhd_hotel.db'
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    if url.startswith('postgresql://') and '+pg8000' not in url:
        url = url.replace('postgresql://', 'postgresql+pg8000://', 1)
    return url


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'jhd-hotel-fallback-key-2025')

    _raw_db_url = os.environ.get('DATABASE_URL', 'sqlite:///jhd_hotel.db')
    SQLALCHEMY_DATABASE_URI    = _fix_db_url(_raw_db_url)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS  = {'pool_pre_ping': True}

    WTF_CSRF_ENABLED     = True
    WTF_CSRF_SSL_STRICT  = False       # Safe default for all proxied environments
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PREFERRED_URL_SCHEME = 'https'

    MAIL_SERVER        = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT          = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS       = True
    MAIL_USERNAME      = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD      = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME', '')

    RAZORPAY_KEY_ID     = os.environ.get('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')

    PAYPAL_CLIENT_ID     = os.environ.get('PAYPAL_CLIENT_ID', '')
    PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET', '')
    PAYPAL_MODE          = os.environ.get('PAYPAL_MODE', 'sandbox')

    HOTEL_PHONE    = '+91 8619882284'
    HOTEL_WHATSAPP = '918619882284'
    HOTEL_GST      = '08AAWFJ9722A1Z2'
    HOTEL_EMAIL    = 'Hoteljhd@gmail.com'
    HOTEL_NAME     = 'JHD Hotel & Bar'

    NORMAL_PRICE       = float(os.environ.get('NORMAL_PRICE', 4000))
    PEAK_PRICE         = float(os.environ.get('PEAK_PRICE', 7000))
    PEAK_SEASON_RANGES = os.environ.get('PEAK_SEASON_RANGES', '10-01:12-31,01-01:03-31')
    SUPER_DELUXE_EXTRA = float(os.environ.get('SUPER_DELUXE_EXTRA', 1500))


class DevelopmentConfig(Config):
    DEBUG = True
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_TIME_LIMIT   = 3600
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle':  300,
    }


config = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'default':     ProductionConfig,
}
