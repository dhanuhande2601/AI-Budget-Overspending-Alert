from database.db import db

class Budget(db.Model):

    __tablename__ = 'budgets'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        unique=True,
        nullable=False
    )

    monthly_budget = db.Column(
        db.Float,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=db.func.now(),
        server_default=db.func.now()
    )
