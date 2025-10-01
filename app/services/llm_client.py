# wrapper for OpenAI API

import openai
from app.core.config import settings

openai.api_key = settings.OPENAI_API_KEY


async def generate_response(messages: list[dict]) -> str:
    """
    messages: list of dicts like [{"role": "user", "content": "hi"}, ...]
    """
    try:
        resp = await openai.ChatCompletion.acreate(
            model="gpt-4o-mini",
            messages=messages,
        )
        return resp.choices[0].message["content"]
    except Exception as e:
        return f"Error from LLM: {str(e)}"
