from apscheduler.schedulers.background import BackgroundScheduler
from services.backup_service import backup_expenses, backup_users
from services.recurring_expense_service import process_due_recurring_expenses

_scheduler = None


def save_all_users_monthly_snapshot(app):
    """Save budget history snapshot for all users — runs on 1st of every month"""
    from models.user_model import User
    from models.expense_model import Expense
    from models.budget_history_model import BudgetHistory
    from database.db import db
    from datetime import datetime
    from sqlalchemy import func
    import calendar

    now = datetime.utcnow()
    # Save snapshot for PREVIOUS month
    if now.month == 1:
        month = 12
        year = now.year - 1
    else:
        month = now.month - 1
        year = now.year

    with app.app_context():
        users = User.query.all()
        for user in users:
            try:
                expenses = Expense.query.filter(
                    Expense.user_id == user.id,
                    func.extract('month', Expense.created_at) == month,
                    func.extract('year', Expense.created_at) == year
                ).all()

                total_spent = sum(float(e.amount) for e in expenses)
                monthly_budget = float(user.available_budget or 0)
                total_saved = max(monthly_budget - total_spent, 0)
                overspent = total_spent > monthly_budget

                category_totals = {}
                for e in expenses:
                    cat = e.category or 'Other'
                    category_totals[cat] = category_totals.get(cat, 0) + float(e.amount)

                top_category = max(category_totals, key=category_totals.get) if category_totals else None

                existing = BudgetHistory.query.filter_by(
                    user_id=user.id, month=month, year=year
                ).first()

                if existing:
                    existing.monthly_budget = monthly_budget
                    existing.total_spent = total_spent
                    existing.total_saved = total_saved
                    existing.overspent = overspent
                    existing.top_category = top_category
                else:
                    db.session.add(BudgetHistory(
                        user_id=user.id,
                        month=month,
                        year=year,
                        monthly_budget=monthly_budget,
                        total_spent=total_spent,
                        total_saved=total_saved,
                        overspent=overspent,
                        top_category=top_category
                    ))

                # Reset monthly alert flags
                user.budget_alert_50_sent = False
                user.budget_alert_75_sent = False
                user.budget_alert_90_sent = False
                user.budget_alert_100_sent = False
                user.budget_alert_50_email_sent = False
                user.budget_alert_75_email_sent = False
                user.budget_alert_90_email_sent = False
                user.budget_alert_100_email_sent = False
                user.budget_alert_50_sms_sent = False
                user.budget_alert_75_sms_sent = False
                user.budget_alert_90_sms_sent = False
                user.budget_alert_100_sms_sent = False

            except Exception as e:
                print(f"Snapshot error for user {user.id}: {e}")

        db.session.commit()
        print(f"Monthly snapshots saved for {len(users)} users — {month}/{year}")


def start_scheduler(app):
    global _scheduler

    if _scheduler and _scheduler.running:
        return _scheduler

    scheduler = BackgroundScheduler()

    def run_with_app_context(task):
        with app.app_context():
            task()

    # Immediate backup on server startup — so local/dev runs always
    # have a fresh backup instead of waiting for the next scheduled time.
    run_with_app_context(backup_users)
    run_with_app_context(backup_expenses)
    print('Initial backup completed on startup')

    # Immediate recurring-expense check on server startup — so if
    # today is the due date for an EMI/rent/subscription, it gets
    # added right away instead of waiting for the next scheduled run.
    process_due_recurring_expenses(app)
    print('Initial recurring expense check completed on startup')

    # Recurring backups every 6 hours — keeps data fresh even if the
    # server stays running for days without a restart.
    scheduler.add_job(
        func=lambda: run_with_app_context(backup_users),
        trigger='interval', hours=6
    )
    scheduler.add_job(
        func=lambda: run_with_app_context(backup_expenses),
        trigger='interval', hours=6
    )

    # Monthly budget history snapshot — runs on 1st of every month at 00:30
    scheduler.add_job(
        func=lambda: save_all_users_monthly_snapshot(app),
        trigger='cron', day=1, hour=0, minute=30
    )

    # Recurring expenses (EMI, rent, subscriptions) — checked every hour,
    # so a due item gets added within an hour of its due date instead of
    # waiting for a once-daily 1 AM run.
    scheduler.add_job(
        func=lambda: process_due_recurring_expenses(app),
        trigger='interval', hours=1
    )

    scheduler.start()
    _scheduler = scheduler
    print('Scheduler started: backups every 6 hours + recurring expenses checked hourly + monthly budget history enabled')
    return scheduler
