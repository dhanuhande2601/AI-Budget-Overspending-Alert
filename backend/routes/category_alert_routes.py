from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.expense_model import Expense
from models.category_budget_model import CategoryBudget
from datetime import datetime

category_alert = Blueprint(
    "category_alert",
    __name__
)


@category_alert.route(
    "/alerts",
    methods=["GET"]
)
@jwt_required()
def get_alerts():

    user_id = int(
        get_jwt_identity()
    )

    budgets = CategoryBudget.query.filter_by(
        user_id=user_id
    ).all()

    now = datetime.utcnow()

    alerts = []

    for budget in budgets:

        if (
            not budget.monthly_limit
            or budget.monthly_limit <= 0
        ):
            continue

        budget_category = (
            budget.category or ""
        ).strip().title()

        expenses = Expense.query.filter_by(
            user_id=user_id
        ).filter(
            Expense.created_at >= datetime(
                now.year,
                now.month,
                1
            )
        ).all()

        total = 0

        for expense in expenses:

            expense_category = (
                expense.category or ""
            ).strip().title()

            if expense_category == budget_category:
                total += float(expense.amount)

        percentage = (
            total /
            float(budget.monthly_limit)
        ) * 100

        if percentage >= 100:

            alerts.append({
                "category": budget_category,
                "message": "Budget Exceeded",
                "percentage": round(
                    percentage,
                    2
                ),
                "type": "danger"
            })

        elif percentage >= 80:

            alerts.append({
                "category": budget_category,
                "message": "Budget Warning",
                "percentage": round(
                    percentage,
                    2
                ),
                "type": "warning"
            })

    return jsonify({
        "alerts": alerts
    })