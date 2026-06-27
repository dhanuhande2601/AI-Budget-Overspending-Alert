import requests
from twilio.rest import Client
from config import Config


def _indian_mobile_number(phone):
    if not phone:
        return None

    digits = "".join(ch for ch in str(phone) if ch.isdigit())
    if len(digits) == 10:
        return digits
    if len(digits) == 12 and digits.startswith("91"):
        return digits[-10:]
    if len(digits) > 10:
        return digits[-10:]

    return None


def _twilio_phone_number(phone):
    mobile = _indian_mobile_number(phone)
    if mobile:
        return "+91" + mobile

    phone = (phone or "").strip()
    return phone if phone.startswith("+") else "+" + phone


def _send_fast2sms(phone, message):
    raw_api_key = Config.FAST2SMS_API_KEY or ""
    api_key = raw_api_key.strip().splitlines()[0].strip()

    if not api_key:
        print("FAST2SMS ERROR = FAST2SMS_API_KEY is not configured.")
        return None

    route = (Config.FAST2SMS_ROUTE or "q").strip().lower()
    if route == "dlt":
        print(
            "FAST2SMS ERROR = DLT route needs sender_id and approved "
            "template variables. For dynamic budget alerts set "
            "FAST2SMS_ROUTE=q."
        )
        return None

    mobile = _indian_mobile_number(phone)
    if not mobile:
        print("FAST2SMS ERROR = Invalid Indian mobile number:", phone)
        return None

    try:
        print("FAST2SMS SENDING =", {"route": route, "numbers": mobile})
        response = requests.post(
            "https://www.fast2sms.com/dev/bulkV2",
            headers={
                "authorization": api_key,
            },
            data={
                "route": route,
                "message": message,
                "language": "english",
                "flash": 0,
                "numbers": mobile,
            },
            timeout=20,
        )
        data = response.json()
        if response.status_code >= 400 or not data.get("return"):
            print("FAST2SMS ERROR =", data)
            return None

        request_id = data.get("request_id") or data.get("message")
        print("FAST2SMS REQUEST ID =", request_id)
        return request_id

    except Exception as error:
        print("FAST2SMS ERROR =", error)
        return None


def _send_twilio(phone, message):
    if not Config.TWILIO_ACCOUNT_SID or not Config.TWILIO_AUTH_TOKEN or not Config.TWILIO_PHONE:
        print("TWILIO ERROR = Twilio credentials or phone number not configured.")
        return None

    if not phone:
        print("TWILIO ERROR = No recipient phone number provided.")
        return None

    phone = _twilio_phone_number(phone)

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


def send_sms(phone, message):
    if Config.SMS_PROVIDER == "fast2sms":
        return _send_fast2sms(phone, message)

    return _send_twilio(phone, message)
