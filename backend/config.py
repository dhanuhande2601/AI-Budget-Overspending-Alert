import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Base directory
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # -----------------------
    # ENV VARIABLES (DB)
    # -----------------------
    MYSQL_HOST = os.getenv("DB_HOST")
    MYSQL_USER = os.getenv("DB_USER")
    MYSQL_PASSWORD = os.getenv("DB_PASSWORD")
    MYSQL_DB = os.getenv("DB_NAME")

    DATABASE_URL = os.getenv("DATABASE_URL")
    DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").lower()

    # -----------------------
    # SECURITY
    # -----------------------
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)

    # -----------------------
    # MAIL CONFIG
    # -----------------------
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", MAIL_USERNAME)

    # -----------------------
    # OPENAI
    # -----------------------
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE = os.getenv("TWILIO_PHONE")

    # -----------------------
    # SMS PROVIDER
    # -----------------------
    SMS_PROVIDER = os.getenv("SMS_PROVIDER", "twilio").lower()
    SMS_ALERTS_ENABLED = os.getenv("SMS_ALERTS_ENABLED", "False").lower() == "true"
    FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY")
    FAST2SMS_ROUTE = os.getenv("FAST2SMS_ROUTE", "q")
    # -----------------------
    # DATABASE CONFIG (FIXED LOGIC)
    # -----------------------
    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL

    elif DB_ENGINE == "mysql":
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
            f"@{MYSQL_HOST}/{MYSQL_DB}"
        )

    else:
        # Default fallback (SQLite)
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(
            BASE_DIR,
            "budget_alert.db"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
