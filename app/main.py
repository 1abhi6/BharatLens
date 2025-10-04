from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.api.v1 import auth, users, chat, multimodal
from app.db.session import get_async_session

app = FastAPI(title="Chatbot API")


# Allow frontend origins
origins = [
    "http://localhost:8080",  # local React dev
    "https://bharatlens.onrender.com/",  # deployed frontend
]

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # list of allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # allow all HTTP methods
    allow_headers=["*"],  # allow all headers
)

# Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(multimodal.router, prefix="/api/v1")


@app.get("/")
async def health_check(db: AsyncSession = Depends(get_async_session)):
    try:
        result = await db.execute(text("SELECT 1"))
        db_status = "connected" if result.scalar() == 1 else "not connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    return {"status": "ok", "database": db_status}
