# wrapper for OpenAI API

# from autogen_ext.models.openai import OpenAIChatCompletionClient
# from autogen_agentchat.messages import UserMessage
from langchain_openai import ChatOpenAI
from app.core.config import settings

OPENAI_API_KEY = settings.OPENAI_API_KEY


async def generate_response(messages: list[dict]) -> str:
    """
    messages: list of dicts like [{"role": "user", "content": "hi"}, ...]
    """
    try:
        model_client = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=OPENAI_API_KEY,
        )

        # resp = await model_client.create([UserMessage(content=messages[-1].get("content", ""), source="user")])
        print(messages)
        print(type(messages))
        print(list(messages))
        resp = model_client.invoke(list(messages))

        return resp.content

    except Exception as e:
        return f"Error from LLM: {str(e)}"
