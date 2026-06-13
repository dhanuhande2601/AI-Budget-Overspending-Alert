from database.db import db


class BudgetNotification(db.Model):

    __tablename__ = "budget_notifications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    title = db.Column(
        db.String(255),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    notification_type = db.Column(
        db.String(50),
        default="IN_APP"
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )