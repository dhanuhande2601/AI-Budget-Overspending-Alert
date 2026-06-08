from flask import Blueprint, request, jsonify

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)

from sqlalchemy import func

from database.db import db
from models.budget_model import Budget
from models.expense_model import Expense
from models.user_model import User

budget = Blueprint('budget', __name__)


@budget.route('/set-budget', methods=['POST'])
@jwt_required()
def set_budget():
    current_user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    try:
        monthly_budget = float(data.get('monthly_budget'))
    except (TypeError, ValueError):
        return jsonify({
            "message": "Monthly budget must be a number"
        }), 400

    if monthly_budget <= 0:
        return jsonify({
            "message": "Monthly budget must be greater than zero"
        }), 400

    existing_budget = Budget.query.filter_by(
        user_id=current_user_id
    ).first()

    if existing_budget:
        existing_budget.monthly_budget = monthly_budget
    else:
        db.session.add(Budget(
            user_id=current_user_id,
            monthly_budget=monthly_budget
        ))

    user = db.session.get(User, current_user_id)
    if user:
        user.available_budget = monthly_budget

    db.session.commit()

    return jsonify({
        "message": "Monthly budget saved successfully",
        "monthly_budget": monthly_budget
    }), 201


@budget.route('/budget-status', methods=['GET'])
@jwt_required()
def budget_status():
    current_user_id = int(get_jwt_identity())

    user = db.session.get(User, current_user_id)

    budget_data = Budget.query.filter_by(
        user_id=current_user_id
    ).first()

    total_spending = db.session.query(
        func.sum(Expense.amount)
    ).filter(
        Expense.user_id == current_user_id
    ).scalar() or 0

    monthly_budget = budget_data.monthly_budget if budget_data else (user.available_budget if user else 0)

    if not monthly_budget:
        return jsonify({
            "message": "No budget set",
            "monthly_budget": 0,
            "total_spending": float(total_spending),
            "usage_percentage": 0,
            "alert": None
        }), 200

    usage_percentage = (total_spending / monthly_budget) * 100

    alert = None
    if usage_percentage >= 100:
        alert = "Budget limit exceeded"
    elif usage_percentage >= 80:
        alert = "Warning: You used more than 80% of your monthly budget"

    return jsonify({
        "monthly_budget": monthly_budget,
        "total_spending": float(total_spending),
        "usage_percentage": round(usage_percentage, 2),
        "alert": alert
    }), 200
