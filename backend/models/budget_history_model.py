from database.db import db
from datetime import datetime
 
class BudgetHistory(db.Model):
    __tablename__ = 'budget_history'
 
    id = db.Column(db.Integer, primary_key=True)
 
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False
    )
 
    month = db.Column(db.Integer, nullable=False)   # 1-12
    year = db.Column(db.Integer, nullable=False)    # e.g. 2025
 
    monthly_budget = db.Column(db.Float, default=0)
    total_spent = db.Column(db.Float, default=0)
    total_saved = db.Column(db.Float, default=0)
    overspent = db.Column(db.Boolean, default=False)
    top_category = db.Column(db.String(100), nullable=True)
 
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
 
    __table_args__ = (
        db.UniqueConstraint('user_id', 'month', 'year', name='unique_user_month_year'),
    )
 