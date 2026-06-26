import os
import socket
import smtplib
import ssl
from email.message import EmailMessage

from flask_mail import Message
import requests

from config import Config
from extensions import mail


APP_SIGNATURE = "AI BUDGET OVERSPENDING ALERT"


def _format_money(amount):
    try:
        value = float(amount or 0)
    except (TypeError, ValueError):
        value = 0

    return f"Rs. {value:,.2f}"


def _format_percent(value):
    try:
        percent = float(value or 0)
    except (TypeError, ValueError):
        percent = 0

    return f"{percent:.2f}".rstrip("0").rstrip(".")


def _alert_severity(percent):
    try:
        value = float(percent or 0)
    except (TypeError, ValueError):
        value = 0

    if value >= 100:
        return "Budget Exceeded"
    if value >= 90:
        return "Critical"
    if value >= 75:
        return "Warning"
    return "Heads up"


def _message_sender():
    return Config.MAIL_DEFAULT_SENDER or Config.MAIL_USERNAME


def _send_with_ipv4_smtp(message):
    sender = _message_sender()
    if not Config.MAIL_USERNAME or not Config.MAIL_PASSWORD or not sender:
        raise RuntimeError("SMTP credentials are missing.")

    email_message = EmailMessage()
    email_message["Subject"] = message.subject
    email_message["From"] = sender
    email_message["To"] = ", ".join(message.recipients)
    email_message.set_content(message.body or "")

    addresses = socket.getaddrinfo(
        Config.MAIL_SERVER,
        Config.MAIL_PORT,
        socket.AF_INET,
        socket.SOCK_STREAM
    )
    if not addresses:
        raise RuntimeError("No IPv4 SMTP address found.")

    smtp_socket = socket.create_connection(addresses[0][4], timeout=20)
    smtp = smtplib.SMTP(timeout=20)
    smtp.sock = smtp_socket
    smtp.file = smtp_socket.makefile("rb")
    smtp._host = Config.MAIL_SERVER

    try:
        if Config.MAIL_PORT == 465:
            context = ssl.create_default_context()
            smtp.sock = context.wrap_socket(
                smtp.sock,
                server_hostname=Config.MAIL_SERVER
            )
            smtp.file = smtp.sock.makefile("rb")

        smtp.ehlo()
        if Config.MAIL_USE_TLS:
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()
        smtp.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
        smtp.send_message(email_message)
    finally:
        smtp.quit()


def _send_with_resend(message):
    api_key = os.getenv("RESEND_API_KEY")
    sender = os.getenv("RESEND_FROM_EMAIL") or _message_sender()
    if not api_key or not sender:
        return False

    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "from": sender,
            "to": message.recipients,
            "subject": message.subject,
            "text": message.body or "",
        },
        timeout=20,
    )
    if response.status_code >= 400:
        raise RuntimeError(
            f"Resend API error {response.status_code}: {response.text}"
        )
    return True


def _send_with_brevo(message):
    api_key = os.getenv("BREVO_API_KEY")
    sender_email = os.getenv("BREVO_FROM_EMAIL") or _message_sender()
    sender_name = os.getenv("BREVO_FROM_NAME", APP_SIGNATURE)
    if not api_key or not sender_email:
        return False

    response = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={
            "accept": "application/json",
            "api-key": api_key,
            "Content-Type": "application/json",
        },
        json={
            "sender": {
                "name": sender_name,
                "email": sender_email,
            },
            "to": [
                {"email": recipient}
                for recipient in message.recipients
            ],
            "subject": message.subject,
            "textContent": message.body or "",
        },
        timeout=20,
    )
    if response.status_code >= 400:
        raise RuntimeError(
            f"Brevo API error {response.status_code}: {response.text}"
        )
    return True


def _send_message(message):
    try:
        mail.send(message)
        return
    except OSError as error:
        print("Flask-Mail SMTP send failed:", error)
    except Exception as error:
        print("Flask-Mail send failed:", error)
        raise

    try:
        if _send_with_resend(message):
            print("Email sent through Resend HTTPS fallback")
            return
    except Exception as error:
        print("Resend HTTPS fallback failed:", error)

    try:
        if _send_with_brevo(message):
            print("Email sent through Brevo HTTPS fallback")
            return
    except Exception as error:
        print("Brevo HTTPS fallback failed:", error)

    print("Trying direct SMTP fallback")
    _send_with_ipv4_smtp(message)


