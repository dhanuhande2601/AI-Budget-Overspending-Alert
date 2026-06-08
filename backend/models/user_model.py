from database.db import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)

    phone = db.Column(db.String(20))

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    monthly_income = db.Column(
        db.Float,
        default=0
    )

    monthly_savings = db.Column(
        db.Float,
        default=0
    )

    available_budget = db.Column(
        db.Float,
        default=0
    )
    budget_alert_50_sent = db.Column(
        db.Boolean,
        default=False
    )

    budget_alert_75_sent = db.Column(
        db.Boolean,
        default=False
    )

    budget_alert_90_sent = db.Column(
        db.Boolean,
        default=False
    )

    budget_alert_100_sent = db.Column(
        db.Boolean,
        default=False
    )
