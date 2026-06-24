import threading
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (jwt_required,get_jwt_identity)
from database.db import db
from services.category_alert_service import (check_category_alerts)
from services.email_service import (send_category_alert)
from models.expense_model import Expense
from services.backup_service import backup_expenses
from services.sms_parser import parse_expense_sms
from services.email_service import send_budget_alert
from models.category_budget_model import CategoryBudget
from services.ai_budget_engine import detect_overspending
from services.sms_service import send_sms
from models.user_model import User
expense = Blueprint(
    'expense',
    __name__
)

def async_backup_expenses():
    app = current_app._get_current_object()
    def task():
        with app.app_context():
            backup_expenses()
    threading.Thread(target=task, daemon=True).start()
def get_total_spending(user_id):
    now = datetime.now()
    current_month_start = datetime(now.year, now.month, 1)

    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.created_at >= current_month_start
    ).all()
    total = 0
    for expense in expenses:
        total += expense.amount
    return total

def create_expense(user_id, title, amount, category, payment_method):
    new_expense = Expense(
        user_id=user_id,
        title=title,
        amount=amount,
        category=category,
        payment_method=payment_method
    )
    db.session.add(new_expense)
    db.session.commit()

    async_backup_expenses()

    return new_expense


BUDGET_ALERT_THRESHOLDS = [
    (100, "budget_alert_100_sent"),
    (90, "budget_alert_90_sent"),
    (75, "budget_alert_75_sent"),
    (50, "budget_alert_50_sent"),
]


def _build_budget_sms_text(threshold, spent, budget):
    remaining = max(round(budget - spent), 0)
    spent_amount = round(spent)
    budget_amount = round(budget)

    if threshold >= 100:
        exceeded_by = max(round(spent - budget), 0)
        return (
            "Budget Alert - 100% Used\n"
            f"Budget: Rs. {budget_amount}\n"
            f"Spent: Rs. {spent_amount}\n"
            f"Remaining: Rs. 0\n"
            f"Exceeded by: Rs. {exceeded_by}"
        )

    return (
        f"Budget Alert - {threshold}% Used\n"
        f"Budget: Rs. {budget_amount}\n"
        f"Spent: Rs. {spent_amount}\n"
        f"Remaining: Rs. {remaining}"
    )


def _mark_reached_budget_alerts_sent(user, threshold):
    for reached_threshold, flag_attr in BUDGET_ALERT_THRESHOLDS:
        if reached_threshold <= threshold:
            setattr(user, flag_attr, True)


def _send_overall_budget_alerts(user, total_spending):
    monthly_budget = float(user.available_budget or 0)
    if monthly_budget <= 0:
        return

    percentage = (total_spending / monthly_budget) * 100

    for threshold, flag_attr in BUDGET_ALERT_THRESHOLDS:
        if percentage < threshold or getattr(user, flag_attr):
            continue

        sent_any_channel = False

        if user.email:
            try:
                send_budget_alert(
                    user.email,
                    threshold,
                    total_spending,
                    monthly_budget
                )
                sent_any_channel = True
            except Exception as error:
                print("Budget email sending failed:", error)

        if user.phone:
            try:
                sms_sid = send_sms(
                    user.phone,
                    _build_budget_sms_text(
                        threshold,
                        total_spending,
                        monthly_budget
                    )
                )
                sent_any_channel = sent_any_channel or bool(sms_sid)
            except Exception as error:
                print("Budget SMS sending failed:", error)

        if not sent_any_channel:
            print("Budget alert not marked sent because no channel delivered.")
            break

        _mark_reached_budget_alerts_sent(user, threshold)
        db.session.commit()
        break


