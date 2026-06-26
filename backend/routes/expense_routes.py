import threading
import os
import tempfile
import json
import re
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (jwt_required,get_jwt_identity)
from openai import OpenAI
from config import Config
from database.db import db
from services.category_alert_service import (
    check_category_alerts,
    mark_category_alert_sent,
)
from services.email_service import (
    send_category_alert,
    send_overspending_summary,
)
from models.expense_model import Expense
from services.backup_service import backup_expenses
from services.sms_parser import parse_expense_sms
from services.email_service import send_budget_alert
from models.category_budget_model import CategoryBudget
from services.ai_budget_engine import detect_overspending
from services.recurring_expense_service import process_due_recurring_expenses
from services.sms_service import send_sms
from models.user_model import User
expense = Blueprint(
    'expense',
    __name__
)

openai_client = OpenAI(api_key=Config.OPENAI_API_KEY) if Config.OPENAI_API_KEY else None

ALLOWED_EXPENSE_CATEGORIES = {
    "Food",
    "Travel",
    "Shopping",
    "Health",
    "Adventure",
    "Loan",
    "Bills",
    "Grocery",
}


def _normalize_payment_method(payment_method):
    payment_method = (payment_method or '').strip().lower()

    if payment_method in ["gpay", "google pay", "phonepe", "paytm", "upi"]:
        return "UPI"

    if payment_method in ["credit card", "debit card", "card"]:
        return "Card"

    if payment_method in ["net banking", "netbanking", "neft", "imps"]:
        return "Net Banking"

    if payment_method == "cash":
        return "Cash"

    return payment_method.title() if payment_method else ""


def _extract_voice_amount(transcript):
    lower = (transcript or '').lower().replace('-', ' ')

    number_matches = list(re.finditer(r"([0-9][0-9,]*(?:\.[0-9]{1,2})?)", lower))
    if number_matches:
        candidates = []
        currency_pattern = re.compile(r"(?:rs\.?|rupees?|rupee|inr|₹)")

        for match in number_matches:
            value = float(match.group(1).replace(',', ''))
            start, end = match.span()
            near_currency = (
                currency_pattern.search(lower[max(0, start - 12):start]) or
                currency_pattern.search(lower[end:end + 12])
            )
            candidates.append((value, bool(near_currency)))

        tagged = [value for value, near_currency in candidates if near_currency]
        return max(tagged or [value for value, _ in candidates])

    small_numbers = {
        "zero": 0,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
        "thirteen": 13,
        "fourteen": 14,
        "fifteen": 15,
        "sixteen": 16,
        "seventeen": 17,
        "eighteen": 18,
        "nineteen": 19,
        "ek": 1,
        "do": 2,
        "teen": 3,
        "char": 4,
        "chaar": 4,
        "panch": 5,
        "paanch": 5,
        "che": 6,
        "chhe": 6,
        "saat": 7,
        "aath": 8,
        "nau": 9,
        "das": 10,
        "gyarah": 11,
        "barah": 12,
    }
    tens = {
        "twenty": 20,
        "thirty": 30,
        "forty": 40,
        "fifty": 50,
        "sixty": 60,
        "seventy": 70,
        "eighty": 80,
        "ninety": 90,
        "bees": 20,
        "tees": 30,
        "chaalis": 40,
        "pachas": 50,
        "sath": 60,
        "saath": 60,
        "sattar": 70,
        "assi": 80,
        "nabbe": 90,
    }
    multipliers = {
        "hundred": 100,
        "sau": 100,
        "thousand": 1000,
        "hazar": 1000,
        "hazaar": 1000,
    }
    amount_markers = {
        "rupee",
        "rupees",
        "rs",
        "inr",
        "spent",
        "spend",
        "paid",
        "pay",
        "cost",
        "costing",
    }

    words = [
        re.sub(r"[^a-z]", "", word)
        for word in lower.split()
    ]
    words = [word for word in words if word]

    best_amount = 0
    current = 0
    total = 0
    found = False
    marker_seen = False

    for word in words:
        if word == "and" and found:
            continue

        if word in amount_markers:
            marker_seen = True
            if found and total + current > 0:
                break
            continue

        if word in small_numbers:
            current += small_numbers[word]
            found = True
            continue

        if word in tens:
            value = tens[word]
            current = (current * 100) + value if 0 < current < 10 else current + value
            found = True
            continue

        if word in multipliers:
            multiplier = multipliers[word]
            current = (current or 1) * multiplier
            if multiplier >= 1000:
                total += current
                current = 0
            found = True
            continue

        if found:
            if marker_seen or word in {"for", "on", "at", "by", "using", "with"}:
                continue
            best_amount = max(best_amount, total + current)
            current = 0
            total = 0
            found = False
            marker_seen = False

    if found:
        best_amount = max(best_amount, total + current)

    return float(best_amount)


