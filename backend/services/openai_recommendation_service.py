from openai import OpenAI
from config import Config

client = OpenAI(
    api_key=Config.OPENAI_API_KEY
)


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

        response = client.responses.create(
            model="gpt-5-mini",
            input=prompt
        )

        ai_text = response.output_text.strip()

        print(
            "AI RESPONSE =",
            ai_text
        )

        return ai_text

    except Exception as e:

        print(
            "OPENAI ERROR =",
            str(e)
        )

        if usage_percent >= 100:

            return (
                "Risk Level: HIGH\n"
                f"Suggestion: Your {category} budget is exceeded. "
                "Reduce non-essential expenses immediately."
            )

        elif usage_percent >= 80:

            return (
                "Risk Level: MEDIUM\n"
                f"Suggestion: You are close to your {category} budget limit. "
                "Spend carefully."
            )

        return (
            "Risk Level: LOW\n"
            f"Suggestion: Spending in {category} is under control."
        )