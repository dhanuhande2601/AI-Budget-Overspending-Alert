from datetime import date
import calendar
from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from config import Config
from database.db import db
from models.budget_notification_model import BudgetNotification
from services.openai_recommendation_service import (
    get_ai_recommendation
)
from services.festival_prediction_service import (
    get_upcoming_festival
)
from services.openai_service import (
    generate_ai_coach,
    generate_ai_recommendation,
    generate_investment_suggestion,
)
from models.budget_history_model import BudgetHistory
from models.expense_model import Expense
from models.user_model import User
from models.category_budget_model import CategoryBudget
from services.ai_budget_engine import (
    budget_usage_alerts,
    calculate_risk_score,
    detect_overspending,
    generate_smart_advice,
    predict_month_end_spending,
)
from services.email_service import send_overspending_summary
from services.sms_service import send_sms

ai = Blueprint('ai', __name__)


def safe_text(value):
    if value is None:
        return ""
    return str(value).replace("₹", "Rs. ")


def _email_alerts_enabled(user):
    return getattr(user, "email_alert_enabled", True) is not False


def _sms_alerts_enabled(user):
    return Config.SMS_ALERTS_ENABLED or bool(getattr(user, "sms_alert_enabled", False))


def _send_daily_overspending_email(user, alerts):
    if not alerts or not user or not user.email or not _email_alerts_enabled(user):
        return

    today_key = date.today().isoformat()
    marker_title = f"Daily Overspending Email {today_key}"
    existing = BudgetNotification.query.filter_by(
        user_id=user.id,
        title=marker_title,
        notification_type="EMAIL"
    ).first()

    if existing:
        print("Daily overspending email skipped: already sent to", user.email)
        return

    send_overspending_summary(user.email, alerts)
    db.session.add(BudgetNotification(
        user_id=user.id,
        title=marker_title,
        message="Daily overspending summary email sent",
        notification_type="EMAIL"
    ))
    db.session.commit()


def _build_daily_overspending_sms(alerts):
    alert_lines = []
    for alert in alerts[:2]:
        category = alert.get("category", "Budget")
        threshold = alert.get("threshold") or round(float(alert.get("percentage") or 0))
        alert_lines.append(f"{category} {threshold}%")

    extra_count = len(alerts) - len(alert_lines)
    if extra_count > 0:
        alert_lines.append(f"{extra_count} more")

    return "Budget update: " + ", ".join(alert_lines) + ". Review in app."


def _send_daily_overspending_sms(user, alerts):
    if not alerts or not user or not user.phone or not _sms_alerts_enabled(user):
        if user and not user.phone:
            print("Daily overspending SMS skipped: user phone is missing")
        return

    today_key = date.today().isoformat()
    marker_title = f"Daily Overspending SMS {today_key}"
    existing = BudgetNotification.query.filter_by(
        user_id=user.id,
        title=marker_title,
        notification_type="SMS"
    ).first()

    if existing:
        print("Daily overspending SMS skipped: already sent to", user.phone)
        return

    sms_id = send_sms(user.phone, _build_daily_overspending_sms(alerts))
    if not sms_id:
        print("Daily overspending SMS failed: provider did not return id")
        return

    db.session.add(BudgetNotification(
        user_id=user.id,
        title=marker_title,
        message="Daily overspending summary SMS sent",
        notification_type="SMS"
    ))
    db.session.commit()


def current_month_context(user_id):
    user = User.query.get(user_id)
    if not user:
        return None

    today = date.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    all_expenses = Expense.query.filter_by(user_id=user_id).all()
    current_month_expenses = [
        expense for expense in all_expenses
        if expense.created_at
        and expense.created_at.month == today.month
        and expense.created_at.year == today.year
    ]

    total_spending = sum(float(expense.amount or 0) for expense in current_month_expenses)
    monthly_budget = float(user.available_budget or 0)
    monthly_income = float(user.monthly_income or 0)
    predicted_spending = predict_month_end_spending(current_month_expenses)
    remaining_budget = monthly_budget - total_spending
    projected_overspend = max(predicted_spending - monthly_budget, 0)
    remaining_days = max(days_in_month - today.day, 1)
    reduce_per_day = (
        round(projected_overspend / remaining_days, 2)
        if projected_overspend > 0 else 0
    )

    category_summary = {}
    for expense in current_month_expenses:
        category = (expense.category or "Other").strip().title()
        category_summary[category] = category_summary.get(category, 0) + float(expense.amount or 0)

    risk_data = calculate_risk_score(
        total_spending,
        monthly_budget,
        predicted_spending
    )

    daily_budget = (
        remaining_budget / remaining_days
        if remaining_days > 0 else 0
    )

    return {
        "user": user,
        "today": today,
        "days_in_month": days_in_month,
        "remaining_days": remaining_days,
        "expenses": current_month_expenses,
        "total_spending": total_spending,
        "monthly_budget": monthly_budget,
        "monthly_income": monthly_income,
        "predicted_spending": predicted_spending,
        "remaining_budget": remaining_budget,
        "projected_overspend": projected_overspend,
        "reduce_per_day": reduce_per_day,
        "category_summary": category_summary,
        "risk_data": risk_data,
        "daily_budget": daily_budget,
    }


