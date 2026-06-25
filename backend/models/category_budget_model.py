# models/category_budget_model.py

from database.db import db


class CategoryBudget(db.Model):

    __tablename__ = "category_budgets"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    category = db.Column(
        db.String(100),
        nullable=False
    )

    monthly_limit = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    # Tracks which alert thresholds have already been sent THIS month,
    # so a category doesn't spam an alert every time any expense is
    # added while spending sits in the same 50/75/80/90/100+ band.
    alert_month = db.Column(db.Integer, nullable=True)
    alert_year = db.Column(db.Integer, nullable=True)
    alert_50_sent = db.Column(db.Boolean, default=False)
    alert_75_sent = db.Column(db.Boolean, default=False)
    alert_80_sent = db.Column(db.Boolean, default=False)
    alert_90_sent = db.Column(db.Boolean, default=False)
    alert_100_sent = db.Column(db.Boolean, default=False)
    alert_50_email_sent = db.Column(db.Boolean, default=False)
    alert_75_email_sent = db.Column(db.Boolean, default=False)
    alert_90_email_sent = db.Column(db.Boolean, default=False)
    alert_100_email_sent = db.Column(db.Boolean, default=False)
    alert_50_sms_sent = db.Column(db.Boolean, default=False)
    alert_75_sms_sent = db.Column(db.Boolean, default=False)
    alert_90_sms_sent = db.Column(db.Boolean, default=False)
    alert_100_sms_sent = db.Column(db.Boolean, default=False)

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category": self.category,
            "monthly_limit": self.monthly_limit
        }
