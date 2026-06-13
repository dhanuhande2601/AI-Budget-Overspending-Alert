from app import app
from database.db import db
from models.expense_model import Expense

with app.app_context():

    expenses = Expense.query.all()

    for expense in expenses:

        # Category Fix
        expense.category = (
            expense.category.strip().title()
        )

        # Payment Fix
        payment = (
            expense.payment_method or ""
        ).strip().lower()

        if payment in [
            "upi",
            "gpay",
            "google pay",
            "phonepe",
            "paytm"
        ]:
            expense.payment_method = "UPI"

        elif payment in [
            "credit card",
            "debit card",
            "card"
        ]:
            expense.payment_method = "Card"

        elif payment in [
            "net banking",
            "netbanking",
            "neft",
            "imps"
        ]:
            expense.payment_method = "Net Banking"

        elif payment == "cash":
            expense.payment_method = "Cash"

    db.session.commit()

    print("All expense data fixed successfully.")