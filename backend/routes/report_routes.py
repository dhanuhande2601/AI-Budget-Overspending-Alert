from io import BytesIO

from flask import Blueprint, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from models.expense_model import Expense
from models.user_model import User
from models.budget_model import Budget
from openpyxl import Workbook

report = Blueprint("report", __name__)


@report.route("/download", methods=["GET"])
@jwt_required()
def download_report():
    user_id = int(get_jwt_identity())

    user = User.query.get(user_id)
    if not user:
        return {"message": "User not found"}, 404

    budget_data = Budget.query.filter_by(user_id=user_id).first()
    budget_amount = budget_data.monthly_budget if budget_data else float(user.available_budget or 0)

    expenses = Expense.query.filter_by(user_id=user_id).all()
    total_spending = sum(expense.amount for expense in expenses)

    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    content = [
        Paragraph("AI Budget Overspending Report", styles["Title"]),
        Spacer(1, 20),
        Paragraph(f"Name: {user.name}", styles["Normal"]),
        Paragraph(f"Email: {user.email}", styles["Normal"]),
        Paragraph(f"Budget: Rs. {budget_amount}", styles["Normal"]),
        Paragraph(f"Total Spending: Rs. {total_spending}", styles["Normal"]),
    ]

    pdf.build(content)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="budget_report.pdf",
        mimetype="application/pdf"
    )

@report.route('/excel', methods=['GET'])
@jwt_required()
def download_excel():

    user_id = int(get_jwt_identity())

    expenses = Expense.query.filter_by(
        user_id=user_id
    ).all()

    workbook = Workbook()

    sheet = workbook.active

    sheet.title = "Expenses"

    headers = [
        "Title",
        "Amount",
        "Category",
        "Payment Method",
        "Created At"
    ]

    sheet.append(headers)

    for expense in expenses:

        sheet.append([
            expense.title,
            expense.amount,
            expense.category,
            expense.payment_method,
            str(expense.created_at)
        ])

    output = BytesIO()

    workbook.save(output)

    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name='expenses.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
