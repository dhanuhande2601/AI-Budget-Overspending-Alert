"""
One-time migration script to add the new per-threshold alert tracking
columns to the EXISTING category_budgets table.

WHY THIS IS NEEDED: db.create_all() only creates tables that don't exist
yet - it does NOT add new columns to a table that's already there. Since
you already had a category_budgets table before this update, simply
restarting the server does nothing for that table, and every query
against CategoryBudget then fails with:

    OperationalError: table category_budgets has no column named alert_month

...which is almost certainly why Predicted month-end spending, Total
spending, Alerts, and Risk Score all stopped showing correctly - one
or more dashboard API calls were failing silently/with a 500 error.

USAGE:
    python migrate_category_alert_columns.py
"""

import sqlite3
import os
import re

# Read the actual configured DB path the same way config.py does, so
# this works regardless of where the .db file actually lives.
DB_PATH = None
try:
    from config import Config
    uri = Config.SQLALCHEMY_DATABASE_URI
    if uri.startswith("sqlite:///"):
        DB_PATH = uri.replace("sqlite:///", "", 1)
except Exception:
    pass

if not DB_PATH or not os.path.exists(DB_PATH):
    # Fall back to the common default location
    DB_PATH = os.path.join(os.path.dirname(__file__), "budget_alert.db")

if not os.path.exists(DB_PATH):
    print(f"Could not find the database file at: {DB_PATH}")
    print("Edit DB_PATH at the top of this script to point to your actual .db file, then re-run.")
    raise SystemExit(1)

print(f"Using database: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(category_budgets)")
existing_columns = {row[1] for row in cursor.fetchall()}
print("Existing columns:", existing_columns)

columns_to_add = {
    "alert_month": "INTEGER",
    "alert_year": "INTEGER",
    "alert_50_sent": "BOOLEAN DEFAULT FALSE",
    "alert_75_sent": "BOOLEAN DEFAULT FALSE",
    "alert_80_sent": "BOOLEAN DEFAULT FALSE",
    "alert_90_sent": "BOOLEAN DEFAULT FALSE",
    "alert_100_sent": "BOOLEAN DEFAULT FALSE",
}

added = []
for column, col_type in columns_to_add.items():
    if column not in existing_columns:
        cursor.execute(f"ALTER TABLE category_budgets ADD COLUMN {column} {col_type}")
        added.append(column)

conn.commit()
conn.close()

if added:
    print(f"Added columns: {added}")
else:
    print("All columns already present - nothing to do.")

print("Migration complete. Restart your backend server now.")
