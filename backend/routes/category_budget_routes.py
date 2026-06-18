from flask import Blueprint
from flask import request
from flask import jsonify

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)

from database.db import db

from models.category_budget_model import (
    CategoryBudget
)

from models.budget_model import Budget
from models.user_model import User

category_budget = Blueprint(
    "category_budget",
    __name__
)

@category_budget.route(
    "/set",
    methods=["POST"]
)
@jwt_required()
def set_budget():

    user_id = int(
        get_jwt_identity()
    )

    data = request.get_json()

    categories = [

        "food",
        "travel",
        "shopping",
        "health",
        "adventure",
        "loan"

    ]

    for category in categories:

        amount = float(
            data.get(category,0)
        )

        existing = CategoryBudget.query.filter_by(

            user_id=user_id,

            category=category.lower()

        ).first()

        if existing:

            existing.monthly_limit = amount

        else:

            db.session.add(

                CategoryBudget(

                    user_id=user_id,

                    category=category,

                    monthly_limit=amount

                )

            )

    db.session.commit()

    return jsonify({

        "message":
        "Category budgets saved"

    })
@category_budget.route(
    "/all",
    methods=["GET"]
)
@jwt_required()
def get_category_budgets():

    user_id = int(
        get_jwt_identity()
    )

    budgets = CategoryBudget.query.filter_by(
        user_id=user_id
    ).all()

    result = []

    for budget in budgets:

        result.append({

            "category":
            budget.category,

            "monthly_limit":
            budget.monthly_limit

        })

    return jsonify(result)

@category_budget.route(
    "/summary",
    methods=["GET"]
)
@jwt_required()
def category_summary():

    user_id = int(
        get_jwt_identity()
    )

    from models.expense_model import Expense

    budgets = CategoryBudget.query.filter_by(
        user_id=user_id
    ).all()

    result = []

    for budget in budgets:

        expenses = Expense.query.filter(
            Expense.user_id == user_id,
            db.func.lower(
                Expense.category
            ) == budget.category.lower()
        ).all()

        spent = sum(

            e.amount
            for e in expenses

        )

        remaining = (

            budget.monthly_limit
            - spent

        )

        status = "Safe"

        if spent >= budget.monthly_limit:

            status = "Exceeded"

        elif spent >= budget.monthly_limit * 0.8:

            status = "Warning"

        result.append({

            "category":
            budget.category,

            "budget":
            budget.monthly_limit,

            "spent":
            spent,

            "remaining":
            remaining,

            "status":
            status

        })

    return jsonify(result)
@category_budget.route(
    "/alerts",
    methods=["GET"]
)
@jwt_required()
def category_alerts():

    user_id = int(
        get_jwt_identity()
    )

    from models.expense_model import Expense

    budgets = CategoryBudget.query.filter_by(
        user_id=user_id
    ).all()

    alerts = []

    for budget in budgets:

        expenses = Expense.query.filter(
            Expense.user_id == user_id,
            db.func.lower(
                Expense.category
            ) == budget.category.lower()
        ).all()

        spent = sum(

            e.amount
            for e in expenses

        )

        percentage = 0

        if budget.monthly_limit > 0:

            percentage = (

                spent /
                budget.monthly_limit

            ) * 100

        if percentage >= 100:

            alerts.append({

                "category":
                budget.category,

                "message":
                f"{budget.category} budget exceeded",

                "level":
                "danger"

            })

        elif percentage >= 80:

            alerts.append({

                "category":
                budget.category,

                "message":
                f"{budget.category} budget reached 80%",

                "level":
                "warning"

            })

    return jsonify({
        "alerts": alerts,
        "count": len(alerts)
    })


@category_budget.route(
    "/risk-score",
    methods=["GET"]
)
@jwt_required()
def risk_score():

    user_id = int(get_jwt_identity())

    from models.expense_model import Expense
    from services.ai_budget_engine import (
        calculate_risk_score,
        predict_month_end_spending,
    )

    expenses = Expense.query.filter_by(user_id=user_id).all()

    total_spending = sum(e.amount for e in expenses)

    budget_data = Budget.query.filter_by(user_id=user_id).first()
    monthly_budget = budget_data.monthly_budget if budget_data else (User.query.get(user_id).available_budget or 0)

    predicted = predict_month_end_spending(expenses)

    risk = calculate_risk_score(
        total_spending,
        monthly_budget,
        predicted
    )

    return jsonify({
        "risk_score": risk.get("score", 0),
        "risk_level": risk.get("level", "UNKNOWN"),
    })


@category_budget.route(
    "/savings-recommendations",
    methods=["GET"]
)
@jwt_required()
def savings_recommendations():

    user_id = int(get_jwt_identity())

    from models.expense_model import Expense

    budgets = CategoryBudget.query.filter_by(user_id=user_id).all()

    recommendations = []
    total_possible_savings = 0

    for budget in budgets:
        expenses = Expense.query.filter(
            Expense.user_id == user_id,
            db.func.lower(
                Expense.category
            ) == budget.category.lower()
        ).all()
        spent = sum(e.amount for e in expenses)
        remaining = budget.monthly_limit - spent
        if remaining > 0:
            recommendations.append({
                "category": budget.category,
                "message": f"You can save ₹{round(remaining,2)} in {budget.category} by staying within the budget",
                "possible_savings": round(remaining,2)
            })
            total_possible_savings += remaining

    return jsonify({
        "recommendations": recommendations,
        "total_possible_savings": round(total_possible_savings,2)
    })