def _transcribe_audio_file(audio_file):
    if not openai_client:
        raise RuntimeError("Voice transcription is not configured. OPENAI_API_KEY is missing.")

    if not audio_file:
        raise ValueError("Audio file is required")

    suffix = os.path.splitext(audio_file.filename or '')[1] or '.webm'
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name

        with open(temp_path, 'rb') as file_handle:
            transcription = openai_client.audio.transcriptions.create(
                model='whisper-1',
                file=file_handle,
                language='en'
            )

        transcript = (getattr(transcription, 'text', '') or '').strip()
        if not transcript:
            raise ValueError("Could not detect speech in the recording")

        return transcript

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def _fallback_parse_voice_expense(transcript):
    lower = transcript.lower()
    amount_match = re.search(
        r"(?:rs\.?|rupees?|inr)?\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)",
        lower
    )
    amount = (
        float(amount_match.group(1).replace(',', ''))
        if amount_match
        else _extract_voice_amount(transcript)
    )

    payment_method = ""
    if any(word in lower for word in ["upi", "gpay", "google pay", "phonepe", "phone pay", "paytm"]):
        payment_method = "UPI"
    elif any(word in lower for word in ["credit card", "debit card", "card"]):
        payment_method = "Card"
    elif any(word in lower for word in ["net banking", "netbanking", "neft", "imps"]):
        payment_method = "Net Banking"
    elif "cash" in lower:
        payment_method = "Cash"

    keyword_categories = {
        "Food": ["food", "lunch", "dinner", "breakfast", "snacks", "swiggy", "zomato", "restaurant", "coffee"],
        "Travel": ["petrol", "fuel", "uber", "ola", "cab", "taxi", "metro", "bus", "train", "parking"],
        "Shopping": ["shopping", "amazon", "flipkart", "myntra", "clothes", "shoes", "electronics"],
        "Health": ["medical", "pharmacy", "medicine", "hospital", "doctor", "clinic"],
        "Adventure": ["movie", "cinema", "netflix", "spotify", "game", "trip", "entertainment"],
        "Loan": ["emi", "loan", "installment", "instalment"],
        "Bills": ["bill", "electricity", "recharge", "broadband", "wifi", "mobile", "rent", "subscription"],
        "Grocery": ["grocery", "groceries", "vegetables", "milk", "fruit", "bread", "rice"],
    }
    category = "Shopping"
    for category_name, keywords in keyword_categories.items():
        if any(keyword in lower for keyword in keywords):
            category = category_name
            break

    title = re.sub(r"(?:rs\.?|rupees?|inr)?\s*[0-9][0-9,]*(?:\.[0-9]{1,2})?", " ", transcript, flags=re.I)
    title = re.sub(r"\b(i|paid|spend|spent|add|expense|for|on|at|using|with|by|via|through|rupees?|rs|inr|upi|gpay|google pay|phonepe|phone pay|paytm|card|cash)\b", " ", title, flags=re.I)
    title = re.sub(r"[^a-zA-Z0-9\s&-]", " ", title)
    title = re.sub(r"\s+", " ", title).strip()

    return {
        "title": title or f"{category} expense",
        "amount": amount,
        "category": category,
        "payment_method": payment_method,
    }


