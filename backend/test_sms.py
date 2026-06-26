"""
Standalone SMS diagnostic script.

Run this directly to test the configured SMS provider and see the exact
provider response without adding an expense in the app.

USAGE:
    python test_sms.py 9876543210
    python test_sms.py +919876543210
"""

import sys

from config import Config
from services.sms_service import send_sms


def hidden(value):
    if not value:
        return None
    value = str(value)
    return value[:6] + "..." if len(value) > 6 else "set"


print("=" * 50)
print("STEP 1 - Checking SMS config loaded into Config")
print("=" * 50)
print("SMS_PROVIDER:", Config.SMS_PROVIDER)
print("SMS_ALERTS_ENABLED:", Config.SMS_ALERTS_ENABLED)
print("FAST2SMS_API_KEY:", hidden(Config.FAST2SMS_API_KEY))
print("FAST2SMS_ROUTE:", Config.FAST2SMS_ROUTE)
print("TWILIO_ACCOUNT_SID:", hidden(Config.TWILIO_ACCOUNT_SID))
print("TWILIO_AUTH_TOKEN:", hidden(Config.TWILIO_AUTH_TOKEN))
print("TWILIO_PHONE:", repr(Config.TWILIO_PHONE))
print()

if Config.SMS_PROVIDER == "fast2sms":
    if not Config.FAST2SMS_API_KEY:
        print("STOPPED: FAST2SMS_API_KEY is missing/None.")
        sys.exit(1)
    if (Config.FAST2SMS_ROUTE or "").strip().lower() == "dlt":
        print("STOPPED: FAST2SMS_ROUTE=dlt is not supported by this dynamic")
        print("budget alert message. Set FAST2SMS_ROUTE=q for this app.")
        sys.exit(1)
elif Config.SMS_PROVIDER == "twilio":
    if not Config.TWILIO_ACCOUNT_SID or not Config.TWILIO_AUTH_TOKEN or not Config.TWILIO_PHONE:
        print("STOPPED: One or more Twilio env vars are missing/None.")
        sys.exit(1)
else:
    print("STOPPED: SMS_PROVIDER must be fast2sms or twilio.")
    sys.exit(1)

if len(sys.argv) < 2:
    print("Usage: python test_sms.py 9876543210")
    sys.exit(1)

target_number = sys.argv[1].strip()

print("=" * 50)
print(f"STEP 2 - Attempting to send a real SMS to: {target_number}")
print("=" * 50)

sms_id = send_sms(
    target_number,
    "AI Budget Alert test SMS. Your SMS alerts are configured correctly."
)

if sms_id:
    print("SUCCESS! Provider message/request id:", sms_id)
else:
    print("FAILED. Check the FAST2SMS/TWILIO ERROR line printed above.")
