from openai import OpenAI
from config import Config

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