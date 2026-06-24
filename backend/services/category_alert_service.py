from datetime import datetime

from services.openai_recommendation_service import (
    get_ai_recommendation
)

from models.category_budget_model import (
    CategoryBudget
)
from services.festival_prediction_service import (
    get_upcoming_festival
)
from models.expense_model import Expense

from models.budget_notification_model import (
    BudgetNotification
)

from database.db import db


# Ordered high-to-low so we always classify into the highest tier reached
THRESHOLD_TIERS = [
    (100, "exceeded", "alert_100_sent"),
    (90, "critical", "alert_90_sent"),
    (80, "warning", "alert_80_sent"),
    (75, "caution", "alert_75_sent"),
    (50, "notice", "alert_50_sent"),
]


def _reset_flags_if_new_month(budget, now):
    """If this CategoryBudget's alert flags belong to a previous month,
    reset them so a new month's spending can trigger alerts again."""
    if budget.alert_month != now.month or budget.alert_year != now.year:
        budget.alert_month = now.month
        budget.alert_year = now.year
        budget.alert_50_sent = False
        budget.alert_75_sent = False
        budget.alert_80_sent = False
        budget.alert_90_sent = False
        budget.alert_100_sent = False


def check_category_alerts(user_id):
    """
    Returns the CURRENT status for every category budget the user has
    (for dashboard display), and ALSO marks which of those should
    trigger a NEW notification (email/SMS) — based on per-threshold,
    per-month flags on CategoryBudget, so the same 50/75/80/90/100+
    tier never sends a duplicate alert mid-month.

    Each returned alert dict includes "should_notify": True/False so
    callers (like the SMS/email sender) can filter on it, while the
    dashboard can still show every category's current status.
    """
    now = datetime.now()
    alerts = []

    budgets = CategoryBudget.query.filter_by(
        user_id=user_id
    ).all()

    print("BUDGETS =", budgets)
    print("TOTAL BUDGETS =", len(budgets))

    current_month_start = datetime(now.year, now.month, 1)

    for budget in budgets:

        budget_category = (budget.category or "").strip().title()

        expenses = Expense.query.filter(
            Expense.user_id == user_id,
            Expense.created_at >= current_month_start
        ).all()

        category_expenses = [
            e for e in expenses
            if (e.category or "").strip().title() == budget_category
        ]

        spent = sum(float(exp.amount) for exp in category_expenses)
        limit = float(budget.monthly_limit or 0)

        if limit <= 0:
            continue

        percent = round((spent / limit) * 100, 2)
        remaining = round(limit - spent, 2)

        print(
            "CATEGORY =", budget_category,
            "SPENT =", spent,
            "LIMIT =", limit,
            "PERCENT =", percent
        )

        # Reset per-month flags if we've rolled into a new month
        _reset_flags_if_new_month(budget, now)

        alert_type = None
        flag_attr = None
        for threshold, tier_name, attr in THRESHOLD_TIERS:
            if percent >= threshold:
                alert_type = tier_name
                flag_attr = attr
                break

        if not alert_type:
            continue

        if alert_type == "exceeded":
            exceeded_by = round(spent - limit, 2)
            message = f"{budget_category} budget exceeded by ₹{exceeded_by}"
        else:
            exceeded_by = 0
            message = f"{budget_category} budget is {percent}% used."

        # Has this exact threshold tier already triggered a notification
        # this month? If not, mark it sent now and flag should_notify.
        already_sent = bool(getattr(budget, flag_attr))
        should_notify = not already_sent
        if should_notify:
            setattr(budget, flag_attr, True)

        try:
            ai_text = get_ai_recommendation(budget_category, spent, limit)
        except Exception as error:
            print("AI ERROR =", error)
            ai_text = "Unable to generate AI recommendation."

        festival_message = ""
        festival = get_upcoming_festival()
        if festival and percent >= 50:
            festival_message = (
                f"{festival['name']} is coming in "
                f"{festival['days_left']} days. "
                f"You have only ₹{max(remaining, 0)} left "
                f"in {budget.category} budget."
            )

        alert_data = {
            "category": budget.category,
            "spent": spent,
            "budget": limit,
            "remaining": max(remaining, 0),
            "exceeded_by": exceeded_by,
            "percent": percent,
            "type": alert_type,
            "message": message,
            "ai_recommendation": ai_text,
            "festival_prediction": festival_message,
            "should_notify": should_notify,
        }

        alerts.append(alert_data)

        if should_notify:
            existing = (
                BudgetNotification.query
                .filter_by(
                    user_id=user_id,
                    title=f"{budget_category} Alert",
                    message=message
                )
                .first()
            )

            if not existing:
                db.session.add(BudgetNotification(
                    user_id=user_id,
                    title=f"{budget_category} Alert",
                    message=message,
                    notification_type="IN_APP"
                ))

    db.session.commit()

    print("ALERTS =", alerts)

    return alerts