from flask import Blueprint,jsonify
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)

from models.expense_model import Expense
from models.category_budget_model import CategoryBudget

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

    alerts = []

    for budget in budgets:

        expenses = Expense.query.filter_by(
            user_id=user_id,
            category=budget.category
        ).all()

        total = sum(
            x.amount
            for x in expenses
        )

        percentage = (
            total /
            budget.monthly_limit
        ) * 100

        if percentage >= 100:

            alerts.append({

                "category":
                    budget.category,

                "message":
                    "Budget Exceeded",

                "percentage":
                    round(
                        percentage,
                        2
                    )
            })

        elif percentage >= 80:

            alerts.append({

                "category":
                    budget.category,

                "message":
                    "Budget Warning",

                "percentage":
                    round(
                        percentage,
                        2
                    )
            })

    return jsonify(
        alerts
    )