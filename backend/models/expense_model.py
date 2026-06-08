from database.db import db

class Expense(db.Model):

    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )

    title = db.Column(db.String(200), nullable=False)

    amount = db.Column(db.Float, nullable=False)

    category = db.Column(db.String(100), nullable=False)

    payment_method = db.Column(db.String(100))

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )