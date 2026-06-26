from openai import OpenAI
from config import Config
import json
import os
import time

client = OpenAI(api_key=Config.OPENAI_API_KEY)

# In-memory caches for OpenAI calls to optimize page loading speed.
# Each entry stores (value, timestamp); entries older than CACHE_TTL_SECONDS
# are treated as expired and regenerated, so advice doesn't go stale forever.
_recommendation_cache = {}
_investment_cache = {}
_coach_cache = {}
CACHE_TTL_SECONDS = 60 * 60  # 1 hour


def _get_cached(cache, key):
    entry = cache.get(key)
    if not entry:
        return None
    value, cached_at = entry
    if time.time() - cached_at > CACHE_TTL_SECONDS:
        return None  # expired
    return value


def _set_cached(cache, key, value):
    cache[key] = (value, time.time())


def _fast_ai_mode():
    return os.getenv("FAST_AI_MODE", "true").lower() != "false"


def _basic_recommendation(
    monthly_budget,
    total_spending,
    predicted_spending,
    daily_budget,
    remaining_budget,
):
    if monthly_budget <= 0:
        return "Set a monthly budget first so the app can guide your spending."

    usage = (total_spending / monthly_budget) * 100
    if predicted_spending > monthly_budget:
        return (
            f"You may cross your budget by month end. Keep daily spending near "
            f"Rs. {max(daily_budget, 0):.0f} and pause non-essential purchases."
        )

    if usage >= 80:
        return (
            f"You have used {usage:.0f}% of your budget. Spend carefully and "
            f"protect the remaining Rs. {max(remaining_budget, 0):.0f}."
        )

    return (
        f"Your spending is under control. Keep daily expenses around "
        f"Rs. {max(daily_budget, 0):.0f} to stay on track."
    )


def generate_ai_recommendation(
    monthly_budget,
    total_spending,
    predicted_spending,
    daily_budget,
    remaining_budget,
    category_summary,
    festival=None
):
    # Construct a cache key based on query metrics
    summary_key = None
    if isinstance(category_summary, list):
        summary_key = tuple(sorted((item.get('category', ''), float(item.get('amount', 0))) for item in category_summary))
    else:
        summary_key = str(category_summary)

    cache_key = (
        round(float(monthly_budget or 0), 2),
        round(float(total_spending or 0), 2),
        round(float(predicted_spending or 0), 2),
        round(float(daily_budget or 0), 2),
        round(float(remaining_budget or 0), 2),
        summary_key,
        str(festival)
    )

    cached = _get_cached(_recommendation_cache, cache_key)
    if cached is not None:
        print("OPENAI CACHE HIT = Returning cached AI recommendation")
        return cached

    if _fast_ai_mode():
        advice = _basic_recommendation(
            float(monthly_budget or 0),
            float(total_spending or 0),
            float(predicted_spending or 0),
            float(daily_budget or 0),
            float(remaining_budget or 0),
        )
        _set_cached(_recommendation_cache, cache_key, advice)
        return advice

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

        advice = response.choices[0].message.content
        _set_cached(_recommendation_cache, cache_key, advice)
        return advice

    except Exception as e:
        print("OpenAI Error:", e)

        fallback = (
            f"You have spent Rs. {total_spending:.0f} out of "
            f"Rs. {monthly_budget:.0f}. "
            f"Try to keep daily expenses within Rs. {daily_budget:.0f}."
        )
        _set_cached(_recommendation_cache, cache_key, fallback)
        return fallback


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
    cache_key = (
        round(float(monthly_income or 0), 2),
        round(float(monthly_budget or 0), 2),
        round(float(total_spending or 0), 2),
        round(float(remaining_budget or 0), 2),
        str(risk_level)
    )

    cached = _get_cached(_investment_cache, cache_key)
    if cached is not None:
        print("OPENAI CACHE HIT = Returning cached investment suggestion")
        return cached

    fallback_amount = max(float(remaining_budget or 0) * 0.1, 0)
    fallback = {
        "min_amount": round(fallback_amount * 0.5, 2),
        "max_amount": round(fallback_amount, 2),
        "suggestions": ["Short-term FD", "Liquid mutual fund"],
    }

    if _fast_ai_mode():
        _set_cached(_investment_cache, cache_key, fallback)
        return fallback

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

        result = {
            "min_amount": round(float(parsed.get("min_amount", 0)), 2),
            "max_amount": round(float(parsed.get("max_amount", 0)), 2),
            "suggestions": parsed.get("suggestions", [])[:3],
        }
        _set_cached(_investment_cache, cache_key, result)
        return result

    except Exception as e:
        print("OpenAI investment suggestion error:", e)

        _set_cached(_investment_cache, cache_key, fallback)
        return fallback


