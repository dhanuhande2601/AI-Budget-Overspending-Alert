from openai import OpenAI
from config import Config
import json

client = OpenAI(api_key=Config.OPENAI_API_KEY)

def generate_ai_recommendation(
    monthly_budget,
    total_spending,
    predicted_spending,
    daily_budget,
    remaining_budget,
    category_summary,
    festival=None
):
    try:
        prompt = f"""
You are a personal finance advisor.

Monthly Budget: ₹{monthly_budget}
Current Spending: ₹{total_spending}
Predicted Month End Spending: ₹{predicted_spending}
Daily Budget: ₹{daily_budget}
Remaining Budget: ₹{remaining_budget}

Category Spending:
{category_summary}

Upcoming Festival:
{festival}

Give short practical advice in 3-4 lines.
Focus on:
1. Daily spending control
2. Category budgets
3. Month-end forecast
4. Festival planning if applicable

Return plain text only.
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a smart budget advisor."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=150
        )

        return response.choices[0].message.content

    except Exception as e:
        print("OpenAI Error:", e)

        return (
            f"You have spent ₹{total_spending:.0f} out of "
            f"₹{monthly_budget:.0f}. "
            f"Try to keep daily expenses within ₹{daily_budget:.0f}."
        )


def generate_investment_suggestion(
    monthly_income,
    monthly_budget,
    total_spending,
    remaining_budget,
    risk_level,
):
    """
    Suggests a rough investable amount range and 2-3 generic, low-risk
    investment categories (not specific stocks/funds) based on what's
    left over after budgeted spending. Framed as general informational
    suggestions, not personalized financial advice.
    """
    try:
        prompt = f"""
You are a cautious personal finance assistant. Based on this user's
numbers, suggest a rough monthly investable amount and 2-3 generic
investment categories suited to their risk level.

Monthly Income: ₹{monthly_income}
Monthly Budget: ₹{monthly_budget}
Current Spending: ₹{total_spending}
Remaining Budget This Month: ₹{remaining_budget}
Financial Risk Level: {risk_level}

Rules:
- Only suggest a SMALL portion of remaining budget as investable, never
  money needed for upcoming bills or the rest of the month's spending.
- If risk level is HIGH or remaining budget is very low, the investable
  amount should be small or zero, and say so.
- Only suggest broad, low-risk categories: SIP in index fund, short-term
  FD, liquid mutual fund, recurring deposit, emergency fund. Never name
  specific stocks, schemes, or companies.
- This is general informational content, not personalized financial advice.

Return ONLY valid JSON, no markdown, no commentary, in this exact shape:
{{
  "min_amount": <number>,
  "max_amount": <number>,
  "suggestions": ["<category 1>", "<category 2>", "<category 3>"]
}}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a cautious financial assistant that only returns valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=200
        )

        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)

        return {
            "min_amount": round(float(parsed.get("min_amount", 0)), 2),
            "max_amount": round(float(parsed.get("max_amount", 0)), 2),
            "suggestions": parsed.get("suggestions", [])[:3],
        }

    except Exception as e:
        print("OpenAI investment suggestion error:", e)

        # Safe fallback: a conservative 10% of whatever's left, no AI needed
        fallback_amount = max(remaining_budget * 0.1, 0)
        return {
            "min_amount": round(fallback_amount * 0.5, 2),
            "max_amount": round(fallback_amount, 2),
            "suggestions": ["Short-term FD", "Liquid mutual fund"],
        }