def _parse_voice_expense_with_ai(transcript):
    if not openai_client:
        return _fallback_parse_voice_expense(transcript)

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract one personal expense from the user's sentence. "
                        "Return only JSON with title, amount, category, payment_method. "
                        "category must be one of: Food, Travel, Shopping, Health, "
                        "Adventure, Loan, Bills, Grocery. amount must be a number. "
                        "payment_method may be UPI, Card, Net Banking, Cash, or empty."
                    )
                },
                {"role": "user", "content": transcript}
            ],
            temperature=0
        )
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
    except Exception as error:
        print("Voice AI parse failed, using fallback:", error)
        parsed = _fallback_parse_voice_expense(transcript)

    title = (parsed.get("title") or "").strip()
    category = (parsed.get("category") or "Shopping").strip().title()
    payment_method = _normalize_payment_method(parsed.get("payment_method"))

    try:
        amount = float(parsed.get("amount"))
    except (TypeError, ValueError):
        amount = 0

    if category not in ALLOWED_EXPENSE_CATEGORIES:
        category = "Shopping"

    return {
        "title": title or f"{category} expense",
        "amount": amount,
        "category": category,
        "payment_method": payment_method,
    }

def async_backup_expenses():
    app = current_app._get_current_object()
    def task():
        with app.app_context():
            backup_expenses()
    threading.Thread(target=task, daemon=True).start()
def get_total_spending(user_id):
    now = datetime.now()
    current_month_start = datetime(now.year, now.month, 1)

    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.created_at >= current_month_start
    ).all()
    total = 0
    for expense in expenses:
        total += expense.amount
    return total

def create_expense(user_id, title, amount, category, payment_method):
    new_expense = Expense(
        user_id=user_id,
        title=title,
        amount=amount,
        category=category,
        payment_method=payment_method
    )
    db.session.add(new_expense)
    db.session.commit()

    async_backup_expenses()

    return new_expense


BUDGET_ALERT_THRESHOLDS = [
    (100, "budget_alert_100_sent"),
    (90, "budget_alert_90_sent"),
    (75, "budget_alert_75_sent"),
    (50, "budget_alert_50_sent"),
]


def _build_budget_sms_text(threshold, spent, budget):
    remaining = max(round(budget - spent), 0)
    spent_amount = round(spent)
    budget_amount = round(budget)

    if threshold >= 100:
        exceeded_by = max(round(spent - budget), 0)
        return (
            "Budget Alert - 100% Used\n"
            f"Budget: Rs. {budget_amount}\n"
            f"Spent: Rs. {spent_amount}\n"
            f"Remaining: Rs. 0\n"
            f"Exceeded by: Rs. {exceeded_by}"
        )

    return (
        f"Budget Alert - {threshold}% Used\n"
        f"Budget: Rs. {budget_amount}\n"
        f"Spent: Rs. {spent_amount}\n"
        f"Remaining: Rs. {remaining}"
    )


def _mark_reached_budget_alerts_sent(user, threshold):
    for reached_threshold, flag_attr in BUDGET_ALERT_THRESHOLDS:
        if reached_threshold <= threshold:
            setattr(user, flag_attr, True)


def _budget_email_flag(flag_attr):
    return flag_attr.replace("_sent", "_email_sent")


def _budget_sms_flag(flag_attr):
    return flag_attr.replace("_sent", "_sms_sent")


def _email_alerts_enabled(user):
    return getattr(user, "email_alert_enabled", True) is not False


def _sms_alerts_enabled(user):
    return bool(getattr(user, "sms_alert_enabled", False))