# =========================================
# ADD EXPENSE
# =========================================
@expense.route('/add', methods=['POST'])
@jwt_required()
def add_expense():

    current_user_id = int(get_jwt_identity())

    data = request.get_json(silent=True) or {}

    title = (data.get('title') or '').strip()
    category = (data.get('category') or '').strip().title()

    payment_method = (
        (data.get('payment_method') or '')
        .strip()
        .lower()
    )

    if payment_method in [
        "gpay",
        "google pay",
        "phonepe",
        "paytm",
        "upi"
    ]:
        payment_method = "UPI"

    elif payment_method in [
        "credit card",
        "debit card",
        "card"
    ]:
        payment_method = "Card"

    elif payment_method in [
        "net banking",
        "netbanking",
        "neft",
        "imps"
    ]:
        payment_method = "Net Banking"

    # Validate amount
    try:

        amount = float(data.get('amount'))

    except (TypeError, ValueError):

        return jsonify({
            "message": "Amount must be a number"
        }), 400

    # Validate title/category
    if not title or not category:

        return jsonify({
            "message": "Title and category are required"
        }), 400

    # Validate amount > 0
    if amount <= 0:

        return jsonify({
            "message": "Amount must be greater than zero"
        }), 400

    # Create expense - this is the only part the user needs to wait on
    create_expense(
        current_user_id,
        title,
        amount,
        category,
        payment_method
    )

    total_spending = get_total_spending(
        current_user_id
    )
    overspending_alerts = detect_overspending(
        current_user_id
    )

    print("OVERSPENDING ALERTS =", overspending_alerts)

    # =========================================
    # NOTIFICATIONS (email, SMS, AI advice) run
    # in the background so the response returns
    # immediately instead of waiting on SMTP/Twilio/
    # OpenAI round-trips, which can each take seconds.
    # =========================================
    _run_expense_notifications_async(current_user_id, total_spending)

    return jsonify({
        "message": "Expense added successfully",
        "total_spending": total_spending,
        "overspending_alerts": overspending_alerts
    }), 201


def _run_expense_notifications_async(current_user_id, total_spending):
    app = current_app._get_current_object()

    def task():
        with app.app_context():
            try:
                current_user = User.query.get(current_user_id)
                if not current_user:
                    return

                # Category-level alerts (email + SMS), includes AI advice
                print("CHECK_CATEGORY_ALERTS CALLED")
                alerts = check_category_alerts(current_user_id)
                print("CATEGORY ALERT RESULT =", alerts)

                # Only notify for thresholds that haven't already been
                # sent this month for that category - prevents the same
                # tier (e.g. 50%) from spamming an SMS/email on every
                # single expense added while spending stays in that band.
                new_alerts = [a for a in alerts if a.get("should_notify")]

                for alert in new_alerts:
                    try:
                        send_category_alert(
                            current_user.email,
                            alert["category"],
                            alert["percent"],
                            alert["type"]
                        )
                    except Exception as error:
                        print("Category email sending failed:", error)

                if current_user.phone:
                    for alert in new_alerts:
                        try:
                            category = alert['category']
                            budget_amount = round(alert['budget'])
                            spent_amount = round(alert['spent'])
                            remaining_amount = round(alert['remaining'])
                            ai_note = (alert.get('ai_recommendation') or '').strip()
                            # Keep the AI note short for SMS - first sentence only
                            ai_note_short = ai_note.split('.')[0].strip()
                            if ai_note_short and not ai_note_short.endswith('.'):
                                ai_note_short += '.'

                            if alert['percent'] >= 100:
                                extra_amount = round(alert['spent'] - alert['budget'])
                                sms_text = (
                                    f"⚠ {category} Budget Alert\n"
                                    f"Budget: ₹{budget_amount}\n"
                                    f"Spent: ₹{spent_amount}\n"
                                    f"Remaining: ₹0\n"
                                    f"You have exceeded by ₹{extra_amount}"
                                )
                            else:
                                sms_text = (
                                    f"⚠ {category} Budget Alert\n"
                                    f"Budget: ₹{budget_amount}\n"
                                    f"Spent: ₹{spent_amount} ({alert['percent']}%)\n"
                                    f"Remaining: ₹{remaining_amount}"
                                )

                            if ai_note_short:
                                sms_text += f"\n💡 {ai_note_short}"

                            send_sms(current_user.phone, sms_text)
                        except Exception as error:
                            print("SMS sending failed:", error)

                # Overall monthly-budget alerts (email + SMS), one time per threshold.
                try:
                    _send_overall_budget_alerts(current_user, total_spending)
                except Exception as error:
                    print("Budget alert sending failed:", error)

            except Exception as error:
                print("Background notification task failed:", error)

    threading.Thread(target=task, daemon=True).start()
