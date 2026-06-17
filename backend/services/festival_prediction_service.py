from datetime import date

from models.festival_model import (
    Festival
)

def get_upcoming_festival():
    today = date.today()
    festivals = Festival.query.order_by(Festival.festival_date.asc()).all()

    for festival in festivals:
        days_left = (festival.festival_date - today).days

        if 0 <= days_left <= 5:        # ✅ Sirf 5 din ke andar wale dikhao
            return {
                "name": festival.name,
                "festival_date": str(festival.festival_date),
                "days_left": days_left,
                "alert": f"🎉 {festival.name} is in {days_left} days! Plan your budget accordingly."
            }

    return None