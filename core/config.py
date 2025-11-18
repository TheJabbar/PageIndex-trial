import os
from typing import Optional
from pydantic_settings import BaseSettings
from loguru import logger
from pageindex import PageIndexClient
import pageindex.utils as utils
from typing import ClassVar

class Config(BaseSettings):
    # FastAPI settings
    APP_NAME: str = "PageIndex RAG Chatbot"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # PDF storage settings
    PDF_STORAGE_PATH: str = "./uploaded_pdfs"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB in bytes
    ALLOWED_EXTENSIONS: set = {"pdf"}

    # Memory settings for chat history
    MAX_HISTORY_LENGTH: int = 10  # Number of conversation turns to keep
    MEMORY_BACKEND: str = "memory"  # Options: memory, redis

    # LLM settings (if you have specific LLM configurations)
    LLM_MODEL_NAME: str = "telkom-ai-instruct"  # Default model
    LLM_TEMPERATURE: float = 0
    LLM_MAX_TOKENS: int = 3000

    # PageIndex settings
    PAGEINDEX_CHUNK_SIZE: int = 1000  # Characters per chunk
    PAGEINDEX_OVERLAP_SIZE: int = 200  # Overlap between chunks
    PAGEINDEX_API_KEY: str = ""  # Your PageIndex API key
    
    # Environment variables from .env file
    URL_CUSTOM_LLM: str = ""
    TOKEN_CUSTOM_LLM: str = ""
    DATABASE_URL: str = "sqlite:///./memori.db"
    
    pass
    
    class Config:
        env_file = ".env"


# Create a global config instance
settings = Config()

# Log environment variables loaded
logger.info(f"Configuration loaded. App: {settings.APP_NAME}, Host: {settings.HOST}, Port: {settings.PORT}")
if settings.URL_CUSTOM_LLM:
    logger.info("URL_CUSTOM_LLM loaded from environment")
else:
    logger.warning("URL_CUSTOM_LLM not found in environment, using default")

if settings.TOKEN_CUSTOM_LLM:
    logger.info("TOKEN_CUSTOM_LLM loaded from environment")
else:
    logger.warning("TOKEN_CUSTOM_LLM not found in environment, using default")

if settings.PAGEINDEX_API_KEY:
    logger.info("PAGEINDEX_API_KEY loaded from environment")
else:
    logger.warning("PAGEINDEX_API_KEY not found in environment, using default")