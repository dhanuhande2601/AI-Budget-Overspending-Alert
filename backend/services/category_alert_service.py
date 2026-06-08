from models.category_budget_model import (
    CategoryBudget
)

from models.expense_model import (
    Expense
)

def check_category_alerts(
    user_id
):

    alerts = []

    budgets = CategoryBudget.query.filter_by(
        user_id=user_id
    ).all()

    for budget in budgets:

        expenses = Expense.query.filter_by(

            user_id=user_id,

            category=budget.category

        ).all()

        spent = sum(

            expense.amount

            for expense in expenses

        )

        if budget.monthly_limit <= 0:

            continue

        percent = (

            spent /
            budget.monthly_limit

        ) * 100

        if percent >= 100:

            alerts.append({

                "category":
                budget.category,

                "percent":
                percent,

                "type":
                "exceeded"

            })

        elif percent >= 80:

            alerts.append({

                "category":
                budget.category,

                "percent":
                percent,

                "type":
                "warning"

            })

    return alerts