def generate_ai_coach(
    total_spending,
    monthly_budget,
    predicted_spending,
    remaining_budget,
    category_summary,
    risk_level,
):
    cache_key = (
        round(float(total_spending or 0), 2),
        round(float(monthly_budget or 0), 2),
        round(float(predicted_spending or 0), 2),
        round(float(remaining_budget or 0), 2),
        str(risk_level),
        tuple(sorted((str(k), round(float(v or 0), 2)) for k, v in category_summary.items())),
    )

    cached = _get_cached(_coach_cache, cache_key)
    if cached is not None:
        return cached

    top_category = None
    if category_summary:
        top_category = max(category_summary, key=category_summary.get)

    if monthly_budget > 0:
        usage = (total_spending / monthly_budget) * 100
    else:
        usage = 0

    fallback = {
        "habit": (
            f"{top_category} is your highest spending area."
            if top_category else "Start adding expenses daily to reveal patterns."
        ),
        "today_challenge": "Keep today's optional spending under control.",
        "smart_move": (
            "Pause big purchases until your budget is back on track."
            if usage >= 80 else "Move a small amount to savings before spending."
        ),
        "daily_goal": (
            f"Stay below Rs. {max(remaining_budget / 7, 0):.0f} today."
            if remaining_budget > 0 else "Avoid new optional spending today."
        ),
        "main_problem": (
            "Projected spending is above budget."
            if predicted_spending > monthly_budget and monthly_budget > 0
            else "Budget looks manageable; consistency is the key."
        ),
    }

    if _fast_ai_mode():
        _set_cached(_coach_cache, cache_key, fallback)
        return fallback

    try:
        prompt = f"""
You are an AI personal finance coach for a budget tracking app.

Monthly Budget: Rs. {monthly_budget}
Spent This Month: Rs. {total_spending}
Predicted Month-End Spending: Rs. {predicted_spending}
Remaining Budget: Rs. {remaining_budget}
Risk Level: {risk_level}
Category Spending: {category_summary}

Return ONLY valid JSON, no markdown, in this exact shape:
{{
  "habit": "<one short spending habit detected>",
  "today_challenge": "<one realistic challenge for today>",
  "smart_move": "<one practical action>",
  "daily_goal": "<one daily limit or behavior goal>",
  "main_problem": "<one biggest issue to fix>"
}}

Rules:
- Keep each value under 18 words.
- Use the exact numbers when useful.
- Do not invent expenses, salaries, debts, or investment returns.
- Tone should be motivational and Hinglish-friendly, but professional.
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a concise personal finance coach that returns valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=220,
            temperature=0.6,
        )

        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)
        result = {
            "habit": str(parsed.get("habit", ""))[:180],
            "today_challenge": str(parsed.get("today_challenge", ""))[:180],
            "smart_move": str(parsed.get("smart_move", ""))[:180],
            "daily_goal": str(parsed.get("daily_goal", ""))[:180],
            "main_problem": str(parsed.get("main_problem", ""))[:180],
        }
        _set_cached(_coach_cache, cache_key, result)
        return result

    except Exception as e:
        print("OpenAI coach error:", e)

        _set_cached(_coach_cache, cache_key, fallback)
        return fallback