def _send_overall_budget_alerts(user, total_spending):
    monthly_budget = float(user.available_budget or 0)
    if monthly_budget <= 0:
        return

    percentage = (total_spending / monthly_budget) * 100

    for threshold, flag_attr in BUDGET_ALERT_THRESHOLDS:
        if percentage < threshold:
            continue

        email_flag_attr = _budget_email_flag(flag_attr)
        sms_flag_attr = _budget_sms_flag(flag_attr)
        email_already_sent = bool(getattr(user, email_flag_attr))
        sms_already_sent = bool(getattr(user, sms_flag_attr))

        should_email = bool(
            user.email
            and _email_alerts_enabled(user)
            and not email_already_sent
        )
        should_sms = bool(
            user.phone
            and _sms_alerts_enabled(user)
            and not sms_already_sent
        )

        if not should_email and not should_sms:
            continue

        sent_any_channel = False

        if should_email:
            try:
                send_budget_alert(
                    user.email,
                    threshold,
                    total_spending,
                    monthly_budget
                )
                sent_any_channel = True
                setattr(user, email_flag_attr, True)
            except Exception as error:
                print("Budget email sending failed:", error)
        elif not user.email:
            print("Budget email skipped: user email is missing")
        elif not _email_alerts_enabled(user):
            print("Budget email skipped: email alerts are disabled")

        if should_sms:
            try:
                sms_sid = send_sms(
                    user.phone,
                    _build_budget_sms_text(
                        threshold,
                        total_spending,
                        monthly_budget
                    )
                )
                if sms_sid:
                    sent_any_channel = True
                    setattr(user, sms_flag_attr, True)
                else:
                    print("Budget SMS not marked sent because provider did not return SID.")
            except Exception as error:
                print("Budget SMS sending failed:", error)
        elif not user.phone:
            print("Budget SMS skipped: user phone is missing")
        elif not _sms_alerts_enabled(user):
            print("Budget SMS skipped: SMS alerts are disabled")

        if not sent_any_channel:
            print("Budget alert not marked sent because no channel delivered.")
            break

        _mark_reached_budget_alerts_sent(user, threshold)
        db.session.commit()
        break


# =========================================
# ADD EXPENSE
# =========================================
@expense.route('/add', methods=['POST'])
@jwt_required()
def add_expense():

    current_user_id = int(get_jwt_identity())

    data = request.get_json(silent=True) or {}

    title = (data.get('title') or '').strip()
    category = (data.get('category') or '').strip().title()

    payment_method = (
        (data.get('payment_method') or '')
        .strip()
        .lower()
    )

    if payment_method in [
        "gpay",
        "google pay",
        "phonepe",
        "paytm",
        "upi"
    ]:
        payment_method = "UPI"

    elif payment_method in [
        "credit card",
        "debit card",
        "card"
    ]:
        payment_method = "Card"

    elif payment_method in [
        "net banking",
        "netbanking",
        "neft",
        "imps"
    ]:
        payment_method = "Net Banking"

    # Validate amount
    try:

        amount = float(data.get('amount'))

    except (TypeError, ValueError):

        return jsonify({
            "message": "Amount must be a number"
        }), 400

    # Validate title/category
    if not title or not category:

        return jsonify({
            "message": "Title and category are required"
        }), 400

    # Validate amount > 0
    if amount <= 0:

        return jsonify({
            "message": "Amount must be greater than zero"
        }), 400

    # Create expense - this is the only part the user needs to wait on
    create_expense(
        current_user_id,
        title,
        amount,
        category,
        payment_method
    )

    total_spending = get_total_spending(
        current_user_id
    )
    overspending_alerts = detect_overspending(
        current_user_id
    )

    print("OVERSPENDING ALERTS =", overspending_alerts)

    # =========================================
    # NOTIFICATIONS (email, SMS, AI advice) run
    # in the background so the response returns
    # immediately instead of waiting on SMTP/Twilio/
    # OpenAI round-trips, which can each take seconds.
    # =========================================
    _run_expense_notifications_async(
        current_user_id,
        total_spending,
        overspending_alerts
    )

    return jsonify({
        "message": "Expense added successfully",
        "total_spending": total_spending,
        "overspending_alerts": overspending_alerts
    }), 201


@expense.route('/voice-transcribe', methods=['POST'])
@jwt_required()
def transcribe_voice_expense():
    audio_file = request.files.get('audio')

    try:
        transcript = _transcribe_audio_file(audio_file)
        return jsonify({
            "transcript": transcript
        }), 200

    except ValueError as error:
        return jsonify({
            "message": str(error)
        }), 400

    except RuntimeError as error:
        return jsonify({
            "message": str(error)
        }), 500

    except Exception as error:
        print("Voice transcription failed:", error)
        return jsonify({
            "message": "Voice transcription failed. Please try again."
        }), 500


