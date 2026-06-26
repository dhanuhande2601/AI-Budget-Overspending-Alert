import os
import socket
import smtplib
import ssl
from email.message import EmailMessage

from flask_mail import Message
import requests

from config import Config
from extensions import mail


def _format_money(amount):
    try:
        value = float(amount or 0)
    except (TypeError, ValueError):
        value = 0

    return f"Rs. {value:,.2f}"


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
    response.raise_for_status()
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

    print("Trying direct SMTP fallback")
    _send_with_ipv4_smtp(message)


def send_budget_alert(recipient, percentage, spent, budget):
    remaining = max(float(budget or 0) - float(spent or 0), 0)
    exceeded_by = max(float(spent or 0) - float(budget or 0), 0)

    msg = Message(
        subject=f"Budget Alert - {percentage}% Used",
        recipients=[recipient]
    )

    msg.body = f"""
Budget Warning

You have used {percentage}% of your monthly budget.

Budget: {_format_money(budget)}
Spent: {_format_money(spent)}
Remaining: {_format_money(remaining)}
{f"Exceeded By: {_format_money(exceeded_by)}" if exceeded_by > 0 else ""}

Please control your expenses.
"""

    try:
        print("Sending budget alert email to:", recipient)
        _send_message(msg)
    except Exception as error:
        print("Budget email sending failed:", error)
        raise


def send_test_email(recipient):
    msg = Message(
        subject="AI Budget App - Email Test",
        recipients=[recipient]
    )
    msg.body = (
        "This test email was sent to your registered AI Budget App email "
        "address from the deployed backend."
    )

    try:
        print("Sending test email to:", recipient)
        _send_message(msg)
    except Exception as error:
        print("Test email sending failed:", error)
        raise


def send_overspending_summary(recipient, alerts):
    msg = Message(
        subject="AI Budget App - Overspending Alert",
        recipients=[recipient]
    )

    lines = [
        "Overspending Alert",
        "",
        "Your recent expense has put one or more budgets in warning/exceeded state.",
        "",
    ]

    for alert in alerts:
        category = alert.get("category", "Budget")
        spent = _format_money(alert.get("spent"))
        limit = _format_money(alert.get("limit"))
        percentage = round(float(alert.get("percentage") or 0), 2)
        message = alert.get("message") or "Budget limit reached"
        lines.append(f"- {category}: {percentage}% used ({spent} of {limit})")
        lines.append(f"  {message}")

    lines.extend([
        "",
        "Please review your spending in the AI Budget App."
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

    subject = (

        f"{category} Budget Alert"
        + (f" - {threshold}% Used" if threshold else "")

    )

    body = f"""

Category : {category}

Alert Level : {threshold if threshold else round(percent,2)}%

Budget : {_format_money(budget)}

Spent : {_format_money(spent)}

Remaining : {_format_money(remaining)}

Used : {round(percent,2)}%

Status : {alert_type}

Please review your spending.

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