# =========================================
# OVERSPENDING ALERTS
# =========================================
@ai.route('/overspending-alerts', methods=['GET'])
@jwt_required()
def overspending_alerts():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    alerts = detect_overspending(current_user_id)
    print("OVESPENDING ALERTS =", alerts)
    try:
        _send_daily_overspending_email(user, alerts)
    except Exception as error:
        print("Daily overspending email failed:", error)
    try:
        _send_daily_overspending_sms(user, alerts)
    except Exception as error:
        print("Daily overspending SMS failed:", error)

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
    ai_recommendation = safe_text(ai_recommendation)
    overspending_alerts_data = detect_overspending(current_user_id)

    print("OVESPENDING ALERTS =", overspending_alerts_data)
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
    ai_recommendation = safe_text(ai_recommendation)

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


# =========================================
# AI FINANCIAL INTELLIGENCE REPORT
# =========================================
@ai.route('/financial-report', methods=['GET'])
@jwt_required()
def financial_report():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    monthly_budget = float(user.available_budget or 0)
    monthly_income = float(user.monthly_income or 0)
    today = date.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]

    all_expenses = Expense.query.filter_by(user_id=user_id).all()

    # Scope "current spending" to THIS month only — using all-time
    # expenses here would make the comparison with last month meaningless,
    # and would also overstate predictions/risk for long-time users.
    current_month_expenses = [
        e for e in all_expenses
        if e.created_at and e.created_at.month == today.month and e.created_at.year == today.year
    ]

    total_spending = 0
    category_summary = {}
    for expense in current_month_expenses:
        total_spending += float(expense.amount)
        category = (expense.category or "").strip().title()
        category_summary[category] = category_summary.get(category, 0) + float(expense.amount)

    predicted_spending = predict_month_end_spending(all_expenses)
    projected_overspend = max(predicted_spending - monthly_budget, 0)

    risk_data = calculate_risk_score(total_spending, monthly_budget, predicted_spending)

    remaining_days = max(days_in_month - today.day, 1)
    remaining_budget = max(monthly_budget - total_spending, 0)
    daily_budget = monthly_budget / days_in_month if monthly_budget > 0 else 0

    # Daily reduction needed to land on-budget by month end, if overspend is projected
    daily_reduction_needed = (
        round(projected_overspend / remaining_days, 2)
        if projected_overspend > 0 else 0
    )

    # Top 3 categories by spend, formatted cleanly (no raw floats, no
    # categories that don't actually exist in the budget system)
    sorted_categories = sorted(
        category_summary.items(), key=lambda item: item[1], reverse=True
    )
    top_categories = [
        {"category": cat, "amount": round(amount, 2)}
        for cat, amount in sorted_categories[:3]
    ]

    # =========================================
    # LAST MONTH COMPARISON
    # =========================================
    if today.month == 1:
        prev_month, prev_year = 12, today.year - 1
    else:
        prev_month, prev_year = today.month - 1, today.year

    last_month_record = BudgetHistory.query.filter_by(
        user_id=user_id, month=prev_month, year=prev_year
    ).first()

    month_comparison = None
    if last_month_record and last_month_record.total_spent > 0:
        last_month_spent = float(last_month_record.total_spent)
        change_amount = total_spending - last_month_spent
        change_percent = round((change_amount / last_month_spent) * 100, 1)

        month_comparison = {
            "last_month_spent": round(last_month_spent, 2),
            "this_month_spent": round(total_spending, 2),
            "change_amount": round(change_amount, 2),
            "change_percent": change_percent,
            "trend": "up" if change_amount > 0 else ("down" if change_amount < 0 else "same"),
        }

    # =========================================
    # UPCOMING FESTIVAL
    # =========================================
    festival = get_upcoming_festival()

    # =========================================
    # AI TEXT RECOMMENDATION
    # =========================================
    ai_recommendation = generate_ai_recommendation(
        monthly_budget,
        total_spending,
        predicted_spending,
        daily_budget,
        remaining_budget,
        category_summary,
        festival
    )

    investment = generate_investment_suggestion(
        monthly_income=monthly_income,
        monthly_budget=monthly_budget,
        total_spending=total_spending,
        remaining_budget=remaining_budget,
        risk_level=risk_data["level"],
    )

    return jsonify({
        "projected_month_end_spending": round(predicted_spending, 2),
        "projected_overspend": round(projected_overspend, 2),
        "risk_level": risk_data["level"],
        "risk_score": risk_data["score"],
        "daily_reduction_needed": daily_reduction_needed,
        "top_categories": top_categories,
        "investment_suggestion": investment,
        "month_comparison": month_comparison,
        "festival": festival,
        "ai_recommendation": ai_recommendation,
    }), 200


