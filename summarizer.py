import os
import logging
from google import genai
from google.genai import types

def get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logging.error("GEMINI_API_KEY environment variable is missing.")
        return None
    return genai.Client(api_key=api_key)

def summarize_daily_news(articles):
    """
    Sends raw article data to Gemini to get a consolidated, formatted daily summary.
    """
    client = get_gemini_client()
    if not client:
        return "Error: Gemini API key not configured."

    # Prepare context
    context = "Here are the top news articles collected today from Chhattisgarh:\n\n"
    for idx, art in enumerate(articles, 1):
        context += f"Article {idx}: [Source: {art['source']}]\nTitle: {art['title']}\nContent Snippet: {art.get('content', '')[:1000]}\nURL: {art['url']}\n\n"

    system_instruction = """
You are an expert news analyst and executive assistant for an IAS officer in Chhattisgarh.
Your task is to analyze the provided news snippets and generate a daily briefing at 8 AM.

CRITICAL RULES:
1. You must read all the provided articles, which may be in Hindi, and output strictly in English.
2. Provide a clear, structured bullet-wise summary of EXACTLY 10 to 15 major points.
3. Categorize the news clearly into:
   - High Priority (Major decisions by High Court or Cabinet, major cases, significant state news).
   - Medium Priority (District collectors/SP news, administrative updates).
   - Low Priority (General state updates, infrastructure).
4. DO NOT INCLUDE ANY low-level news (e.g., petty crime, minor knife incidents, small-level crime). Ignore these completely.
5. Highlight 'Good News / Positives' (e.g., new inspirational launches, positive developments) in a dedicated section if available.
6. The summary MUST NOT be made up. Base it ONLY on the provided articles.
7. Include the source name briefly for context.

Make the output clean, professional, and easy to skim.
"""

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=context,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
            )
        )
        return response.text
    except Exception as e:
        logging.error(f"Error calling Gemini API: {e}")
        return f"Error generating summary: {e}"

def summarize_single_article(text):
    """Summarizes a single pasted article text."""
    client = get_gemini_client()
    if not client:
        return "Error: Gemini API key not configured."

    prompt = f"Please provide a concise, bulleted summary in English of the following article:\n\n{text}"
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
            )
        )
        return response.text
    except Exception as e:
        logging.error(f"Error calling Gemini API: {e}")
        return f"Error generating summary: {e}"
