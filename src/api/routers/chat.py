from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from src.agents import Retriver
from src.agents import rag_memory


load_dotenv()

rag_assistant = Retriver().rag_assistant()

router = APIRouter()

@router.get("/chat/{api_key}")
async def chat(message: str, api_key: str):

    if api_key != os.getenv("API_KEY"):
        return HTTPException(status_code=401, detail="Invalid API key")
    
    output = await rag_assistant.run(task=message)
    reponse = output.messages[-1].content

    await rag_memory.close()

    return JSONResponse(
        status_code=200, content=reponse
    )