def send_budget_alert(recipient, percentage, spent, budget):
    remaining = max(float(budget or 0) - float(spent or 0), 0)
    exceeded_by = max(float(spent or 0) - float(budget or 0), 0)
    percent_text = _format_percent(percentage)
    severity = _alert_severity(percentage)

    msg = Message(
        subject=f"AI Budget Alert: {severity} - {percent_text}% Used",
        recipients=[recipient]
    )

    msg.body = f"""
Hi,

Budget Warning

You have used {percent_text}% of your monthly budget.

Summary
- Budget: {_format_money(budget)}
- Spent: {_format_money(spent)}
- Remaining: {_format_money(remaining)}
{f"- Exceeded by: {_format_money(exceeded_by)}" if exceeded_by > 0 else ""}

Please control your expenses and review your latest spending in the app.

{APP_SIGNATURE}
"""

    try:
        print("Sending budget alert email to:", recipient)
        _send_message(msg)
    except Exception as error:
        print("Budget email sending failed:", error)
        raise


def send_test_email(recipient):
    msg = Message(
        subject=f"{APP_SIGNATURE} - Email Test",
        recipients=[recipient]
    )
    msg.body = (
        f"This test email was sent to your registered {APP_SIGNATURE} "
        "email address from the deployed backend."
    )

    try:
        print("Sending test email to:", recipient)
        _send_message(msg)
    except Exception as error:
        print("Test email sending failed:", error)
        raise


def send_overspending_summary(recipient, alerts):
    msg = Message(
        subject="AI Budget Alert: Spending Needs Attention",
        recipients=[recipient]
    )

    lines = [
        "Hi,",
        "",
        "Overspending Alert",
        "",
        "Your recent expense has put one or more budgets in warning/exceeded state.",
        "",
        "Budget snapshot",
    ]

    for alert in alerts:
        category = alert.get("category", "Budget")
        spent = _format_money(alert.get("spent"))
        limit = _format_money(alert.get("limit"))
        percentage = _format_percent(alert.get("percentage"))
        severity = _alert_severity(alert.get("percentage"))
        message = alert.get("message") or "Budget limit reached"
        lines.append(f"- {category}: {percentage}% used ({spent} of {limit})")
        lines.append(f"  Status: {severity}")
        lines.append(f"  Insight: {message}")

    lines.extend([
        "",
        f"Please review your spending in the {APP_SIGNATURE} app.",
        "",
        "Recommended action",
        "Reduce optional spending in the categories listed above until your budget is back on track.",
        "",
        APP_SIGNATURE
    ])

    msg.body = "\n".join(lines)

    try:
        print("Sending overspending summary email to:", recipient)
        _send_message(msg)
    except Exception as error:
        print("Overspending summary email sending failed:", error)
        raise


def send_category_alert(

    email,

    category,

    percent,

    alert_type,

    threshold=None,

    spent=None,

    budget=None,

    remaining=None

):
    percent_text = _format_percent(percent)
    alert_level = threshold if threshold else percent_text
    severity = _alert_severity(percent)

    subject = (

        f"AI Budget Alert: {category} {severity}"
        + (f" - {threshold}% Used" if threshold else f" - {percent_text}% Used")

    )

    body = f"""
Hi,

Category Budget Alert

Summary
- Category: {category}
- Alert level: {alert_level}%
- Budget: {_format_money(budget)}
- Spent: {_format_money(spent)}
- Remaining: {_format_money(remaining)}
- Used: {percent_text}%
- Status: {alert_type}

Please review your spending.

Recommended action
Review recent {category} expenses and avoid non-essential spending in this category for now.

{APP_SIGNATURE}

"""

    msg = Message(

        subject,

        recipients=[email]

    )

    msg.body = body

    try:
        print("Sending category alert email to:", email)
        _send_message(msg)
    except Exception as error:
        print("Category email sending failed:", error)
        raise
