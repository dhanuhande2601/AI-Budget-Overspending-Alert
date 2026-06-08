from flask import (Blueprint, request, jsonify)
from models.user_model import User
from models.budget_model import Budget
from database.db import db
from utils.password_hash import hash_password
from flask_jwt_extended import create_access_token
from utils.password_hash import check_password
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.backup_service import backup_users
auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['POST'])
def register():

    data = request.get_json(silent=True) or {}

    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password')
    phone = (data.get('phone') or '').strip()

    if not name or not email or not password:
        return jsonify({
            "message": "Name, email, and password are required"
        }), 400

    try:

        monthly_income = float(
            data.get(
                'monthly_income',
                0
            )
        )

        monthly_savings = float(
            data.get(
                'monthly_savings',
                0
            )
        )

    except (TypeError, ValueError):

        return jsonify({
            "message":
            "Income and savings must be numbers"
        }), 400

    if monthly_income < 0:

        return jsonify({
            "message":
            "Income cannot be negative"
        }), 400

    if monthly_savings < 0:

        return jsonify({
            "message":
            "Savings cannot be negative"
        }), 400

    available_budget = (
        monthly_income -
        monthly_savings
    )

    existing_user = User.query.filter_by(email=email).first()
    if monthly_savings > monthly_income:

        return jsonify({
            "message":
            "Savings cannot be greater than income"
        }), 400
    if existing_user:
        return jsonify({
            "message": "User already exists"
        }), 400

    hashed_password = hash_password(password)

    new_user = User(

        name=name,
        email=email,
        password=hashed_password,
        phone=phone,
        monthly_income=monthly_income,
        monthly_savings=monthly_savings,
        available_budget=available_budget

    )

    db.session.add(new_user)
    db.session.flush()

    if available_budget > 0:
        db.session.add(
            Budget(
                user_id=new_user.id,
                monthly_budget=available_budget
            )
        )

    db.session.commit()
    backup_users()  # Call the backup function after user registration

    return jsonify({
        "message": "User registered successfully"
    }), 201

@auth.route('/login', methods=['POST'])
def login():

    data = request.get_json(silent=True) or {}

    email = (data.get('email') or '').strip().lower()
    password = data.get('password')

    if not email or not password:
        return jsonify({
            "message": "Email and password are required"
        }), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    if not check_password(password, user.password):
        return jsonify({
            "message": "Invalid password"
        }), 401

    access_token = create_access_token(identity=str(user.id))

    budget_data = Budget.query.filter_by(user_id=user.id).first()
    monthly_budget = (
        budget_data.monthly_budget
        if budget_data
        else user.available_budget
    )

    return jsonify({
        "message": "Login successful",
        "token": access_token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "monthly_income": user.monthly_income,
            "monthly_savings": user.monthly_savings,
            "available_budget": user.available_budget,
            "monthly_budget": monthly_budget,
        }
    }), 200

@auth.route('/profile', methods=['GET'])
@jwt_required()
def profile():

    current_user_id = int(get_jwt_identity())

    user = db.session.get(User, current_user_id)

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    budget_data = Budget.query.filter_by(user_id=user.id).first()
    monthly_budget = (
        budget_data.monthly_budget
        if budget_data
        else user.available_budget
    )

    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "monthly_income": user.monthly_income,
        "monthly_savings": user.monthly_savings,
        "available_budget": user.available_budget,
        "monthly_budget": monthly_budget,
    }), 200

@auth.route('/update-budget', methods=['PUT'])
@jwt_required()
def update_budget():

    current_user_id = int(
        get_jwt_identity()
    )

    user = db.session.get(
        User,
        current_user_id
    )

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    data = request.get_json(
        silent=True
    ) or {}

    monthly_budget = data.get("monthly_budget")

    if monthly_budget is not None:
        try:
            monthly_budget = float(monthly_budget)
        except (TypeError, ValueError):
            return jsonify({
                "message": "Budget must be numeric"
            }), 400

        if monthly_budget < 0:
            return jsonify({
                "message": "Budget cannot be negative"
            }), 400

        user.available_budget = monthly_budget

        budget = Budget.query.filter_by(
            user_id=user.id
        ).first()

        if budget:
            budget.monthly_budget = monthly_budget
        else:
            db.session.add(
                Budget(
                    user_id=user.id,
                    monthly_budget=monthly_budget
                )
            )

        db.session.commit()

        return jsonify({
            "message":
            "Monthly budget updated successfully",

            "monthly_income":
            user.monthly_income,

            "monthly_savings":
            user.monthly_savings,

            "available_budget":
            user.available_budget
        }), 200

    try:

        monthly_income = float(
            data.get(
                "monthly_income",
                user.monthly_income
            )
        )

        monthly_savings = float(
            data.get(
                "monthly_savings",
                user.monthly_savings
            )
        )

    except (TypeError, ValueError):

        return jsonify({
            "message":
            "Income and savings must be numeric"
        }), 400

    if monthly_income < 0:
        return jsonify({
            "message":
            "Income cannot be negative"
        }), 400

    if monthly_savings < 0:
        return jsonify({
            "message":
            "Savings cannot be negative"
        }), 400

    if monthly_savings > monthly_income:
        return jsonify({
            "message":
            "Savings cannot be greater than income"
        }), 400

    available_budget = (
        monthly_income -
        monthly_savings
    )

    user.monthly_income = monthly_income
    user.monthly_savings = monthly_savings
    user.available_budget = available_budget

    budget = Budget.query.filter_by(
        user_id=user.id
    ).first()

    if budget:

        budget.monthly_budget = (
            available_budget
        )

    else:

        db.session.add(
            Budget(
                user_id=user.id,
                monthly_budget=available_budget
            )
        )

    db.session.commit()

    return jsonify({

        "message":
        "Financial data updated successfully",

        "monthly_income":
        user.monthly_income,

        "monthly_savings":
        user.monthly_savings,

        "available_budget":
        user.available_budget

    }), 200


@auth.route('/update-profile', methods=['PUT'])
@jwt_required()
def update_profile():

    current_user_id = int(
        get_jwt_identity()
    )

    user = db.session.get(
        User,
        current_user_id
    )

    if not user:
        return jsonify({
            "message": "User not found"
        }), 404

    data = request.get_json(
        silent=True
    ) or {}

    if 'name' in data:
        name = (data.get('name') or '').strip()
        if name:
            user.name = name

    if 'email' in data:
        email = (data.get('email') or '').strip().lower()
        if email:
            existing_user = User.query.filter_by(
                email=email
            ).first()
            if existing_user and existing_user.id != user.id:
                return jsonify({
                    "message": "Email already in use"
                }), 400
            user.email = email

    if 'phone' in data:
        phone = (data.get('phone') or '').strip()
        user.phone = phone

    db.session.commit()

    budget_data = Budget.query.filter_by(
        user_id=user.id
    ).first()
    monthly_budget = (
        budget_data.monthly_budget
        if budget_data
        else user.available_budget
    )

    return jsonify({
        "message": "Profile updated successfully",
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "monthly_income": user.monthly_income,
        "monthly_savings": user.monthly_savings,
        "available_budget": user.available_budget,
        "monthly_budget": monthly_budget,
    }), 200