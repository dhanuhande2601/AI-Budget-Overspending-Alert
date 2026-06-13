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


def check_category_alerts(user_id):

    alerts = []

    budgets = CategoryBudget.query.filter_by(
        user_id=user_id
    ).all()

    print("BUDGETS =", budgets)
    print("TOTAL BUDGETS =", len(budgets))

    current_month_start = datetime(
        datetime.now().year,
        datetime.now().month,
        1
    )

    for budget in budgets:

        budget_category = (
            budget.category or ""
        ).strip().title()

        expenses = Expense.query.filter(
            Expense.user_id == user_id,
            Expense.created_at >= current_month_start
        ).all()

        category_expenses = []

        for expense in expenses:

            expense_category = (
                expense.category or ""
            ).strip().title()

            if expense_category == budget_category:
                category_expenses.append(expense)

        spent = sum(
            float(exp.amount)
            for exp in category_expenses
        )

        limit = float(
            budget.monthly_limit or 0
        )

        if limit <= 0:
            continue

        percent = round(
            (spent / limit) * 100,
            2
        )

        print(
            "CATEGORY =", budget_category,
            "SPENT =", spent,
            "LIMIT =", limit,
            "PERCENT =", percent
        )

        remaining = round(
            limit - spent,
            2
        )

        alert_type = None
        message = None

        if percent >= 100:

            exceeded_by = round(
                spent - limit,
                2
            )

            alert_type = "exceeded"

            message = (
                f"{budget_category} budget exceeded "
                f"by ₹{exceeded_by}"
            )

        elif percent >= 90:

            alert_type = "critical"

            message = (
                f"{budget_category} budget is "
                f"{percent}% used."
            )

        elif percent >= 80:

            alert_type = "warning"

            message = (
                f"{budget_category} budget is "
                f"{percent}% used."
            )

        if alert_type:

            try:

                ai_text = get_ai_recommendation(
                    budget_category,
                    spent,
                    limit
                )

            except Exception as error:

                print(
                    "AI ERROR =",
                    error
                )

                ai_text = (
                    "Unable to generate AI recommendation."
                )
                festival_message = get_upcoming_festival(
                    spent,
                    limit
                )
                festival = get_upcoming_festival()

                festival_message = None

                if festival and percent >= 80:

                    festival_message = (
                        f"{festival['name']} is coming in "
                        f"{festival['days_left']} days. "
                        f"You have only ₹{max(remaining,0)} left "
                        f"in {budget.category} budget."
                    )

            alert_data = {
                "category": budget.category,
                "spent": spent,
                "budget": limit,
                "remaining": max(remaining, 0),
                "percent": percent,
                "type": alert_type,
                "message": message,
                "ai_recommendation": get_ai_recommendation(
                    budget.category,
                    spent,
                    limit
                ),
                "festival_prediction": festival_message
            }

            alerts.append(
                alert_data
            )

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

                notification = (
                    BudgetNotification(
                        user_id=user_id,
                        title=f"{budget_category} Alert",
                        message=message,
                        notification_type="IN_APP"
                    )
                )

                db.session.add(
                    notification
                )

    db.session.commit()

    print("ALERTS =", alerts)

    return alerts