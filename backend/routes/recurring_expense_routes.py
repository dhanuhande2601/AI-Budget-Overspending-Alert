from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date
from database.db import db
from models.recurring_expense_model import RecurringExpense

recurring_expense = Blueprint('recurring_expense', __name__)

VALID_FREQUENCIES = ['monthly', 'weekly', 'yearly']


# =========================================
# CREATE RECURRING EXPENSE
# =========================================
@recurring_expense.route('/add', methods=['POST'])
@jwt_required()
def add_recurring_expense():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    title = (data.get('title') or '').strip()
    category = (data.get('category') or '').strip().title()
    frequency = (data.get('frequency') or 'monthly').strip().lower()
    payment_method = (data.get('payment_method') or '').strip()

    try:
        amount = float(data.get('amount'))
    except (TypeError, ValueError):
        return jsonify({"message": "Amount must be a number"}), 400

    try:
        day_of_month = int(data.get('day_of_month', 1))
    except (TypeError, ValueError):
        day_of_month = 1

    end_date = None
    end_date_str = (data.get('end_date') or '').strip()
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"message": "End date must be in YYYY-MM-DD format"}), 400

    if not title or not category:
        return jsonify({"message": "Title and category are required"}), 400

    if amount <= 0:
        return jsonify({"message": "Amount must be greater than zero"}), 400

    if frequency not in VALID_FREQUENCIES:
        return jsonify({"message": f"Frequency must be one of {VALID_FREQUENCIES}"}), 400

    if day_of_month < 1 or day_of_month > 28:
        return jsonify({"message": "Day of month must be between 1 and 28"}), 400

    if end_date and end_date < date.today():
        return jsonify({"message": "End date cannot be in the past"}), 400

    new_recurring = RecurringExpense(
        user_id=user_id,
        title=title,
        amount=amount,
        category=category,
        payment_method=payment_method,
        frequency=frequency,
        day_of_month=day_of_month,
        end_date=end_date,
        is_active=True,
    )

    db.session.add(new_recurring)
    db.session.commit()

    return jsonify({
        "message": "Recurring expense created successfully",
        "id": new_recurring.id
    }), 201


# =========================================
# GET ALL RECURRING EXPENSES
# =========================================
@recurring_expense.route('/all', methods=['GET'])
@jwt_required()
def get_recurring_expenses():
    user_id = int(get_jwt_identity())

    items = RecurringExpense.query.filter_by(user_id=user_id).all()

    result = [{
        "id": item.id,
        "title": item.title,
        "amount": float(item.amount),
        "category": item.category,
        "payment_method": item.payment_method,
        "frequency": item.frequency,
        "day_of_month": item.day_of_month,
        "is_active": item.is_active,
        "end_date": str(item.end_date) if item.end_date else None,
        "last_added_on": str(item.last_added_on) if item.last_added_on else None,
        "is_expired": bool(item.end_date and item.end_date < date.today()),
    } for item in items]

    return jsonify(result), 200


# =========================================
# TOGGLE ACTIVE / PAUSE
# =========================================
@recurring_expense.route('/toggle/<int:recurring_id>', methods=['PUT'])
@jwt_required()
def toggle_recurring_expense(recurring_id):
    user_id = int(get_jwt_identity())

    item = RecurringExpense.query.filter_by(
        id=recurring_id, user_id=user_id
    ).first()

    if not item:
        return jsonify({"message": "Recurring expense not found"}), 404

    item.is_active = not item.is_active
    db.session.commit()

    return jsonify({
        "message": "Updated successfully",
        "is_active": item.is_active
    }), 200


# =========================================
# DELETE RECURRING EXPENSE
# =========================================
@recurring_expense.route('/delete/<int:recurring_id>', methods=['DELETE'])
@jwt_required()
def delete_recurring_expense(recurring_id):
    user_id = int(get_jwt_identity())

    item = RecurringExpense.query.filter_by(
        id=recurring_id, user_id=user_id
    ).first()

    if not item:
        return jsonify({"message": "Recurring expense not found"}), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({"message": "Recurring expense deleted successfully"}), 200