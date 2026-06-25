from flask_mail import Message

from extensions import mail


def _format_money(amount):
    try:
        value = float(amount or 0)
    except (TypeError, ValueError):
        value = 0

    return f"Rs. {value:,.2f}"


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
        mail.send(msg)
    except Exception as error:
        print("Budget email sending failed:", error)
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
        mail.send(msg)
    except Exception as error:
        print("Category email sending failed:", error)
        raise
