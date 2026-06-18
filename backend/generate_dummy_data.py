"""
Dummy data generator for AI Budget Overspending Alert.

Generates 6 months of realistic expense history for an existing user,
sets category budgets, and backfills BudgetHistory snapshots so the
dashboard, charts, and predictions all have meaningful data to show
right away instead of looking empty.

USAGE:
    python generate_dummy_data.py your_email@example.com

Run this from inside the backend/ folder, with your virtual environment
activated, so it picks up the same database the Flask app uses.
"""

import sys
import random
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from app import app
from database.db import db
from models.user_model import User
from models.expense_model import Expense
from models.category_budget_model import CategoryBudget
from models.budget_history_model import BudgetHistory

import pytz
india_tz = pytz.timezone("Asia/Kolkata")

# =========================================
# CONFIG — tweak these to change the shape of the dummy data
# =========================================

MONTHS_OF_HISTORY = 6

CATEGORY_BUDGETS = {
    "Food": 8000,
    "Travel": 4000,
    "Shopping": 6000,
    "Health": 3000,
    "Adventure": 2500,
    "Loan": 12000,
}

# (title options, typical amount range) per category — used to generate
# realistic-looking expense rows rather than one giant blob per category.
CATEGORY_EXPENSE_TEMPLATES = {
    "Food": [
        ("Swiggy order", (150, 600)),
        ("Zomato order", (150, 700)),
        ("Grocery shopping", (800, 2500)),
        ("Café visit", (100, 400)),
        ("Restaurant dinner", (500, 1500)),
    ],
    "Travel": [
        ("Uber ride", (100, 500)),
        ("Ola ride", (100, 450)),
        ("Petrol", (500, 1500)),
        ("Metro card recharge", (200, 600)),
        ("Bus ticket", (50, 300)),
    ],
    "Shopping": [
        ("Amazon order", (500, 3000)),
        ("Flipkart order", (400, 2500)),
        ("Myntra clothing", (800, 2000)),
        ("Electronics store", (1000, 5000)),
    ],
    "Health": [
        ("Pharmacy", (200, 800)),
        ("Doctor visit", (500, 1500)),
        ("Gym membership", (1000, 2000)),
        ("Health checkup", (800, 2500)),
    ],
    "Adventure": [
        ("Movie tickets", (300, 800)),
        ("Weekend trip", (1500, 4000)),
        ("Trekking gear", (500, 2000)),
        ("Adventure park entry", (800, 1800)),
    ],
    "Loan": [
        ("Home Loan EMI (Auto)", (12000, 12000)),
    ],
}

PAYMENT_METHODS = ["UPI", "Card", "Net Banking", "Cash"]


def random_amount(low, high):
    return round(random.uniform(low, high), 2)


def get_or_create_category_budgets(user_id):
    for category, limit in CATEGORY_BUDGETS.items():
        existing = CategoryBudget.query.filter_by(
            user_id=user_id, category=category.lower()
        ).first()
        if existing:
            existing.monthly_limit = limit
        else:
            db.session.add(CategoryBudget(
                user_id=user_id,
                category=category.lower(),
                monthly_limit=limit,
            ))
    db.session.commit()
    print(f"Category budgets set for user {user_id}: {CATEGORY_BUDGETS}")


