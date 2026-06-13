from email.mime import message
from datetime import date
import calendar
from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from services.openai_recommendation_service import (
    get_ai_recommendation
)
from services.festival_prediction_service import (
    get_upcoming_festival
)
from services.openai_service import (
    generate_ai_recommendation
)
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
    print("OVESPENDING ALERTS =", alerts)
    return jsonify({
        "alerts": alerts
    }), 200

def generate_recommendations(category_summary):

    recommendations = []

    for item in category_summary:

        category = item["category"]
        amount = item["amount"]

        if category == "Food" and amount > 10000:
            recommendations.append(
                "Try reducing food delivery expenses."
            )

        if category == "Shopping" and amount > 5000:
            recommendations.append(
                "Avoid unnecessary shopping this month."
            )

        if category == "Health" and amount > 10000:
            recommendations.append(
                "Review medical expenses and insurance."
            )

    if not recommendations:
        recommendations.append(
            "Your spending pattern looks healthy."
        )

    return recommendations
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
    today = date.today()

    days_in_month = calendar.monthrange(
        today.year,
        today.month
    )[1]

    daily_budget = (
        monthly_budget / days_in_month
        if monthly_budget > 0
        else 0
    )
    expenses = Expense.query.filter_by(
        user_id=current_user_id
    ).all()

    total_spending = 0
    category_summary = {}
    festival = get_upcoming_festival()
    for expense in expenses:

        total_spending += expense.amount

        category = (
            expense.category or ""
        ).strip().title()

        category_summary[category] = (
            category_summary.get(category, 0)
            + expense.amount
        )

    predicted_spending = predict_month_end_spending(expenses)
    expected_spending = (
        daily_budget * today.day
    )

    remaining_budget = (
        monthly_budget - total_spending
    )

    remaining_days = (
        days_in_month - today.day
    )
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
    recommendations = generate_recommendations(
    formatted_categories
    )
    today = date.today()

    days_in_month = 30
    remaining_days = max(
        days_in_month - today.day,
        1
    )

    remaining_budget = (
        monthly_budget - total_spending
    )

    daily_budget = (
        remaining_budget / remaining_days
        if remaining_days > 0
        else 0
    )

    ai_recommendation = (
        generate_ai_recommendation(
            monthly_budget,
            total_spending,
            predicted_spending,
            daily_budget,
            remaining_budget,
            formatted_categories,
            festival
        )     
    )
    overspending_alerts_data = detect_overspending(current_user_id)

    print("OVESPENDING ALERTS =", overspending_alerts_data)
    print("AI Recommendation =", ai_recommendation)
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
        "smart_advice": smart_advice,
        "festival": festival,
        "ai_recommendation":ai_recommendation,
        "recommendations" : recommendations,
        "daily_budget": round(daily_budget, 2),
        "expected_spending": round(
            expected_spending,
            2
        ),
        "remaining_budget": round(
            remaining_budget,
            2
        ),

        "remaining_days": remaining_days,
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
    user = User.query.get(user_id)

    monthly_budget = float(user.available_budget or 0)

    predicted_spending = predict_month_end_spending(expenses)

    remaining_budget = monthly_budget - total_spending

    today = date.today()

    days_in_month = calendar.monthrange(
        today.year,
        today.month
    )[1]

    remaining_days = max(
        days_in_month - today.day,
        1
    )

    daily_budget = (
        remaining_budget / remaining_days
        if remaining_days > 0
        else 0
    )

    festival = get_upcoming_festival()

    formatted_categories = [
        {
            "category": k,
            "amount": float(v)
        }
        for k, v in category_totals.items()
    ]

    ai_recommendation = generate_ai_recommendation(
        monthly_budget,
        total_spending,
        predicted_spending,
        daily_budget,
        remaining_budget,
        formatted_categories,
        festival
    )

    print("MONTHLY AI =", ai_recommendation)

    return jsonify({
        "highest_category": highest_category,
        "highest_amount": category_totals[highest_category],
        "lowest_category": lowest_category,
        "lowest_amount": category_totals[lowest_category],
        "total_transactions": total_transactions,
        "average_expense": average_expense,
        "total_spending": total_spending,

        "ai_recommendation": ai_recommendation
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

    budgets = CategoryBudget.query.filter_by(
        user_id=user_id
    ).all()

    recommendations = []

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

            recommendations.append({

                "category":
                budget.category,

                "message":
                get_ai_recommendation(
                    budget.category,
                    spent,
                    budget.monthly_limit
                )
            })

        elif spent >= budget.monthly_limit * 0.8:

            remaining = round(
                budget.monthly_limit - spent,
                2
            )

            recommendations.append({

                "category":
                budget.category,

                "message":
                get_ai_recommendation(
                    budget.category,
                    spent,
                    budget.monthly_limit
                )
            })

    return jsonify(
        recommendations
    )