# =========================================
# GET ALL EXPENSES
# =========================================
@expense.route('/all', methods=['GET'])
@jwt_required()
def get_expenses():

    current_user_id = int(
        get_jwt_identity()
    )

    expenses = Expense.query.filter_by(
        user_id=current_user_id
    ).order_by(
        Expense.created_at.desc()
    ).all()

    expense_list = []

    for item in expenses:

        expense_list.append({

            "id": item.id,

            "title": item.title,

            "amount": float(item.amount),

            "category": item.category,

            "payment_method": item.payment_method,

            "created_at": (
                item.created_at.isoformat()
                if item.created_at
                else None
            )

        })

    return jsonify({
        "expenses": expense_list
    }), 200
# =========================================
# DELETE EXPENSE
# =========================================
@expense.route('/delete/<int:expense_id>', methods=['DELETE'])
@jwt_required()
def delete_expense(expense_id):

    current_user_id = int(
        get_jwt_identity()
    )

    expense_item = Expense.query.filter_by(

        id=expense_id,

        user_id=current_user_id

    ).first()

    if not expense_item:

        return jsonify({
            "message": "Expense not found"
        }), 404

    db.session.delete(
        expense_item
    )

    db.session.commit()

    async_backup_expenses()

    return jsonify({

        "message":
        "Expense deleted successfully"

    }), 200
# =========================================
# SMS PREVIEW
# =========================================
@expense.route('/sms/preview', methods=['POST'])
@jwt_required()
def preview_sms_expense():

    data = (
        request.get_json(
            silent=True
        ) or {}
    )

    sms_text = (
        data.get(
            'sms_text'
        ) or ''
    )

    parsed = parse_expense_sms(
        sms_text
    )

    status_code = (
        200
        if parsed.get(
            'is_expense'
        )
        else 400
    )

    response = {
        "parsed": parsed
    }

    if not parsed.get(
        'is_expense'
    ):

        response["message"] = (
            parsed.get(
                'error'
            )
            or
            "Could not parse SMS"
        )

    return jsonify(
        response
    ), status_code


