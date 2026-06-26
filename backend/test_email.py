"""
Standalone email diagnostic script.

Run this directly to test your email (Flask-Mail/SMTP) config and see
the EXACT error, without needing to add an expense or trigger the full
app flow and dig through terminal logs.

USAGE:
    python test_email.py your_email@example.com
"""

import sys

from config import Config


print("=" * 50)
print("STEP 1 - Checking .env values loaded into Config")
print("=" * 50)
print("MAIL_SERVER:", Config.MAIL_SERVER)
print("MAIL_PORT:", Config.MAIL_PORT)
print("MAIL_USE_TLS:", Config.MAIL_USE_TLS)
print("MAIL_USERNAME:", Config.MAIL_USERNAME)
print("MAIL_PASSWORD:", "set (hidden)" if Config.MAIL_PASSWORD else None)
print("MAIL_DEFAULT_SENDER:", Config.MAIL_DEFAULT_SENDER)
print()

if not Config.MAIL_USERNAME or not Config.MAIL_PASSWORD:
    print("STOPPED: MAIL_USERNAME or MAIL_PASSWORD is missing/None.")
    print("Check your .env file is in the backend/ folder and has no typos in variable names.")
    sys.exit(1)

if len(sys.argv) < 2:
    print("Usage: python test_email.py your_email@example.com")
    sys.exit(1)

target_email = sys.argv[1].strip()

print("=" * 50)
print(f"STEP 2 - Attempting to send a real email to: {target_email}")
print("=" * 50)

from app import app
from extensions import mail
from flask_mail import Message


with app.app_context():
    try:
        msg = Message(
            subject="AI Budget App - Test Email",
            recipients=[target_email],
        )
        msg.body = "This is a test email to confirm your SMTP/email alerts are working correctly."
        mail.send(msg)
        print("SUCCESS! Email sent without error.")
        print()
        print("If the recipient still doesn't see it, check their SPAM/Promotions folder -")
        print("Gmail sometimes routes automated emails there, especially on first send.")

    except Exception as e:
        print("FAILED WITH ERROR:")
        print(repr(e))
        print()

        error_text = str(e).lower()
        if (
            "username and password not accepted" in error_text
            or "5.7.8" in error_text
            or "5.7.0" in error_text
        ):
            print("*** This is a Gmail AUTHENTICATION error. ***")
            print("If MAIL_USERNAME is a Gmail address, MAIL_PASSWORD must be an")
            print("App Password, NOT your regular Gmail login password. Gmail blocks")
            print("plain-password SMTP login for security. Generate one at:")
            print("  https://myaccount.google.com/apppasswords")
            print("(Requires 2-Step Verification to be enabled on the Google account.)")
        elif (
            "connection refused" in error_text
            or "timed out" in error_text
            or "timeout" in error_text
        ):
            print("*** Could not reach the SMTP server. ***")
            print("Check MAIL_SERVER and MAIL_PORT are correct, and that your hosting")
            print("provider doesn't block outbound SMTP traffic (some free-tier hosts do).")
        else:
            print("Common causes:")
            print("- Wrong MAIL_USERNAME/MAIL_PASSWORD")
            print("- 2-Step Verification not enabled + no App Password generated (Gmail)")
            print("- Hosting provider blocking outbound SMTP port 587")
