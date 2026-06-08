import os
import json
from datetime import datetime
from models.user_model import User
from models.expense_model import Expense

BACKUP_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "backups")
)

def ensure_dir():
    os.makedirs(BACKUP_DIR, exist_ok=True)


# -------------------------
# USERS BACKUP (JSON)
# -------------------------
def backup_users():
    ensure_dir()

    users = User.query.all()

    data = [{
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "phone": u.phone,
        "monthly_budget": u.available_budget,
        "created_at": (
            u.created_at.strftime("%Y-%m-%d %H:%M:%S")
            if u.created_at
            else ""
        )
    } for u in users]

    backup_date = datetime.now().date()
    filename = f"{BACKUP_DIR}/users_{backup_date}.json"

    with open(filename, "w") as f:
        json.dump({
            "count": len(data),
            "users": data
        }, f, indent=4)

    table_filename = f"{BACKUP_DIR}/users_{backup_date}.txt"
    headers = ["ID", "Name", "Email", "Phone", "Budget", "Created"]
    rows = [
        [
            str(user["id"]),
            str(user["name"] or ""),
            str(user["email"] or ""),
            str(user["phone"] or ""),
            str(user["monthly_budget"] or 0),
            str(user["created_at"] or "")
        ]
        for user in data
    ]

    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        if rows
        else len(headers[index])
        for index in range(len(headers))
    ]

    def format_row(values):
        return "  ".join(
            value.ljust(widths[index])
            for index, value in enumerate(values)
        )

    with open(table_filename, "w") as f:
        f.write(format_row(headers) + "\n")
        f.write(format_row(["-" * width for width in widths]) + "\n")

        for row in rows:
            f.write(format_row(row) + "\n")


# -------------------------
# EXPENSES BACKUP (JSON)
# -------------------------
def backup_expenses():
    ensure_dir()

    expenses = Expense.query.all()

    data = [{
        "id": e.id,
        "user_id": e.user_id,
        "title": e.title,
        "amount": e.amount,
        "category": e.category,
        "payment_method": e.payment_method
    } for e in expenses]

    filename = f"{BACKUP_DIR}/expenses_{datetime.now().date()}.json"

    with open(filename, "w") as f:
        json.dump({
            "count": len(data),
            "expenses": data
        }, f, indent=4)
