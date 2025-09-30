import asyncio
from autogen_ext.memory.chromadb import (
    ChromaDBVectorMemory,
    PersistentChromaDBVectorMemoryConfig,
    SentenceTransformerEmbeddingFunctionConfig,
)
import os
from pathlib import Path
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_ext.models.anthropic import AnthropicChatCompletionClient

# 1. Initialize Vector Database (ChromaDB)
vector_memory = ChromaDBVectorMemory(
    PersistentChromaDBVectorMemoryConfig(
        collection_name="user_preferences",
        persistence_path=os.path.join(str(Path.home()), ".chromadb_autogen"),
        k=3,  # Return top 3 results
        score_threshold=0.5,  # Minimum similarity score
        embedding_function_config=SentenceTransformerEmbeddingFunctionConfig(
            model_name="all-MiniLM-L6-v2"  # Use default model for testing
        ),
    ),  # directory for persistent storage
)

model_client = AnthropicChatCompletionClient(model="claude-sonnet-4-20250514")

# 2. Define Assistant Agent for Retrieval Augmented Generation (RAG)
assistant = AssistantAgent(name="WebRAGAssistant", memory=[vector_memory], model_client=model_client)


# 3. Extract Content from Webpage (replace with your URL)
async def fetch_and_store_content(url):
    import aiohttp
    from autogen_core.memory import MemoryContent, MemoryMimeType

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.text()
            # Optional: strip HTML tags here for plain text chunks
            chunk = content[:1500]  # simple chunking for demo
            await vector_memory.add(
                [
                    MemoryContent(
                        content=chunk,
                        mime_type=MemoryMimeType.TEXT,
                        metadata={"source": url},
                    )
                ]
            )


# 4. Index (Extract & Embed) Content
example_url = "https://en.wikipedia.org/wiki/Artificial_intelligence"
asyncio.run(fetch_and_store_content(example_url))

# 5. Search Workflow
query = "What is the history of artificial intelligence?"
search_results = asyncio.run(vector_memory.search(query, top_k=3))

print("Top Matching Chunks:")
for doc in search_results:
    print(doc["content"][:200], "...\n")  # print first 200 chars

# 6. (Optional) Use as part of agent chat: ask question with context from vector DB
user_proxy = UserProxyAgent(human_input_mode="NEVER")
response = asyncio.run(assistant.respond(query, memory=vector_memory))
print("Agent's RAG Answer:", response)
