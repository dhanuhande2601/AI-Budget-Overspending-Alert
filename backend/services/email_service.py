from flask_mail import Message

from extensions import mail


def send_budget_alert(recipient, percentage, spent, budget):
    msg = Message(
        subject=f"Budget Alert - {percentage}% Used",
        recipients=[recipient]
    )

    msg.body = f"""
Budget Warning

You have used {percentage}% of your monthly budget.

Budget: Rs. {budget}
Spent: Rs. {spent}

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

    alert_type

):

    subject = (

        f"{category} Budget Alert"

    )

    body = f"""

Category : {category}

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