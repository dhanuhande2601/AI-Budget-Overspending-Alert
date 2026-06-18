from datetime import date, timedelta
from database.db import db
from models.recurring_expense_model import RecurringExpense
from models.expense_model import Expense


def process_due_recurring_expenses(app):
    """
    Checks all active recurring expenses and auto-creates a real
    Expense entry for any that are due today and haven't already
    been added for this cycle. Also auto-deactivates any recurring
    expense whose end_date (e.g. EMI tenure) has passed.
    Runs once a day via the scheduler.
    """
    with app.app_context():
        today = date.today()
        recurring_items = RecurringExpense.query.filter_by(is_active=True).all()
        created_count = 0
        expired_count = 0

        for item in recurring_items:
            # If this recurring expense has an end date and it's passed,
            # stop it permanently - no more auto-adds after this point.
            if item.end_date and item.end_date < today:
                item.is_active = False
                expired_count += 1
                continue

            if _is_due_today(item, today):
                new_expense = Expense(
                    user_id=item.user_id,
                    title=f"{item.title} (Auto)",
                    amount=item.amount,
                    category=item.category,
                    payment_method=item.payment_method or "Auto-Debit",
                )
                db.session.add(new_expense)
                item.last_added_on = today
                created_count += 1

        if created_count or expired_count:
            db.session.commit()

        print(
            f"Recurring expenses processed: {created_count} added, "
            f"{expired_count} expired on {today}"
        )


def _is_due_today(item, today):
    # Already added today or this cycle - skip
    if item.last_added_on == today:
        return False

    if item.frequency == 'monthly':
        if today.day != item.day_of_month:
            return False
        # Avoid double-adding same month if job runs twice
        if item.last_added_on and item.last_added_on.month == today.month and item.last_added_on.year == today.year:
            return False
        return True

    if item.frequency == 'weekly':
        if not item.last_added_on:
            return True
        return (today - item.last_added_on) >= timedelta(days=7)

    if item.frequency == 'yearly':
        if today.day != item.day_of_month:
            return False
        if item.last_added_on and item.last_added_on.year == today.year:
            return False
        return True

    return False