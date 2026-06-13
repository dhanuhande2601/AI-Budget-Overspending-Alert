from twilio.rest import Client
from config import Config

client = Client(
    Config.TWILIO_ACCOUNT_SID,
    Config.TWILIO_AUTH_TOKEN
)

def send_sms(phone, message):

    try:
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