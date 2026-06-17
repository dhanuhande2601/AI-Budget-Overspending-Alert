from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from sqlalchemy import func
 
from database.db import db
from models.budget_history_model import BudgetHistory
from models.expense_model import Expense
from models.user_model import User
 
budget_history = Blueprint('budget_history', __name__)
 
 
# =========================================
# GET ALL BUDGET HISTORY
# =========================================
@budget_history.route('/all', methods=['GET'])
@jwt_required()
def get_budget_history():
    user_id = int(get_jwt_identity())
 
    records = BudgetHistory.query.filter_by(
        user_id=user_id
    ).order_by(
        BudgetHistory.year.desc(),
        BudgetHistory.month.desc()
    ).all()
 
    result = []
    for r in records:
        month_name = datetime(r.year, r.month, 1).strftime('%b %Y')
        result.append({
            'id': r.id,
            'month': r.month,
            'year': r.year,
            'month_label': month_name,
            'monthly_budget': r.monthly_budget,
            'total_spent': r.total_spent,
            'total_saved': r.total_saved,
            'overspent': r.overspent,
            'top_category': r.top_category,
            'usage_percent': round(
                (r.total_spent / r.monthly_budget * 100)
                if r.monthly_budget > 0 else 0, 1
            )
        })
 
    return jsonify(result), 200
 
 
# =========================================
# SAVE CURRENT MONTH SNAPSHOT
# (called manually or by scheduler)
# =========================================
@budget_history.route('/snapshot', methods=['POST'])
@jwt_required()
def save_snapshot():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
 
    if not user:
        return jsonify({'message': 'User not found'}), 404
 
    now = datetime.utcnow()
    month = now.month
    year = now.year
 
    # Get all expenses for this month
    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        func.extract('month', Expense.created_at) == month,
        func.extract('year', Expense.created_at) == year
    ).all()
 
    total_spent = sum(float(e.amount) for e in expenses)
    monthly_budget = float(user.available_budget or 0)
    total_saved = max(monthly_budget - total_spent, 0)
    overspent = total_spent > monthly_budget
 
    # Find top spending category
    category_totals = {}
    for e in expenses:
        cat = e.category or 'Other'
        category_totals[cat] = category_totals.get(cat, 0) + float(e.amount)
 
    top_category = max(category_totals, key=category_totals.get) if category_totals else None
 
    # Upsert — update if exists else create
    existing = BudgetHistory.query.filter_by(
        user_id=user_id,
        month=month,
        year=year
    ).first()
 
    if existing:
        existing.monthly_budget = monthly_budget
        existing.total_spent = total_spent
        existing.total_saved = total_saved
        existing.overspent = overspent
        existing.top_category = top_category
    else:
        db.session.add(BudgetHistory(
            user_id=user_id,
            month=month,
            year=year,
            monthly_budget=monthly_budget,
            total_spent=total_spent,
            total_saved=total_saved,
            overspent=overspent,
            top_category=top_category
        ))
 
    db.session.commit()
 
    return jsonify({'message': 'Snapshot saved successfully'}), 200
 
 
# =========================================
# GET SUMMARY STATS (for charts)
# =========================================
@budget_history.route('/summary', methods=['GET'])
@jwt_required()
def get_summary():
    user_id = int(get_jwt_identity())
 
    records = BudgetHistory.query.filter_by(
        user_id=user_id
    ).order_by(
        BudgetHistory.year.asc(),
        BudgetHistory.month.asc()
    ).all()
 
    if not records:
        return jsonify({
            'total_months': 0,
            'avg_spent': 0,
            'avg_saved': 0,
            'overspent_months': 0,
            'best_month': None,
            'worst_month': None,
            'chart_data': []
        }), 200
 
    total_months = len(records)
    avg_spent = round(sum(r.total_spent for r in records) / total_months, 2)
    avg_saved = round(sum(r.total_saved for r in records) / total_months, 2)
    overspent_months = sum(1 for r in records if r.overspent)
 
    best = min(records, key=lambda r: r.total_spent)
    worst = max(records, key=lambda r: r.total_spent)
 
    chart_data = [{
        'month_label': datetime(r.year, r.month, 1).strftime('%b %Y'),
        'budget': r.monthly_budget,
        'spent': r.total_spent,
        'saved': r.total_saved,
    } for r in records]
 
    return jsonify({
        'total_months': total_months,
        'avg_spent': avg_spent,
        'avg_saved': avg_saved,
        'overspent_months': overspent_months,
        'best_month': datetime(best.year, best.month, 1).strftime('%b %Y'),
        'worst_month': datetime(worst.year, worst.month, 1).strftime('%b %Y'),
        'chart_data': chart_data
    }), 200
 