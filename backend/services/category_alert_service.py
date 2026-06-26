from datetime import datetime

from database.db import db
from models.budget_notification_model import BudgetNotification
from models.category_budget_model import CategoryBudget
from models.expense_model import Expense
from models.user_model import User
from services.festival_prediction_service import get_upcoming_festival
from services.openai_recommendation_service import get_ai_recommendation


# Ordered low-to-high so every crossed threshold can trigger once.
THRESHOLD_TIERS = [
    (50, "notice", "alert_50_sent"),
    (75, "caution", "alert_75_sent"),
    (90, "critical", "alert_90_sent"),
    (100, "exceeded", "alert_100_sent"),
]

ALERT_FLAGS = {flag for _, _, flag in THRESHOLD_TIERS}
EMAIL_ALERT_FLAGS = {
    flag.replace("_sent", "_email_sent")
    for flag in ALERT_FLAGS
}
SMS_ALERT_FLAGS = {
    flag.replace("_sent", "_sms_sent")
    for flag in ALERT_FLAGS
}
CHANNEL_ALERT_FLAGS = EMAIL_ALERT_FLAGS | SMS_ALERT_FLAGS


def _email_flag(flag_attr):
    return flag_attr.replace("_sent", "_email_sent")


def _sms_flag(flag_attr):
    return flag_attr.replace("_sent", "_sms_sent")


def _email_alerts_enabled(user):
    return getattr(user, "email_alert_enabled", True) is not False


def _sms_alerts_enabled(user):
    return bool(getattr(user, "sms_alert_enabled", False))


def _reset_flags_if_new_month(budget, now):
    """Reset per-threshold alert flags when the calendar month changes."""
    if budget.alert_month == now.month and budget.alert_year == now.year:
        return

    budget.alert_month = now.month
    budget.alert_year = now.year
    for flag in ALERT_FLAGS | CHANNEL_ALERT_FLAGS:
        setattr(budget, flag, False)

    # Kept for older databases that already have this unused 80% column.
    if hasattr(budget, "alert_80_sent"):
        budget.alert_80_sent = False


def _build_alert_message(category, threshold, percent, exceeded_by):
    if threshold >= 100:
        return (
            f"{category} budget crossed 100% "
            f"and is exceeded by Rs. {exceeded_by}"
        )

    return f"{category} budget crossed {threshold}% ({percent}% used)."


def _build_alert_payload(
    budget,
    budget_category,
    spent,
    limit,
    remaining,
    percent,
    exceeded_by,
    threshold,
    alert_type,
    flag_attr,
    message,
    ai_text,
    festival_message,
    should_notify,
    should_email,
    should_sms,
    email_flag_attr,
    sms_flag_attr,
):
    return {
        "category": budget.category,
        "spent": spent,
        "budget": limit,
        "remaining": max(remaining, 0),
        "exceeded_by": exceeded_by,
        "percent": percent,
        "threshold": threshold,
        "type": alert_type,
        "message": message,
        "ai_recommendation": ai_text,
        "festival_prediction": festival_message,
        "should_notify": should_notify,
        "should_email": should_email,
        "should_sms": should_sms,
        "flag_attr": flag_attr,
        "email_flag_attr": email_flag_attr,
        "sms_flag_attr": sms_flag_attr,
        "budget_id": budget.id,
    }