@ai.route('/forecast', methods=['GET'])
@jwt_required()
def ai_forecast():
    user_id = int(get_jwt_identity())
    context = current_month_context(user_id)
    if not context:
        return jsonify({"message": "User not found"}), 404

    return jsonify({
        "forecast": round(context["predicted_spending"], 2),
        "projected_month_end_spending": round(context["predicted_spending"], 2),
        "overspend": round(context["projected_overspend"], 2),
        "projected_overspend": round(context["projected_overspend"], 2),
        "reduce_per_day": round(context["reduce_per_day"], 2),
        "remaining_days": context["remaining_days"],
        "remaining_budget": round(context["remaining_budget"], 2),
        "risk_level": context["risk_data"]["level"],
    }), 200


@ai.route('/score', methods=['GET'])
@jwt_required()
def ai_score():
    user_id = int(get_jwt_identity())
    context = current_month_context(user_id)
    if not context:
        return jsonify({"message": "User not found"}), 404

    return jsonify({
        "score": context["risk_data"]["score"],
        "risk_level": context["risk_data"]["level"],
        "budget_usage_percent": round(
            (context["total_spending"] / context["monthly_budget"]) * 100,
            2
        ) if context["monthly_budget"] > 0 else 0,
    }), 200


@ai.route('/savings-recommendation', methods=['GET'])
@jwt_required()
def savings_recommendation():
    user_id = int(get_jwt_identity())
    context = current_month_context(user_id)
    if not context:
        return jsonify({"message": "User not found"}), 404

    income = context["monthly_income"]
    remaining_budget = max(context["remaining_budget"], 0)
    configured_savings = float(context["user"].monthly_savings or 0)

    if context["risk_data"]["level"] == "HIGH":
        recommended = max(remaining_budget * 0.05, 0)
    elif configured_savings > 0:
        recommended = min(configured_savings, remaining_budget * 0.5)
    elif income > 0:
        recommended = min(income * 0.1, remaining_budget * 0.4)
    else:
        recommended = remaining_budget * 0.15

    return jsonify({
        "recommended_savings": round(max(recommended, 0), 2),
        "monthly_savings_target": round(configured_savings, 2),
        "remaining_budget": round(context["remaining_budget"], 2),
        "reason": (
            "Risk is high, so savings recommendation is conservative."
            if context["risk_data"]["level"] == "HIGH"
            else "Based on remaining budget and your savings target."
        ),
    }), 200


@ai.route('/coach', methods=['GET'])
@jwt_required()
def ai_coach():
    user_id = int(get_jwt_identity())
    context = current_month_context(user_id)
    if not context:
        return jsonify({"message": "User not found"}), 404

    coach = generate_ai_coach(
        total_spending=context["total_spending"],
        monthly_budget=context["monthly_budget"],
        predicted_spending=context["predicted_spending"],
        remaining_budget=context["remaining_budget"],
        category_summary=context["category_summary"],
        risk_level=context["risk_data"]["level"],
    )

    return jsonify({
        "coach": coach,
        "metrics": {
            "total_spending": round(context["total_spending"], 2),
            "monthly_budget": round(context["monthly_budget"], 2),
            "forecast": round(context["predicted_spending"], 2),
            "remaining_budget": round(context["remaining_budget"], 2),
            "risk_level": context["risk_data"]["level"],
        },
    }), 200


@ai.route('/weekly-challenge', methods=['GET'])
@jwt_required()
def weekly_challenge():
    user_id = int(get_jwt_identity())
    context = current_month_context(user_id)
    if not context:
        return jsonify({"message": "User not found"}), 404

    top_category = None
    if context["category_summary"]:
        top_category = max(
            context["category_summary"],
            key=context["category_summary"].get
        )

    challenges = [
        {
            "title": "No Food Delivery Monday",
            "task": "Skip Swiggy/Zomato today and log a home meal instead.",
            "reward": "Save around Rs. 200",
        },
        {
            "title": "Savings Tuesday",
            "task": "Move a small fixed amount to savings before spending.",
            "reward": "Build savings discipline",
        },
        {
            "title": "No Shopping Wednesday",
            "task": "Avoid impulse shopping for 24 hours.",
            "reward": "Protect your monthly budget",
        },
        {
            "title": "Tracking Thursday",
            "task": "Add every expense immediately after payment.",
            "reward": "Cleaner AI insights",
        },
        {
            "title": "Budget Friday",
            "task": "Keep today's spending below your daily budget.",
            "reward": "Stay closer to month-end target",
        },
        {
            "title": "Low-Spend Saturday",
            "task": "Choose one free or low-cost plan today.",
            "reward": "Reduce weekend overspending",
        },
        {
            "title": "Finance Sunday",
            "task": "Review top categories and set next week's spending limit.",
            "reward": "Better financial planning",
        },
    ]

    challenge = challenges[context["today"].weekday()]
    if top_category:
        challenge["focus_category"] = top_category
        challenge["task"] = (
            f"Control {top_category} spending today. "
            f"{challenge['task']}"
        )

    return jsonify(challenge), 200
