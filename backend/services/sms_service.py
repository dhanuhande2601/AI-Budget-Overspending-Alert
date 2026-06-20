from twilio.rest import Client
from config import Config

def send_sms(phone, message):
    if not Config.TWILIO_ACCOUNT_SID or not Config.TWILIO_AUTH_TOKEN or not Config.TWILIO_PHONE:
        print("TWILIO ERROR = Twilio credentials or phone number not configured.")
        return None

    if not phone:
        print("TWILIO ERROR = No recipient phone number provided.")
        return None

    # Auto-format phone number
    phone = phone.strip()
    if not phone.startswith('+'):
        if len(phone) == 10 and phone.isdigit():
            phone = '+91' + phone
        elif len(phone) == 12 and phone.startswith('91') and phone.isdigit():
            phone = '+' + phone
        else:
            phone = '+' + phone

    try:
        client = Client(
            Config.TWILIO_ACCOUNT_SID,
            Config.TWILIO_AUTH_TOKEN
        )
        sms = client.messages.create(
            body=message,
            from_=Config.TWILIO_PHONE,
            to=phone
        )

        print("SMS SID =", sms.sid)
        return sms.sid

    except Exception as e:
        print("TWILIO ERROR =", e)
        return None