def check_category_alerts(user_id):
    """
    Return category-budget alerts for the current month.

    A category triggers each threshold once per month: 50, 75, 90, and 100.
    If a single expense jumps from below 50 directly to 90 or 100, all newly
    crossed unsent thresholds are returned with should_notify=True.
    """
    now = datetime.now()
    alerts = []
    current_month_start = datetime(now.year, now.month, 1)

    user = User.query.get(user_id)
    budgets = CategoryBudget.query.filter_by(user_id=user_id).all()

    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.created_at >= current_month_start
    ).all()

    for budget in budgets:
        budget_category = (budget.category or "").strip().title()
        limit = float(budget.monthly_limit or 0)

        if limit <= 0:
            continue

        spent = sum(
            float(expense.amount)
            for expense in expenses
            if (expense.category or "").strip().title() == budget_category
        )

        percent = round((spent / limit) * 100, 2)
        remaining = round(limit - spent, 2)

        print(
            "CATEGORY =", budget_category,
            "SPENT =", spent,
            "LIMIT =", limit,
            "PERCENT =", percent
        )

        _reset_flags_if_new_month(budget, now)

        reached_tiers = [
            (threshold, alert_type, flag_attr)
            for threshold, alert_type, flag_attr in THRESHOLD_TIERS
            if percent >= threshold
        ]

        if not reached_tiers:
            continue

        exceeded_by = round(spent - limit, 2) if percent >= 100 else 0

        try:
            ai_text = get_ai_recommendation(budget_category, spent, limit)
        except Exception as error:
            print("AI ERROR =", error)
            ai_text = "Unable to generate AI recommendation."

        festival_message = ""
        festival = get_upcoming_festival()
        if festival:
            festival_message = (
                f"{festival['name']} is coming in "
                f"{festival['days_left']} days. "
                f"You have only Rs. {max(remaining, 0)} left "
                f"in {budget.category} budget."
            )

        added_unsent_alert = False

        for threshold, alert_type, flag_attr in reached_tiers:
            email_flag_attr = _email_flag(flag_attr)
            sms_flag_attr = _sms_flag(flag_attr)

            # Channel-specific flags decide whether email/SMS should be
            # retried. The legacy combined flag only controls in-app alert
            # history and must not permanently suppress email delivery.
            email_already_sent = bool(getattr(budget, email_flag_attr))
            sms_already_sent = bool(getattr(budget, sms_flag_attr))

            should_email = bool(
                user
                and user.email
                and _email_alerts_enabled(user)
                and not email_already_sent
            )
            should_sms = bool(
                user
                and user.phone
                and _sms_alerts_enabled(user)
                and not sms_already_sent
            )
            should_notify = should_email or should_sms

            if not should_notify:
                continue

            added_unsent_alert = True
            message = _build_alert_message(
                budget_category,
                threshold,
                percent,
                exceeded_by
            )

            alerts.append(_build_alert_payload(
                budget,
                budget_category,
                spent,
                limit,
                remaining,
                percent,
                exceeded_by,
                threshold,
                alert_type,
                flag_attr,
                message,
                ai_text,
                festival_message,
                True,
                should_email,
                should_sms,
                email_flag_attr,
                sms_flag_attr,
            ))

            existing = BudgetNotification.query.filter_by(
                user_id=user_id,
                title=f"{budget_category} {threshold}% Alert",
                message=message
            ).first()

            if not existing:
                db.session.add(BudgetNotification(
                    user_id=user_id,
                    title=f"{budget_category} {threshold}% Alert",
                    message=message,
                    notification_type="IN_APP"
                ))

        if not added_unsent_alert:
            threshold, alert_type, flag_attr = reached_tiers[-1]
            email_flag_attr = _email_flag(flag_attr)
            sms_flag_attr = _sms_flag(flag_attr)
            message = _build_alert_message(
                budget_category,
                threshold,
                percent,
                exceeded_by
            )

            alerts.append(_build_alert_payload(
                budget,
                budget_category,
                spent,
                limit,
                remaining,
                percent,
                exceeded_by,
                threshold,
                alert_type,
                flag_attr,
                message,
                ai_text,
                festival_message,
                False,
                False,
                False,
                email_flag_attr,
                sms_flag_attr,
            ))

    db.session.commit()

    print("ALERTS =", alerts)

    return alerts


def mark_category_alert_sent(budget_id, flag_attr):
    if flag_attr not in ALERT_FLAGS | CHANNEL_ALERT_FLAGS:
        return

    budget = CategoryBudget.query.get(budget_id)
    if not budget:
        return

    setattr(budget, flag_attr, True)
    db.session.commit()
