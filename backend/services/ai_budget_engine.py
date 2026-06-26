from datetime import datetime, timedelta
import calendar
from models.expense_model import Expense
from models.user_model import User
 
 
from models.category_budget_model import CategoryBudget
 
from datetime import datetime

def detect_overspending(user_id):
    now = datetime.now()
    budgets = CategoryBudget.query.filter_by(user_id=user_id).all()
    current_month_start = datetime(now.year, now.month, 1)
    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.created_at >= current_month_start
    ).all()
    alerts = []
    for budget in budgets:
        budget_category = (budget.category or "").strip().title()
        spent = sum(
            float(exp.amount)
            for exp in expenses
            if (exp.category or "").strip().title() == budget_category
        )
 
        percentage = (
            spent / budget.monthly_limit * 100
            if budget.monthly_limit > 0
            else 0
        )
 
        if percentage >= 100:
 
            alerts.append({
                "category": budget_category,
                "message": f"{budget_category} budget exceeded",
                "spent": spent,
                "limit": budget.monthly_limit,
                "percentage": round(percentage, 2)
            })
 
        elif percentage >= 80:
 
            alerts.append({
                "category": budget_category,
                "message": f"{budget_category} budget is {round(percentage,2)}% used",
                "spent": spent,
                "limit": budget.monthly_limit,
                "percentage": round(percentage, 2)
            })
 
    return alerts
def predict_month_end_spending(expenses):
    if not expenses:
        return 0
 
    now = datetime.now()
    today_day = now.day
    current_month_days = calendar.monthrange(now.year, now.month)[1]
    remaining_days = current_month_days - today_day
 
    # Filter only current month expenses
    current_month_expenses = [
        e for e in expenses
        if e.created_at and e.created_at.month == now.month
        and e.created_at.year == now.year
    ]
 
    if not current_month_expenses:
        # No current month data — use all expenses as fallback
        current_month_expenses = expenses
 
    total_spending = sum(float(e.amount) for e in current_month_expenses)
 
    # Avoid division by zero
    if today_day <= 0:
        return round(total_spending, 2)
 
    # Daily average spending so far
    daily_avg = total_spending / today_day
 
    # Predicted = spent so far + (daily avg * remaining days)
    prediction = total_spending + (daily_avg * remaining_days)
 
    return round(prediction, 2)
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
            "level": "LOW"
        }
 
    current_usage = (
        total_spending /
        monthly_budget
    ) * 100
 
    predicted_usage = (
        predicted_spending /
        monthly_budget
    ) * 100
 
    score = (
        current_usage * 0.8
        +
        predicted_usage * 0.2
    )
 
    score = min(
        round(score),
        100
    )
 
    if score >= 80:
        level = "HIGH"
 
    elif score >= 60:
        level = "MEDIUM"
 
    else:
        level = "LOW"
 
    return {
        "score": score,
        "level": level
    }
