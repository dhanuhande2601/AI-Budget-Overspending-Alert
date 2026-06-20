from openai import OpenAI
from config import Config
import time

client = OpenAI(
    api_key=Config.OPENAI_API_KEY
)

# In-memory cache for category advice to prevent slow page reloads.
# Entries expire after CACHE_TTL_SECONDS so advice refreshes periodically
# instead of staying stale forever.
_category_advice_cache = {}
CACHE_TTL_SECONDS = 60 * 60  # 1 hour


def get_ai_recommendation(
    category,
    spent,
    budget
):

    usage_percent = (
        round((spent / budget) * 100, 2)
        if budget > 0
        else 0
    )

    cache_key = (
        str(category).strip().title(),
        round(float(spent or 0), 2),
        round(float(budget or 0), 2)
    )

    cached_entry = _category_advice_cache.get(cache_key)
    if cached_entry:
        cached_value, cached_at = cached_entry
        if time.time() - cached_at <= CACHE_TTL_SECONDS:
            print("OPENAI CACHE HIT = Returning cached category AI recommendation")
            return cached_value

    prompt = f"""
You are an expert financial advisor.

Category: {category}
Budget: ₹{budget}
Spent: ₹{spent}
Usage: {usage_percent}%

Rules:
- Above 100% = HIGH RISK
- 80% to 100% = MEDIUM RISK
- Below 80% = LOW RISK
- Give practical advice
- Maximum 3 lines

Example:

Risk Level: HIGH
Suggestion: Reduce food delivery orders and cook at home more often.
"""

    try:

        print(
            "AI CALLED =",
            category,
            spent,
            budget
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )
        ai_text = response.choices[0].message.content.strip()

        print(
            "AI RESPONSE =",
            ai_text
        )

        _category_advice_cache[cache_key] = (ai_text, time.time())
        return ai_text

    except Exception as e:

        print(
            "OPENAI ERROR =",
            str(e)
        )

        fallback = ""
        if usage_percent >= 100:

            fallback = (
                "Risk Level: HIGH\n"
                f"Suggestion: Your {category} budget is exceeded. "
                "Reduce non-essential expenses immediately."
            )

        elif usage_percent >= 80:

            fallback = (
                "Risk Level: MEDIUM\n"
                f"Suggestion: You are close to your {category} budget limit. "
                "Spend carefully."
            )

        else:

            fallback = (
                "Risk Level: LOW\n"
                f"Suggestion: Spending in {category} is under control."
            )

        _category_advice_cache[cache_key] = (fallback, time.time())
        return fallback