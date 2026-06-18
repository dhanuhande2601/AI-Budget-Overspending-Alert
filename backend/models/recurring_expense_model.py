from database.db import db
from datetime import datetime
import pytz
 
india_tz = pytz.timezone("Asia/Kolkata")
 
 
class RecurringExpense(db.Model):
    __tablename__ = "recurring_expenses"
 
    id = db.Column(db.Integer, primary_key=True)
 
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )
 
    title = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    payment_method = db.Column(db.String(100))
 
    # 'monthly', 'weekly', 'yearly'
    frequency = db.Column(db.String(20), nullable=False, default='monthly')
 
    # Day of month to charge (1-28, safe for all months)
    day_of_month = db.Column(db.Integer, nullable=False, default=1)
 
    is_active = db.Column(db.Boolean, default=True)

    # Optional - if set, the recurring expense auto-stops after this date
    # (e.g. EMI tenure ending, subscription contract ending)
    end_date = db.Column(db.Date, nullable=True)
 
    # Track when this was last auto-added, to avoid duplicates
    last_added_on = db.Column(db.Date, nullable=True)
 
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(india_tz)
    )