@expense.route('/voice-add', methods=['POST'])
@jwt_required()
def add_voice_expense():
    current_user_id = int(get_jwt_identity())
    audio_file = request.files.get('audio')

    try:
        transcript = _transcribe_audio_file(audio_file)
        parsed = _parse_voice_expense_with_ai(transcript)

        title = (parsed.get("title") or "").strip()
        category = (parsed.get("category") or "").strip().title()
        payment_method = _normalize_payment_method(parsed.get("payment_method"))
        amount = float(parsed.get("amount") or 0)

        if not title or not category:
            return jsonify({
                "message": "Could not detect expense title or category from voice",
                "transcript": transcript
            }), 400

        if amount <= 0:
            return jsonify({
                "message": "Could not detect expense amount from voice",
                "transcript": transcript
            }), 400

        new_expense = create_expense(
            current_user_id,
            title,
            amount,
            category,
            payment_method
        )

        total_spending = get_total_spending(current_user_id)
        overspending_alerts = detect_overspending(current_user_id)
        _run_expense_notifications_async(
            current_user_id,
            total_spending,
            overspending_alerts
        )

        return jsonify({
            "message": "Voice expense added successfully",
            "transcript": transcript,
            "expense": {
                "id": new_expense.id,
                "title": new_expense.title,
                "amount": float(new_expense.amount),
                "category": new_expense.category,
                "payment_method": new_expense.payment_method,
            },
            "total_spending": total_spending,
            "overspending_alerts": overspending_alerts
        }), 201

    except ValueError as error:
        return jsonify({
            "message": str(error)
        }), 400

    except RuntimeError as error:
        return jsonify({
            "message": str(error)
        }), 500

    except Exception as error:
        print("Voice expense add failed:", error)
        return jsonify({
            "message": "Voice expense could not be added. Please try again."
        }), 500


