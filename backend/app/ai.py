import os
from openai import OpenAI, RateLimitError, APIError
from .models import Category

# The OpenAI client will automatically read the OPENAI_API_KEY environment variable.
# Ensure it is set in your environment, e.g., in docker-compose.yml.
client = OpenAI(api_key=os.environ.get("HUMAN_RIGHTS_AI_MONITOR_OAI_KEY"))

async def get_summary(text: str) -> str:
    """
    Generates a summary for the given text using the OpenAI API.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes articles about AI and human rights. Summarize the following text in 1-2 sentences."},
                {"role": "user", "content": text}
            ],
            max_tokens=150,
            temperature=0.3,
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except (RateLimitError, APIError) as e:
        print(f"OpenAI API error generating summary: {e}")
        return "(AI summary failed due to API error.)"
    except Exception as e:
        # Catching other potential exceptions, e.g., network issues
        print(f"An unexpected error occurred while generating summary: {e}")
        return "(AI summary failed.)"

async def get_category(text: str) -> Category:
    """
    Categorizes the given text as Risk-focused or Opportunity-focused using the OpenAI API.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are an expert in AI and human rights. Your task is to categorize the following article as either '{Category.RISK.value}' or '{Category.OPPORTUNITY.value}'. Respond with only one of these two options."},
                {"role": "user", "content": text}
            ],
            max_tokens=10,
            temperature=0.0,
        )
        category_str = response.choices[0].message.content.strip()
        if category_str == Category.OPPORTUNITY.value:
            return Category.OPPORTUNITY
        return Category.RISK
    except (RateLimitError, APIError) as e:
        print(f"OpenAI API error getting category: {e}")
        return Category.RISK # Default to risk on failure
    except Exception as e:
        print(f"An unexpected error occurred while getting category: {e}")
        return Category.RISK # Default to risk on failure
