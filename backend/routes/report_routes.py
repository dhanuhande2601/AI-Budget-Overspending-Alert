from io import BytesIO

from flask import Blueprint, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

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

    # Most recent expense first
    expenses = (
        Expense.query
        .filter_by(user_id=user_id)
        .order_by(Expense.created_at.desc())
        .all()
    )
    total_spending = sum(expense.amount for expense in expenses)

    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    content = [
        Paragraph("AI Budget Overspending Report", styles["Title"]),
        Spacer(1, 20),
        Paragraph(f"Name: {user.name}", styles["Normal"]),
        Paragraph(f"Email: {user.email}", styles["Normal"]),
        Paragraph(f"Budget: Rs. {budget_amount}", styles["Normal"]),
        Paragraph(f"Total Spending: Rs. {total_spending}", styles["Normal"]),
        Spacer(1, 20),
        Paragraph("Expense History", styles["Heading2"]),
        Spacer(1, 10),
    ]

    if expenses:
        table_data = [["Date", "Title", "Category", "Payment Method", "Amount (Rs.)"]]

        for expense in expenses:
            created = expense.created_at.strftime("%d-%m-%Y") if expense.created_at else "-"
            table_data.append([
                created,
                expense.title,
                expense.category,
                expense.payment_method or "-",
                f"{expense.amount:.2f}",
            ])

        history_table = Table(table_data, repeatRows=1)
        history_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
            ("ALIGN", (4, 0), (4, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))

        content.append(history_table)
    else:
        content.append(Paragraph("No expenses recorded yet.", styles["Normal"]))

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