import threading
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (jwt_required,get_jwt_identity)
from database.db import db
from services.category_alert_service import (check_category_alerts)
from services.email_service import (send_category_alert)
from models.budget_notification_model import BudgetNotification
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
    expenses = Expense.query.filter_by(
        user_id=user_id
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
    user = User.query.get(current_user_id)
    expenses = Expense.query.filter_by(user_id=current_user_id).all()
    spent = sum(e.amount for e in expenses)
    budget = float(user.available_budget or 0)
    if budget > 0:
        percentage = (spent / budget) * 100
        if percentage >= 75 and not user.budget_alert_75_sent:
            send_budget_alert(user.email, percentage, spent, budget)
            user.budget_alert_75_sent = True
            db.session.commit()
        elif percentage >= 50 and not user.budget_alert_50_sent:
            send_budget_alert(user.email, percentage, spent, budget)
            user.budget_alert_50_sent = True
            db.session.commit()
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

    # Create expense
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
    # EMAIL ALERTS
    # =========================================
    current_user = User.query.get(
        current_user_id
    )

    sms_message = (
        f"Expense Added\n"
        f"Title: {title}\n"
        f"Amount: ₹{amount}\n"
        f"Category: {category}\n"
        f"Total Spending: ₹{total_spending}"
    )

    if current_user:

        # Category alerts should include the new expense
        print("CHECK_CATEGORY_ALERTS CALLED")
        
        alerts = check_category_alerts(
            current_user_id
        )
        print("CATEGORY ALERT RESULT =", alerts)

        for alert in alerts:
            
            try:
                send_category_alert(
                    current_user.email,
                    alert["category"],
                    alert["percent"],
                    alert["type"]
                )
                
            except Exception as error:
                print("Category email sending failed:", error)

        monthly_budget = float(
            current_user.available_budget or 0
        )

        if current_user.phone:
            for alert in alerts:
                try:
                    send_sms(
                        current_user.phone,
                        f"⚠ Budget Alert: {alert['category']} reached {alert['percent']}% of limit"
                    )
                except Exception as error:
                    print("SMS sending failed:", error)

        if monthly_budget > 0:
            percentage = (
                total_spending /
                monthly_budget
            ) * 100
            try:

                if percentage >= 75 and not user.budget_alert_75_sent:
                    send_budget_alert(user.email, percentage, spent, budget)
                    user.budget_alert_75_sent = True
                    db.session.commit()
                elif percentage >= 50 and not user.budget_alert_50_sent:
                    send_budget_alert(user.email, percentage, spent, budget)
                    user.budget_alert_50_sent = True
                    db.session.commit()

                elif (
                    percentage >= 90
                    and percentage < 100
                    and not current_user.budget_alert_90_sent
                ):
                    send_budget_alert(
                        current_user.email,
                        90,
                        total_spending,
                        monthly_budget
                    )
                    current_user.budget_alert_90_sent = True
                    db.session.commit()

                elif percentage >= 100 and not current_user.budget_alert_100_sent:
                    send_budget_alert(
                        current_user.email,
                        100,
                        total_spending,
                        monthly_budget
                    )
                    current_user.budget_alert_100_sent = True
                    db.session.commit()
                

            except Exception as error:

                print(
                    "Budget email sending failed:",
                    error
                )

    return jsonify({
        "message": "Expense added successfully",
        "total_spending": total_spending,
        "overspending_alerts": overspending_alerts
    }), 201
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