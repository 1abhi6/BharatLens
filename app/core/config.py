# settings using pydantic BaseSettings

from pydantic import AnyUrl
from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = "chatbot"
    # Database: postgresql+asyncpg://user:pass@host:port/dbname
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day by default

    # OpenAI
    OPENAI_API_KEY: Optional[str]

    # Misc
    sqlalchemy_echo: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