# =========================================
# ADD EXPENSE FROM SMS
# =========================================
@expense.route('/sms/add', methods=['POST'])
@jwt_required()
def add_sms_expense():

    current_user_id = int(
        get_jwt_identity()
    )

    data = (
        request.get_json(
            silent=True
        ) or {}
    )

    sms_text = (
        data.get(
            'sms_text'
        ) or ''
    )

    parsed = parse_expense_sms(
        sms_text
    )

    if not parsed.get(
        'is_expense'
    ):

        return jsonify({
            "message":
            parsed.get(
                'error'
            )
            or
            "Could not parse SMS"
        }), 400

    title = (data.get('title') or '').strip()

    category = (
        (data.get('category') or '')
        .strip()
        .title()
    )

    payment_method = (
        (data.get('payment_method') or '')
        .strip()
        .lower()
    )

    if payment_method in [
        "gpay",
        "google pay",
        "phonepe",
        "paytm",
        "upi"
    ]:
        payment_method = "UPI"

    elif payment_method in [
        "credit card",
        "debit card",
        "card"
    ]:
        payment_method = "Card"

    elif payment_method in [
        "net banking",
        "netbanking",
        "neft",
        "imps"
    ]:
        payment_method = "Net Banking"

    try:

        amount = float(

            data.get('amount')

            or

            parsed.get('amount')

        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify({
            "message":
            "Parsed amount is invalid"
        }), 400

    if not title or not category:

        return jsonify({
            "message":
            "Parsed title and category are required"
        }), 400

    if amount <= 0:

        return jsonify({
            "message":
            "Parsed amount must be greater than zero"
        }), 400

    new_expense = create_expense(

        current_user_id,

        title,

        amount,

        category,

        payment_method

    )

    total_spending = get_total_spending(
        current_user_id
    )

    _run_expense_notifications_async(current_user_id, total_spending)

    return jsonify({

        "message":
        "SMS expense added successfully",

        "expense": {

            "id":
            new_expense.id,

            "title":
            new_expense.title,

            "amount":
            float(
                new_expense.amount
            ),

            "category":
            new_expense.category,

            "payment_method":
            new_expense.payment_method

        },

        "total_spending":
        total_spending

    }), 201

# =========================================
# UPDATE EXPENSE
# =========================================
@expense.route('/update/<int:expense_id>', methods=['PUT'])
@jwt_required()
def update_expense(expense_id):

    current_user_id = int(
        get_jwt_identity()
    )

    expense_item = Expense.query.filter_by(
        id=expense_id,
        user_id=current_user_id
    ).first()

    if not expense_item:

        return jsonify({
            "message": "Expense not found"
        }), 404

    data = request.get_json(
        silent=True
    ) or {}

    title = (
        data.get('title') or ''
    ).strip()

    category = (
        data.get('category') or ''
    ).strip().title()

    payment_method = (
        data.get('payment_method') or ''
    ).strip()

    try:

        amount = float(
            data.get('amount')
        )

    except (TypeError, ValueError):

        return jsonify({
            "message": "Invalid amount"
        }), 400

    if not title:

        return jsonify({
            "message": "Title is required"
        }), 400

    if not category:

        return jsonify({
            "message": "Category is required"
        }), 400

    if amount <= 0:

        return jsonify({
            "message":
            "Amount must be greater than zero"
        }), 400

    expense_item.title = title
    expense_item.amount = amount
    expense_item.category = category
    expense_item.payment_method = payment_method

    db.session.commit()

    async_backup_expenses()

    return jsonify({
        "message":
        "Expense updated successfully"
    }), 200

@expense.route(
    '/latest',
    methods=['GET']
)
@jwt_required()
def latest_expenses():

    user_id = int(
        get_jwt_identity()
    )

    expenses = Expense.query.filter_by(
        user_id=user_id
    ).order_by(
        Expense.id.desc()
    ).limit(10).all()

    result = []

    for item in expenses:

        result.append({
            "id": item.id,
            "title": item.title,
            "amount": item.amount,
            "category": item.category,
            "payment_method": item.payment_method,
            "created_at": str(item.created_at)
            if item.created_at else None
        })

    return jsonify(result)

@expense.route(
    "/category-history",
    methods=["GET"]
)
@jwt_required()
def category_history():

    user_id = int(
        get_jwt_identity()
    )

    budgets = CategoryBudget.query.filter_by(
        user_id=user_id
    ).all()

    result = {}

    for budget in budgets:

        category_name = budget.category

        expenses = Expense.query.filter_by(
            user_id=user_id,
            category=category_name
        ).order_by(
            Expense.id.desc()
        ).limit(10).all()

        spent = 0

        expense_list = []

        for item in expenses:

            spent += float(item.amount)

            expense_list.append({

                "id":
                    item.id,

                "title":
                    item.title,

                "amount":
                    float(item.amount),

                "payment_method":
                    item.payment_method
            })

        budget_limit = float(
            budget.monthly_limit
        )

        percentage = 0

        if budget_limit > 0:

            percentage = round(
                (spent / budget_limit) * 100,
                2
            )

        status = "SAFE"

        if percentage >= 100:

            status = "EXCEEDED"

        elif percentage >= 80:

            status = "WARNING"

        result[
            category_name
        ] = {

            "budget":
                budget_limit,

            "spent":
                spent,

            "percentage":
                percentage,

            "status":
                status,

            "expenses":
                expense_list
        }

    return jsonify(result)

@expense.route(
    "/latest-by-category",
    methods=["GET"]
)
@jwt_required()
def latest_by_category():

    user_id = int(
        get_jwt_identity()
    )

    expenses = Expense.query.filter_by(
        user_id=user_id
    ).order_by(
        Expense.created_at.desc()
    ).limit(10).all()

    result = {}

    for expense in expenses:

        category = expense.category

        if category not in result:

            result[category] = []

        result[category].append({

            "title":
            expense.title,

            "amount":
            expense.amount,

            "date":
            expense.created_at.strftime(
                "%d-%m-%Y"
            )

        })

    return jsonify(result)
