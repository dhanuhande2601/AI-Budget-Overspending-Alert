import os
from datetime import timedelta

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from sqlalchemy import text
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
# from routes.user import user_bp
from config import Config
from database.db import db

# Models
from models.user_model import User
from models.expense_model import Expense
from models.budget_model import Budget
from models.category_budget_model import CategoryBudget

# Routes
from routes.auth_routes import auth
from routes.expense_routes import expense
from routes.ai_routes import ai
from routes.budget_routes import budget
from routes.report_routes import report
from routes.category_budget_routes import (
    category_budget
)
from routes.category_alert_routes import (
    category_alert
)
# Services
from extensions import mail

# Scheduler
from scheduler.job import start_scheduler


app = Flask(__name__)

# =========================================
# APP CONFIG
# =========================================

app.config['SECRET_KEY'] = Config.SECRET_KEY

app.config['JWT_SECRET_KEY'] = Config.SECRET_KEY

app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    Config.SQLALCHEMY_DATABASE_URI
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# =========================================
# EMAIL CONFIG
# =========================================

app.config['MAIL_SERVER'] = Config.MAIL_SERVER
app.config['MAIL_PORT'] = Config.MAIL_PORT
app.config['MAIL_USE_TLS'] = Config.MAIL_USE_TLS
app.config['MAIL_USERNAME'] = Config.MAIL_USERNAME
app.config['MAIL_PASSWORD'] = Config.MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = Config.MAIL_DEFAULT_SENDER
# =========================================
# EXTENSIONS
# =========================================

db.init_app(app)

mail.init_app(app)

jwt = JWTManager(app)

CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173"
            ],
            "methods": [
                "GET",
                "POST",
                "PUT",
                "PATCH",
                "DELETE",
                "OPTIONS"
            ],
            "allow_headers": [
                "Content-Type",
                "Authorization"
            ]
        }
    },
    supports_credentials=True
)

# =========================================
# BLUEPRINTS
# =========================================

app.register_blueprint(
    auth,
    url_prefix='/api/auth'
)

app.register_blueprint(
    expense,
    url_prefix='/api/expense'
)

app.register_blueprint(
    ai,
    url_prefix='/api/ai'
)

app.register_blueprint(
    budget,
    url_prefix='/api/budget'
)

app.register_blueprint(
    report,
    url_prefix='/api/report'
)

app.register_blueprint(
    category_budget,
    url_prefix='/api/category-budget'
)

app.register_blueprint(
    category_alert,
    url_prefix='/api/category-alert'
)
# app.register_blueprint(
#     user_bp,
#     url_prefix="/api/user"
# )

# =========================================
# HOME ROUTE
# =========================================

@app.route('/')
def home():

    return {
        'message':
        'AI Budget Overspending Alert Backend Running'
    }

# =========================================
# DATABASE INIT
# =========================================

def init_database():
    with app.app_context():
        db.create_all()
        ensure_user_alert_columns()
        ensure_category_budget_columns()

def ensure_category_budget_columns():

    columns = {
        row[1]
        for row in db.session.execute(
            text("PRAGMA table_info(category_budgets)")
        )
    }

    required_columns = {
        "created_at": "DATETIME",
        "monthly_limit": "FLOAT DEFAULT 0",
    }

    for column, datatype in required_columns.items():
        if column not in columns:
            db.session.execute(
                text(
                    f"ALTER TABLE category_budgets ADD COLUMN {column} {datatype}"
                )
            )

    db.session.commit()

def ensure_user_alert_columns():

    existing_columns = {
        row[1]
        for row in db.session.execute(
            text("PRAGMA table_info(users)")
        )
    }

    required_columns = {
        "monthly_income":
            "FLOAT DEFAULT 0",

        "monthly_savings":
            "FLOAT DEFAULT 0",

        "available_budget":
            "FLOAT DEFAULT 0",

        "budget_alert_50_sent":
            "BOOLEAN DEFAULT 0",

        "budget_alert_75_sent":
            "BOOLEAN DEFAULT 0",

        "budget_alert_90_sent":
            "BOOLEAN DEFAULT 0",

        "budget_alert_100_sent":
            "BOOLEAN DEFAULT 0",
    }

    for column, datatype in required_columns.items():

        if column not in existing_columns:

            db.session.execute(
                text(
                    f"ALTER TABLE users "
                    f"ADD COLUMN {column} {datatype}"
                )
            )

    db.session.commit()

@app.route("/test-email")
def test_email():

    from services.email_service import send_budget_alert

    send_budget_alert(
        "dhanuhande2601@gmail.com",
        50,
        10000,
        20000
    )

    return "Email Sent"

# =========================================
# RUN APP
# =========================================

if __name__ == '__main__':

    init_database()

    start_scheduler(app)

    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000
    )