def _run_expense_notifications_async(
    current_user_id,
    total_spending,
    overspending_alerts=None
):
    app = current_app._get_current_object()

    def task():
        with app.app_context():
            try:
                current_user = User.query.get(current_user_id)
                if not current_user:
                    return

                # Category-level alerts (email + SMS), includes AI advice
                print("CHECK_CATEGORY_ALERTS CALLED")
                alerts = check_category_alerts(current_user_id)
                print("CATEGORY ALERT RESULT =", alerts)

                # Only notify for thresholds that haven't already been
                # sent this month for that category - prevents the same
                # tier (e.g. 50%) from spamming an SMS/email on every
                # single expense added while spending stays in that band.
                new_alerts = [a for a in alerts if a.get("should_notify")]
                sent_category_email = False

                for alert in new_alerts:
                    try:
                        if alert.get("should_email"):
                            send_category_alert(
                                current_user.email,
                                alert["category"],
                                alert["percent"],
                                alert["type"],
                                alert.get("threshold"),
                                alert.get("spent"),
                                alert.get("budget"),
                                alert.get("remaining")
                            )
                            mark_category_alert_sent(
                                alert["budget_id"],
                                alert["email_flag_attr"]
                            )
                            sent_category_email = True
                        elif not current_user.email:
                            print("Category email skipped: user email is missing")
                    except Exception as error:
                        print("Category email sending failed:", error)

                    try:
                        if alert.get("should_sms"):
                            category = alert["category"]
                            budget_amount = round(alert["budget"])
                            spent_amount = round(alert["spent"])
                            remaining_amount = round(alert["remaining"])
                            ai_note = (alert.get("ai_recommendation") or "").strip()
                            ai_note_short = ai_note.split(".")[0].strip()
                            if ai_note_short and not ai_note_short.endswith("."):
                                ai_note_short += "."

                            if alert["percent"] >= 100:
                                extra_amount = round(alert["spent"] - alert["budget"])
                                sms_text = (
                                    f"{category} Budget Alert - {alert['threshold']}% Used\n"
                                    f"Budget: Rs. {budget_amount}\n"
                                    f"Spent: Rs. {spent_amount}\n"
                                    f"Remaining: Rs. 0\n"
                                    f"You have exceeded by Rs. {extra_amount}"
                                )
                            else:
                                sms_text = (
                                    f"{category} Budget Alert - {alert['threshold']}% Used\n"
                                    f"Budget: Rs. {budget_amount}\n"
                                    f"Spent: Rs. {spent_amount} ({alert['percent']}%)\n"
                                    f"Remaining: Rs. {remaining_amount}"
                                )

                            if ai_note_short:
                                sms_text += f"\nTip: {ai_note_short}"

                            sms_sid = send_sms(current_user.phone, sms_text)
                            if sms_sid:
                                mark_category_alert_sent(
                                    alert["budget_id"],
                                    alert["sms_flag_attr"]
                                )
                            else:
                                print(
                                    "Category SMS not marked sent because provider did not return SID:",
                                    alert["category"],
                                    alert["type"]
                                )
                        elif not current_user.phone:
                            print("Category SMS skipped: user phone is missing")
                    except Exception as error:
                        print("SMS sending failed:", error)

                if (
                    not sent_category_email
                    and current_user.email
                    and _email_alerts_enabled(current_user)
                    and overspending_alerts
                ):
                    try:
                        send_overspending_summary(
                            current_user.email,
                            overspending_alerts
                        )
                    except Exception as error:
                        print("Overspending summary email failed:", error)

                # Corrected sender above handled all new alerts. Keep the
                # older block below inactive to avoid duplicate messages.
                new_alerts = []

                for alert in new_alerts:
                    try:
                        send_category_alert(
                            current_user.email,
                            alert["category"],
                            alert["percent"],
                            alert["type"]
                        )
                    except Exception as error:
                        print("Category email sending failed:", error)

                if current_user.phone:
                    for alert in new_alerts:
                        try:
                            category = alert['category']
                            budget_amount = round(alert['budget'])
                            spent_amount = round(alert['spent'])
                            remaining_amount = round(alert['remaining'])
                            ai_note = (alert.get('ai_recommendation') or '').strip()
                            # Keep the AI note short for SMS - first sentence only
                            ai_note_short = ai_note.split('.')[0].strip()
                            if ai_note_short and not ai_note_short.endswith('.'):
                                ai_note_short += '.'

                            if alert['percent'] >= 100:
                                extra_amount = round(alert['spent'] - alert['budget'])
                                sms_text = (
                                    f"⚠ {category} Budget Alert\n"
                                    f"Budget: ₹{budget_amount}\n"
                                    f"Spent: ₹{spent_amount}\n"
                                    f"Remaining: ₹0\n"
                                    f"You have exceeded by ₹{extra_amount}"
                                )
                            else:
                                sms_text = (
                                    f"⚠ {category} Budget Alert\n"
                                    f"Budget: ₹{budget_amount}\n"
                                    f"Spent: ₹{spent_amount} ({alert['percent']}%)\n"
                                    f"Remaining: ₹{remaining_amount}"
                                )

                            if ai_note_short:
                                sms_text += f"\n💡 {ai_note_short}"

                            send_sms(current_user.phone, sms_text)
                        except Exception as error:
                            print("SMS sending failed:", error)

                # Overall monthly-budget alerts (email + SMS), one time per threshold.
                try:
                    _send_overall_budget_alerts(current_user, total_spending)
                except Exception as error:
                    print("Budget alert sending failed:", error)

            except Exception as error:
                print("Background notification task failed:", error)

    threading.Thread(target=task, daemon=True).start()
