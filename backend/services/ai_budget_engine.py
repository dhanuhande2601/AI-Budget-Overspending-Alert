from datetime import datetime, timedelta

from sqlalchemy import func

from models.expense_model import Expense
from models.user_model import User


def detect_overspending(user_id):
    today = datetime.utcnow()
    current_week = today - timedelta(days=7)
    previous_week = today - timedelta(days=14)

    current_week_expenses = (
        Expense.query
        .with_entities(
            Expense.category,
            func.sum(Expense.amount)
        )
        .filter(
            Expense.user_id == user_id,
            Expense.created_at >= current_week
        )
        .group_by(Expense.category)
        .all()
    )

    previous_week_expenses = (
        Expense.query
        .with_entities(
            Expense.category,
            func.sum(Expense.amount)
        )
        .filter(
            Expense.user_id == user_id,
            Expense.created_at >= previous_week,
            Expense.created_at < current_week
        )
        .group_by(Expense.category)
        .all()
    )

    previous_dict = {
        category: amount
        for category, amount in previous_week_expenses
    }

    alerts = []

    for category, current_amount in current_week_expenses:
        previous_amount = previous_dict.get(category, 0)

        if previous_amount > 0:
            increase_percentage = (
                (current_amount - previous_amount) / previous_amount
            ) * 100

            if increase_percentage >= 40:
                alerts.append({
                    'category': category,
                    'previous_week': round(previous_amount, 2),
                    'current_week': round(current_amount, 2),
                    'increase_percentage': round(increase_percentage, 2),
                    'alert': f'{category} spending increased {round(increase_percentage, 2)}% this week'
                })

    return alerts


from datetime import datetime

def predict_month_end_spending(expenses):

    if not expenses:
        return 0

    total_spending = sum(
        expense.amount
        for expense in expenses
    )

    today = datetime.now().day

    # First 3 days of month → prediction unstable
    if today <= 3:
        return total_spending

    average_daily_spending = (
        total_spending / today
    )

    predicted_total = (
        average_daily_spending * 30
    )

    return round(
        predicted_total,
        2
    )


def generate_smart_advice(category_summary):
    advice = []

    for item in category_summary:
        category = item['category']
        amount = item['amount']

        if amount >= 5000:
            advice.append(f'High spending detected in {category}')
        elif amount >= 3000:
            advice.append(f'Try reducing {category} expenses')
        else:
            advice.append(f'{category} spending looks healthy')

    return advice


def budget_usage_alerts(user_id):
    user = User.query.get(user_id)

    if not user:
        return []

    monthly_budget = user.available_budget or 0

    if monthly_budget <= 0:
        return []

    expenses = Expense.query.filter_by(
        user_id=user_id
    ).all()

    total_spending = 0

    for item in expenses:
        total_spending += item.amount

    usage_percent = (total_spending / monthly_budget) * 100
    alerts = []

    if usage_percent >= 100:
        alerts.append({
            'level': 'critical',
            'message': 'Budget exceeded completely'
        })
    elif usage_percent >= 90:
        alerts.append({
            'level': 'danger',
            'message': '90% budget used'
        })
    elif usage_percent >= 75:
        alerts.append({
            'level': 'warning',
            'message': '75% budget used'
        })
    elif usage_percent >= 50:
        alerts.append({
            'level': 'info',
            'message': '50% budget used'
        })

    return alerts
def calculate_risk_score(
    total_spending,
    monthly_budget,
    predicted_spending
):

    if monthly_budget <= 0:
        return {
            "score": 0,
            "level": "UNKNOWN"
        }

    usage = (
        total_spending /
        monthly_budget
    ) * 100

    score = 0

    if usage >= 50:
        score += 30

    if usage >= 75:
        score += 30

    if usage >= 90:
        score += 20

    if predicted_spending > monthly_budget:
        score += 20

    if score >= 80:
        level = "HIGH"

    elif score >= 50:
        level = "MEDIUM"

    else:
        level = "LOW"

    return {
        "score": score,
        "level": level
    }