import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

# Use async client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def analyze_image_vision_fn(image_url: str) -> str:
    """
    Analyze image using GPT-4o Vision asynchronously.
    Returns a short description and any detected text.
    """
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are an assistant that describes images and extracts any visible text.",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Describe this image briefly. If there is any text, extract it.",
                    },
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ],
    )
    return response.choices[0].message.content