# =========================================
# GET ALL EXPENSES
# =========================================
@expense.route('/all', methods=['GET'])
@jwt_required()
def get_expenses():

    current_user_id = int(
        get_jwt_identity()
    )

    try:
        process_due_recurring_expenses(
            current_app._get_current_object(),
            current_user_id
        )
    except Exception as error:
        print("Recurring expense auto-check failed:", error)

    expenses = Expense.query.filter_by(
        user_id=current_user_id
    ).order_by(
        Expense.created_at.desc()
    ).all()

    expense_list = []

    for item in expenses:

        expense_list.append({

            "id": item.id,

            "title": item.title,

            "amount": float(item.amount),

            "category": item.category,

            "payment_method": item.payment_method,

            "created_at": (
                item.created_at.isoformat()
                if item.created_at
                else None
            )

        })

    return jsonify({
        "expenses": expense_list
    }), 200
# =========================================
# DELETE EXPENSE
# =========================================
@expense.route('/delete/<int:expense_id>', methods=['DELETE'])
@jwt_required()
def delete_expense(expense_id):

    current_user_id = int(
        get_jwt_identity()
    )

    expense_item = Expense.query.filter_by(

        id=expense_id,

        user_id=current_user_id

    ).first()

    if not expense_item:

        return jsonify({
            "message": "Expense not found"
        }), 404

    db.session.delete(
        expense_item
    )

    db.session.commit()

    async_backup_expenses()

    return jsonify({

        "message":
        "Expense deleted successfully"

    }), 200
# =========================================
# SMS PREVIEW
# =========================================
@expense.route('/sms/preview', methods=['POST'])
@jwt_required()
def preview_sms_expense():

    data = (
        request.get_json(
            silent=True
        ) or {}
    )

    sms_text = (
        data.get(
            'sms_text'
        ) or ''
    )

    parsed = parse_expense_sms(
        sms_text
    )

    status_code = (
        200
        if parsed.get(
            'is_expense'
        )
        else 400
    )

    response = {
        "parsed": parsed
    }

    if not parsed.get(
        'is_expense'
    ):

        response["message"] = (
            parsed.get(
                'error'
            )
            or
            "Could not parse SMS"
        )

    return jsonify(
        response
    ), status_code


