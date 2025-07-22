import os
import aiohttp
import tempfile
from openai import OpenAI, RateLimitError, APIError
from .models import Category

# The OpenAI client will automatically read the OPENAI_API_KEY environment variable.
# Ensure it is set in your environment, e.g., in docker-compose.yml.
api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

async def get_summary(text: str) -> str:
    if not client:
        return "(AI summary disabled: API key not configured)"
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
    if not client:
        return Category.UNCATEGORIZED
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
        print(f"An unexpected error occurred while categorizing: {e}")
        return Category.RISK # Default to risk on failure

async def transcribe_audio(audio_url: str) -> str:
    if not client:
        raise HTTPException(status_code=500, detail="Audio transcription is disabled: API key not configured")
    """
    Downloads audio from URL and transcribes it using OpenAI Whisper API.
    """
    try:
        # Download audio file
        async with aiohttp.ClientSession() as session:
            async with session.get(audio_url) as response:
                if response.status != 200:
                    print(f"Failed to download audio from {audio_url}")
                    return "(Audio transcription failed: Could not download file)"
                    return ""
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                    temp_file.write(await response.read())
                    temp_file_path = temp_file.name
        
        # Transcribe using OpenAI Whisper
        with open(temp_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        return transcript
        
    except (RateLimitError, APIError) as e:
        print(f"OpenAI API error during transcription: {e}")
        return ""
    except Exception as e:
        print(f"Error transcribing audio from {audio_url}: {e}")
        return ""

async def analyze_relevance(text: str) -> float:
    """
    Analyzes the relevance of content to AI and human rights topics.
    Returns a score between 0.0 and 1.0.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert in AI and human rights. Rate the relevance of the following text to AI and human rights topics on a scale of 0.0 to 1.0, where 1.0 is highly relevant and 0.0 is not relevant at all. Respond with only the numerical score."},
                {"role": "user", "content": text}
            ],
            max_tokens=10,
            temperature=0.0,
        )
        
        score_str = response.choices[0].message.content.strip()
        try:
            score = float(score_str)
            return max(0.0, min(1.0, score))  # Ensure score is between 0 and 1
        except ValueError:
            print(f"Invalid relevance score format: {score_str}")
            return 0.5  # Default to medium relevance
            
    except (RateLimitError, APIError) as e:
        print(f"OpenAI API error during relevance analysis: {e}")
        return 0.5
    except Exception as e:
        print(f"Error analyzing relevance: {e}")
        return 0.5 # Default to risk on failure
