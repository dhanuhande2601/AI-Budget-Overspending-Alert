"""
Standalone SMS diagnostic script.

Run this directly to test your Twilio config and see the EXACT error,
without needing to add an expense or trigger the full app flow.

USAGE:
    python test_sms.py +919876543210

(Replace with the real phone number you want to test, in +91 format)
"""

import sys
from config import Config

print("=" * 50)
print("STEP 1 - Checking .env values loaded into Config")
print("=" * 50)
print("TWILIO_ACCOUNT_SID:", Config.TWILIO_ACCOUNT_SID)
print("TWILIO_AUTH_TOKEN:", Config.TWILIO_AUTH_TOKEN[:6] + "..." if Config.TWILIO_AUTH_TOKEN else None)
print("TWILIO_PHONE:", repr(Config.TWILIO_PHONE))
print()

if not Config.TWILIO_ACCOUNT_SID or not Config.TWILIO_AUTH_TOKEN or not Config.TWILIO_PHONE:
    print("STOPPED: One or more Twilio env vars are missing/None.")
    print("Check your .env file is in the backend/ folder and has no typos in variable names.")
    sys.exit(1)

if " " in Config.TWILIO_PHONE:
    print("WARNING: TWILIO_PHONE contains a space character — this will likely fail.")
    print("It should look like +15706XXXXXX with NO spaces.")
    print()

if len(sys.argv) < 2:
    print("Usage: python test_sms.py +919876543210")
    sys.exit(1)

target_number = sys.argv[1].strip()

print("=" * 50)
print(f"STEP 2 - Attempting to send a real SMS to: {target_number}")
print("=" * 50)

from twilio.rest import Client

try:
    client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
    sms = client.messages.create(
        body="Test SMS from AI Budget app diagnostic script",
        from_=Config.TWILIO_PHONE,
        to=target_number
    )
    print("SUCCESS! Message SID:", sms.sid)
    print("Status:", sms.status)
    print()
    print("If you still don't receive it, check the message status on your")
    print("Twilio Console -> Monitor -> Logs -> Messaging. It will show")
    print("'delivered', 'undelivered', or 'failed' with the real reason.")

except Exception as e:
    print("FAILED WITH ERROR:")
    print(repr(e))
    print()
    print("Common causes based on the error above:")
    print("- 'unverified' -> your number isn't verified in Twilio (trial accounts)")
    print("- 'not a valid phone number' -> check +91 format, no spaces/dashes")
    print("- 'authenticate' -> ACCOUNT_SID or AUTH_TOKEN is wrong")
    print("- 'not a Twilio phone number' -> TWILIO_PHONE value itself is wrong")