# =========================================
# ADD EXPENSE FROM SMS
# =========================================
@expense.route('/sms/add', methods=['POST'])
@jwt_required()
def add_sms_expense():

    current_user_id = int(
        get_jwt_identity()
    )

    data = (
        request.get_json(
            silent=True
        ) or {}
    )

    sms_text = (
        data.get(
            'sms_text'
        ) or ''
    )

    parsed = parse_expense_sms(
        sms_text
    )

    if not parsed.get(
        'is_expense'
    ):

        return jsonify({
            "message":
            parsed.get(
                'error'
            )
            or
            "Could not parse SMS"
        }), 400

    title = (data.get('title') or '').strip()

    category = (
        (data.get('category') or '')
        .strip()
        .title()
    )

    payment_method = (
        (data.get('payment_method') or '')
        .strip()
        .lower()
    )

    if payment_method in [
        "gpay",
        "google pay",
        "phonepe",
        "paytm",
        "upi"
    ]:
        payment_method = "UPI"

    elif payment_method in [
        "credit card",
        "debit card",
        "card"
    ]:
        payment_method = "Card"

    elif payment_method in [
        "net banking",
        "netbanking",
        "neft",
        "imps"
    ]:
        payment_method = "Net Banking"

    try:

        amount = float(

            data.get('amount')

            or

            parsed.get('amount')

        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify({
            "message":
            "Parsed amount is invalid"
        }), 400

    if not title or not category:

        return jsonify({
            "message":
            "Parsed title and category are required"
        }), 400

    if amount <= 0:

        return jsonify({
            "message":
            "Parsed amount must be greater than zero"
        }), 400

    new_expense = create_expense(

        current_user_id,

        title,

        amount,

        category,

        payment_method

    )

    total_spending = get_total_spending(
        current_user_id
    )

    overspending_alerts = detect_overspending(current_user_id)

    _run_expense_notifications_async(
        current_user_id,
        total_spending,
        overspending_alerts
    )

    return jsonify({

        "message":
        "SMS expense added successfully",

        "expense": {

            "id":
            new_expense.id,

            "title":
            new_expense.title,

            "amount":
            float(
                new_expense.amount
            ),

            "category":
            new_expense.category,

            "payment_method":
            new_expense.payment_method

        },

        "total_spending":
        total_spending

    }), 201

# =========================================
# UPDATE EXPENSE
# =========================================
@expense.route('/update/<int:expense_id>', methods=['PUT'])
@jwt_required()
def update_expense(expense_id):

    current_user_id = int(
        get_jwt_identity()
    )

    expense_item = Expense.query.filter_by(
        id=expense_id,
        user_id=current_user_id
    ).first()

    if not expense_item:

        return jsonify({
            "message": "Expense not found"
        }), 404

    data = request.get_json(
        silent=True
    ) or {}

    title = (
        data.get('title') or ''
    ).strip()

    category = (
        data.get('category') or ''
    ).strip().title()

    payment_method = (
        data.get('payment_method') or ''
    ).strip()

    try:

        amount = float(
            data.get('amount')
        )

    except (TypeError, ValueError):

        return jsonify({
            "message": "Invalid amount"
        }), 400

    if not title:

        return jsonify({
            "message": "Title is required"
        }), 400

    if not category:

        return jsonify({
            "message": "Category is required"
        }), 400

    if amount <= 0:

        return jsonify({
            "message":
            "Amount must be greater than zero"
        }), 400

    expense_item.title = title
    expense_item.amount = amount
    expense_item.category = category
    expense_item.payment_method = payment_method

    db.session.commit()

    async_backup_expenses()

    return jsonify({
        "message":
        "Expense updated successfully"
    }), 200

@expense.route(
    '/latest',
    methods=['GET']
)
@jwt_required()
def latest_expenses():

    user_id = int(
        get_jwt_identity()
    )

    expenses = Expense.query.filter_by(
        user_id=user_id
    ).order_by(
        Expense.id.desc()
    ).limit(10).all()

    result = []

    for item in expenses:

        result.append({
            "id": item.id,
            "title": item.title,
            "amount": item.amount,
            "category": item.category,
            "payment_method": item.payment_method,
            "created_at": str(item.created_at)
            if item.created_at else None
        })

    return jsonify(result)

@expense.route(
    "/category-history",
    methods=["GET"]
)
@jwt_required()
def category_history():

    user_id = int(
        get_jwt_identity()
    )

    budgets = CategoryBudget.query.filter_by(
        user_id=user_id
    ).all()

    result = {}

    for budget in budgets:

        category_name = budget.category

        expenses = Expense.query.filter_by(
            user_id=user_id,
            category=category_name
        ).order_by(
            Expense.id.desc()
        ).limit(10).all()

        spent = 0

        expense_list = []

        for item in expenses:

            spent += float(item.amount)

            expense_list.append({

                "id":
                    item.id,

                "title":
                    item.title,

                "amount":
                    float(item.amount),

                "payment_method":
                    item.payment_method
            })

        budget_limit = float(
            budget.monthly_limit
        )

        percentage = 0

        if budget_limit > 0:

            percentage = round(
                (spent / budget_limit) * 100,
                2
            )

        status = "SAFE"

        if percentage >= 100:

            status = "EXCEEDED"

        elif percentage >= 80:

            status = "WARNING"

        result[
            category_name
        ] = {

            "budget":
                budget_limit,

            "spent":
                spent,

            "percentage":
                percentage,

            "status":
                status,

            "expenses":
                expense_list
        }

    return jsonify(result)

@expense.route(
    "/latest-by-category",
    methods=["GET"]
)
@jwt_required()
def latest_by_category():

    user_id = int(
        get_jwt_identity()
    )

    expenses = Expense.query.filter_by(
        user_id=user_id
    ).order_by(
        Expense.created_at.desc()
    ).limit(10).all()

    result = {}

    for expense in expenses:

        category = expense.category

        if category not in result:

            result[category] = []

        result[category].append({

            "title":
            expense.title,

            "amount":
            expense.amount,

            "date":
            expense.created_at.strftime(
                "%d-%m-%Y"
            )

        })

    return jsonify(result)
