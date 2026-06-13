import requests

from datetime import datetime

from database.db import db
from models.festival_model import Festival


def sync_festivals():

    try:
        year = datetime.now().year

        url = (
            f"https://date.nager.at/api/v3/"
            f"PublicHolidays/{year}/IN"
        )

        response = requests.get(url, timeout=10)

        response = requests.get(url, timeout=10)

        print("Status Code:", response.status_code)

        if response.status_code == 204:
            print("No festival data available for", year)
            return

        if response.status_code != 200:
            print("Festival API Failed")
            return

        festivals = response.json()

        for item in festivals:

            festival_date = datetime.strptime(
                item["date"],
                "%Y-%m-%d"
            ).date()

            festival_name = item.get(
                "localName",
                item.get("name", "Unknown Festival")
            )

            existing = Festival.query.filter_by(
                name=festival_name
            ).first()

            if existing:

                existing.festival_date = festival_date

            else:

                festival = Festival(
                    name=festival_name,
                    festival_date=festival_date
                )

                db.session.add(festival)

        db.session.commit()

        print("Festival Sync Done")

    except Exception as e:

        import traceback

        traceback.print_exc()

        db.session.rollback()

        print("Festival API Failed:", str(e))