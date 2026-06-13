from datetime import date

from models.festival_model import (
    Festival
)

def get_upcoming_festival():

    today = date.today()

    festivals = Festival.query.order_by(
        Festival.festival_date.asc()
    ).all()

    for festival in festivals:

        days_left = (
            festival.festival_date - today
        ).days

        if days_left >= 0:

            return {
                "name": festival.name,
                "festival_date": str(
                    festival.festival_date
                ),
                "days_left": days_left
            }

    return None