def generate_expenses_for_month(user_id, month_start, month_end, is_current_month):
    """
    Generates a randomised but realistic set of expenses for one month,
    spread across categories and days. Returns total spent.
    """
    total_spent = 0
    days_in_range = (month_end - month_start).days

    for category, templates in CATEGORY_EXPENSE_TEMPLATES.items():
        # Loan/EMI is a single fixed monthly charge, not multiple random entries
        if category == "Loan":
            title, (low, high) = templates[0]
            emi_day = min(5, days_in_range)
            emi_date = month_start + timedelta(days=emi_day)
            if is_current_month and emi_date > datetime.now(india_tz).replace(tzinfo=None):
                continue  # don't add future-dated EMI in the current month
            amount = random_amount(low, high)
            db.session.add(Expense(
                user_id=user_id,
                title=title,
                amount=amount,
                category=category,
                payment_method="Auto-Debit",
                created_at=india_tz.localize(emi_date),
            ))
            total_spent += amount
            continue

        # For other categories: 3-7 random expenses spread across the month
        num_expenses = random.randint(3, 7)
        for _ in range(num_expenses):
            title, (low, high) = random.choice(templates)
            day_offset = random.randint(0, max(days_in_range - 1, 0))
            expense_date = month_start + timedelta(days=day_offset)

            # Don't generate future-dated expenses in the current month
            if is_current_month and expense_date > datetime.now(india_tz).replace(tzinfo=None):
                continue

            amount = random_amount(low, high)
            db.session.add(Expense(
                user_id=user_id,
                title=title,
                amount=amount,
                category=category,
                payment_method=random.choice(PAYMENT_METHODS),
                created_at=india_tz.localize(expense_date),
            ))
            total_spent += amount

    db.session.commit()
    return total_spent


def backfill_budget_history(user_id, month, year, monthly_budget, total_spent):
    existing = BudgetHistory.query.filter_by(
        user_id=user_id, month=month, year=year
    ).first()

    total_saved = max(monthly_budget - total_spent, 0)
    overspent = total_spent > monthly_budget

    # Find the top spending category for this month from actual expense rows
    month_start = datetime(year, month, 1)
    month_end = month_start + relativedelta(months=1)
    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.created_at >= month_start,
        Expense.created_at < month_end,
    ).all()

    category_totals = {}
    for e in expenses:
        category_totals[e.category] = category_totals.get(e.category, 0) + float(e.amount)
    top_category = max(category_totals, key=category_totals.get) if category_totals else None

    if existing:
        existing.monthly_budget = monthly_budget
        existing.total_spent = total_spent
        existing.total_saved = total_saved
        existing.overspent = overspent
        existing.top_category = top_category
    else:
        db.session.add(BudgetHistory(
            user_id=user_id,
            month=month,
            year=year,
            monthly_budget=monthly_budget,
            total_spent=total_spent,
            total_saved=total_saved,
            overspent=overspent,
            top_category=top_category,
        ))
    db.session.commit()


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_dummy_data.py your_email@example.com")
        sys.exit(1)

    email = sys.argv[1].strip()

    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"No user found with email: {email}")
            print("Make sure you've registered this account in the app first.")
            sys.exit(1)

        print(f"Generating {MONTHS_OF_HISTORY} months of dummy data for: {user.name} ({user.email})")

        # Make sure income/budget exist so predictions and risk score have something to work with
        if not user.monthly_income:
            user.monthly_income = 60000
        if not user.available_budget:
            user.available_budget = sum(CATEGORY_BUDGETS.values())
        db.session.commit()

        get_or_create_category_budgets(user.id)

        today = datetime.now(india_tz).replace(tzinfo=None)
        monthly_budget_total = sum(CATEGORY_BUDGETS.values())

        # Go from oldest to newest: 5 months ago -> current month
        for offset in range(MONTHS_OF_HISTORY - 1, -1, -1):
            month_date = today - relativedelta(months=offset)
            month_start = datetime(month_date.year, month_date.month, 1)

            is_current_month = (month_date.year == today.year and month_date.month == today.month)
            month_end = today if is_current_month else month_start + relativedelta(months=1)

            total_spent = generate_expenses_for_month(
                user.id, month_start, month_end, is_current_month
            )

            # Don't backfill BudgetHistory for the current month —
            # the scheduler will save that snapshot naturally at month end.
            if not is_current_month:
                backfill_budget_history(
                    user.id, month_start.month, month_start.year,
                    monthly_budget_total, total_spent
                )

            label = month_start.strftime('%b %Y')
            print(f"  {label}: generated expenses totalling Rs.{total_spent:.2f}")

        print("\nDone! 6 months of dummy data created.")
        print("Refresh your dashboard to see Budget History, weekly/monthly trends,")
        print("category predictions, and risk score all populated with real-looking data.")


if __name__ == "__main__":
    main()
    