from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from chunker import rag_memory
from autogen_agentchat.ui import Console
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


# Create our RAG assistant agent
rag_assistant = AssistantAgent(
    name="rag_assistant",
    model_client=OpenAIChatCompletionClient(
        model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY")
    ),
    memory=[rag_memory],
)

# Ask questions about AutoGen
stream = rag_assistant.run_stream(task="What is AgentChat?")


async def main():
    await Console(stream)
    # Remember to close the memory when done
    await rag_memory.close()


if __name__ == "__main__":
    asyncio.run(main())
