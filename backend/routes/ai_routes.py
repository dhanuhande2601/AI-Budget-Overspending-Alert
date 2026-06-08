from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from models.expense_model import Expense
from models.user_model import User
from services.ai_budget_engine import (
    budget_usage_alerts,
    calculate_risk_score,
    detect_overspending,
    generate_smart_advice,
    predict_month_end_spending,
)

ai = Blueprint('ai', __name__)


# =========================================
# OVERSPENDING ALERTS
# =========================================
@ai.route('/overspending-alerts', methods=['GET'])
@jwt_required()
def overspending_alerts():
    current_user_id = int(get_jwt_identity())
    alerts = detect_overspending(current_user_id)

    return jsonify({
        "alerts": alerts
    }), 200


# =========================================
# DASHBOARD ANALYTICS
# =========================================
@ai.route('/dashboard-analytics', methods=['GET'])
@jwt_required()
def dashboard_analytics():
    current_user_id = int(get_jwt_identity())

    user = User.query.get(current_user_id)
    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    monthly_budget = float(user.available_budget or 0)

    expenses = Expense.query.filter_by(
        user_id=current_user_id
    ).all()

    total_spending = 0
    category_summary = {}

    for expense in expenses:
        total_spending += expense.amount
        category_summary[expense.category] = (
            category_summary.get(expense.category, 0) + expense.amount
        )

    predicted_spending = predict_month_end_spending(expenses)
    risk_data = calculate_risk_score(
        total_spending,
        monthly_budget,
        predicted_spending
    )

    formatted_categories = [
        {
            "category": category,
            "amount": float(amount)
        }
        for category, amount in category_summary.items()
    ]

    alerts = []
    for item in formatted_categories:
        if item["amount"] >= 5000:
            alerts.append({
                "category": item["category"],
                "alert": f"High spending detected in {item['category']}"
            })

    budget_percentage = 0
    if monthly_budget > 0:
        budget_percentage = (total_spending / monthly_budget) * 100

    if budget_percentage >= 100:
        alerts.append({
            "category": "budget",
            "alert": "Budget limit exceeded"
        })
    elif budget_percentage >= 90:
        alerts.append({
            "category": "budget",
            "alert": "90% of monthly budget used"
        })
    elif budget_percentage >= 75:
        alerts.append({
            "category": "budget",
            "alert": "75% of monthly budget used"
        })
    elif budget_percentage >= 50:
        alerts.append({
            "category": "budget",
            "alert": "50% of monthly budget used"
        })

    smart_advice = generate_smart_advice(formatted_categories)

    return jsonify({
        "total_spending": float(total_spending),
        "monthly_budget": monthly_budget,
        "budget_percentage": round(budget_percentage, 2),
        "predicted_spending": float(predicted_spending),
        "category_summary": formatted_categories,
        "alerts": alerts,
        "budget_alerts": budget_usage_alerts(current_user_id),
        "risk_score": risk_data["score"],
        "risk_level": risk_data["level"],
        "smart_advice": smart_advice
    }), 200

@ai.route(
    '/monthly-insights',
    methods=['GET']
)
@jwt_required()
def monthly_insights():

    user_id = int(
        get_jwt_identity()
    )

    expenses = Expense.query.filter_by(
        user_id=user_id
    ).all()

    if not expenses:

        return jsonify({
            "message":
                "No expenses found"
        })

    total_spending = sum(
        item.amount
        for item in expenses
    )

    total_transactions = len(
        expenses
    )

    average_expense = round(
        total_spending /
        total_transactions,
        2
    )

    category_totals = {}

    for item in expenses:

        category_totals[
            item.category
        ] = (
            category_totals.get(
                item.category,
                0
            )
            +
            item.amount
        )

    highest_category = max(
        category_totals,
        key=category_totals.get
    )

    lowest_category = min(
        category_totals,
        key=category_totals.get
    )

    return jsonify({

        "highest_category":
            highest_category,

        "highest_amount":
            category_totals[
                highest_category
            ],

        "lowest_category":
            lowest_category,

        "lowest_amount":
            category_totals[
                lowest_category
            ],

        "total_transactions":
            total_transactions,

        "average_expense":
            average_expense,

        "total_spending":
            total_spending
    })


@ai.route(
    "/category-predictions",
    methods=["GET"]
)
@jwt_required()
def category_predictions():

    user_id = int(
        get_jwt_identity()
    )

    expenses = Expense.query.filter_by(
        user_id=user_id
    ).all()

    categories = {}

    for expense in expenses:

        category = expense.category

        if category not in categories:

            categories[category] = 0

        categories[category] += float(
            expense.amount
        )

    result = []

    for category, spent in categories.items():

        predicted = spent * 1.5

        result.append({

            "category":
            category,

            "current":
            spent,

            "predicted":
            round(predicted,2)

        })

    return jsonify(result)

@ai.route(
    "/recommendations",
    methods=["GET"]
)
@jwt_required()
def ai_recommendations():

    user_id = int(
        get_jwt_identity()
    )

    from models.category_budget_model import (
        CategoryBudget
    )

    from models.expense_model import (
        Expense
    )

    recommendations = []

    budgets = CategoryBudget.query.filter_by(
        user_id=user_id
    ).all()

    for budget in budgets:

        expenses = Expense.query.filter_by(

            user_id=user_id,

            category=budget.category

        ).all()

        spent = sum(
            e.amount
            for e in expenses
        )

        if spent >= budget.monthly_limit:

            extra = round(
                spent - budget.monthly_limit,
                2
            )

            recommendations.append({

                "category":
                budget.category,

                "message":
                f"You exceeded your {budget.category} budget by ₹{extra}. Try reducing spending next month."

            })

        elif spent >= budget.monthly_limit * 0.8:

            remaining = round(

                budget.monthly_limit
                - spent,

                2

            )

            recommendations.append({

                "category":
                budget.category,

                "message":
                f"Only ₹{remaining} left in {budget.category} budget. Spend carefully."

            })

    return jsonify(
        recommendations
    )