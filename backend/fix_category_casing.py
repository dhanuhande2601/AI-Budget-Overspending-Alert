"""
One-time cleanup script to fix inconsistent category casing in existing
data, caused by a bug where /expense/add used .title() but /expense/update
used .lower() — meaning "Shopping" and "shopping" were treated as two
different categories.

This script normalizes every Expense.category and CategoryBudget.category
to Title Case, then merges any duplicate CategoryBudget rows that resulted
from the bug (keeping the most recently created one).

USAGE:
    python fix_category_casing.py
"""

from app import app
from database.db import db
from models.expense_model import Expense
from models.category_budget_model import CategoryBudget


def normalize_expenses():
    expenses = Expense.query.all()
    fixed = 0
    for expense in expenses:
        normalized = (expense.category or '').strip().title()
        if expense.category != normalized:
            expense.category = normalized
            fixed += 1
    db.session.commit()
    print(f"Normalized {fixed} expense rows")


def normalize_and_merge_category_budgets():
    budgets = CategoryBudget.query.all()
    seen = {}  # normalized_category -> CategoryBudget row to keep

    for budget in budgets:
        normalized = (budget.category or '').strip().lower()

        if normalized not in seen:
            seen[normalized] = budget
            budget.category = normalized
        else:
            # Duplicate found (case-mismatch from the old bug) — keep
            # whichever has the higher monthly_limit set (likely the
            # one the user actually edited most recently/intentionally),
            # delete the other.
            kept = seen[normalized]
            if budget.monthly_limit > kept.monthly_limit:
                seen[normalized] = budget
                budget.category = normalized
                db.session.delete(kept)
            else:
                db.session.delete(budget)

    db.session.commit()
    print(f"Category budgets normalized — {len(seen)} unique categories remain")


def main():
    with app.app_context():
        print("Fixing category casing...")
        normalize_expenses()
        normalize_and_merge_category_budgets()
        print("Done! All categories are now consistently cased.")


if __name__ == "__main__":
    main()