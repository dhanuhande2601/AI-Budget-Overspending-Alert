from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from sqlalchemy import func

from database.db import db
from models.budget_history_model import BudgetHistory
from models.expense_model import Expense
from models.user_model import User

budget_history = Blueprint('budget_history', __name__)


def _build_live_current_month(user_id):
    """
    Calculates the current month's spending live from actual Expense
    rows (never saved to BudgetHistory until month-end), so Budget
    History always reflects expenses added today/this month without
    waiting for the scheduler's month-end snapshot.
    """
    user = User.query.get(user_id)
    if not user:
        return None

    now = datetime.utcnow()
    month, year = now.month, now.year

    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        func.extract('month', Expense.created_at) == month,
        func.extract('year', Expense.created_at) == year
    ).all()

    total_spent = sum(float(e.amount) for e in expenses)
    monthly_budget = float(user.available_budget or 0)
    total_saved = max(monthly_budget - total_spent, 0)
    overspent = total_spent > monthly_budget

    category_totals = {}
    for e in expenses:
        cat = e.category or 'Other'
        category_totals[cat] = category_totals.get(cat, 0) + float(e.amount)
    top_category = max(category_totals, key=category_totals.get) if category_totals else None

    return {
        'month': month,
        'year': year,
        'monthly_budget': monthly_budget,
        'total_spent': total_spent,
        'total_saved': total_saved,
        'overspent': overspent,
        'top_category': top_category,
    }


# =========================================
# GET ALL BUDGET HISTORY (includes live current month)
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

    # Live current month goes first, marked as in-progress, and is
    # never read from the saved BudgetHistory table.
    live = _build_live_current_month(user_id)
    if live:
        month_name = datetime(live['year'], live['month'], 1).strftime('%b %Y')
        result.append({
            'id': 'current',
            'month': live['month'],
            'year': live['year'],
            'month_label': month_name,
            'monthly_budget': live['monthly_budget'],
            'total_spent': live['total_spent'],
            'total_saved': live['total_saved'],
            'overspent': live['overspent'],
            'top_category': live['top_category'],
            'usage_percent': round(
                (live['total_spent'] / live['monthly_budget'] * 100)
                if live['monthly_budget'] > 0 else 0, 1
            ),
            'is_current': True,
        })

    for r in records:
        # Skip a saved row for the current month if one somehow exists,
        # so we don't show it twice (live version above takes priority).
        if live and r.month == live['month'] and r.year == live['year']:
            continue

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
            ),
            'is_current': False,
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

    live = _build_live_current_month(user_id)
    if not live:
        return jsonify({'message': 'Could not calculate current month data'}), 400

    existing = BudgetHistory.query.filter_by(
        user_id=user_id,
        month=live['month'],
        year=live['year']
    ).first()

    if existing:
        existing.monthly_budget = live['monthly_budget']
        existing.total_spent = live['total_spent']
        existing.total_saved = live['total_saved']
        existing.overspent = live['overspent']
        existing.top_category = live['top_category']
    else:
        db.session.add(BudgetHistory(
            user_id=user_id,
            month=live['month'],
            year=live['year'],
            monthly_budget=live['monthly_budget'],
            total_spent=live['total_spent'],
            total_saved=live['total_saved'],
            overspent=live['overspent'],
            top_category=live['top_category']
        ))

    db.session.commit()

    return jsonify({'message': 'Snapshot saved successfully'}), 200


# =========================================
# GET SUMMARY STATS (for charts) — includes live current month
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

    live = _build_live_current_month(user_id)

    # Build the combined list (saved months + live current month),
    # skipping any saved row that duplicates the current month.
    combined = [
        r for r in records
        if not (live and r.month == live['month'] and r.year == live['year'])
    ]

    chart_data = [{
        'month_label': datetime(r.year, r.month, 1).strftime('%b %Y'),
        'budget': r.monthly_budget,
        'spent': r.total_spent,
        'saved': r.total_saved,
        'is_current': False,
    } for r in combined]

    if live:
        chart_data.append({
            'month_label': datetime(live['year'], live['month'], 1).strftime('%b %Y') + ' (In Progress)',
            'budget': live['monthly_budget'],
            'spent': live['total_spent'],
            'saved': live['total_saved'],
            'is_current': True,
        })

    all_for_stats = combined + ([live] if live else [])

    if not all_for_stats:
        return jsonify({
            'total_months': 0,
            'avg_spent': 0,
            'avg_saved': 0,
            'overspent_months': 0,
            'best_month': None,
            'worst_month': None,
            'chart_data': []
        }), 200

    def get_spent(item):
        return item.total_spent if hasattr(item, 'total_spent') else item['total_spent']

    def get_saved(item):
        return item.total_saved if hasattr(item, 'total_saved') else item['total_saved']

    def get_overspent(item):
        return item.overspent if hasattr(item, 'overspent') else item['overspent']

    def get_label(item):
        if hasattr(item, 'month'):
            return datetime(item.year, item.month, 1).strftime('%b %Y')
        return datetime(item['year'], item['month'], 1).strftime('%b %Y')

    total_months = len(all_for_stats)
    avg_spent = round(sum(get_spent(r) for r in all_for_stats) / total_months, 2)
    avg_saved = round(sum(get_saved(r) for r in all_for_stats) / total_months, 2)
    overspent_months = sum(1 for r in all_for_stats if get_overspent(r))

    best = min(all_for_stats, key=get_spent)
    worst = max(all_for_stats, key=get_spent)

    return jsonify({
        'total_months': total_months,
        'avg_spent': avg_spent,
        'avg_saved': avg_saved,
        'overspent_months': overspent_months,
        'best_month': get_label(best),
        'worst_month': get_label(worst),
        'chart_data': chart_data
    }), 200