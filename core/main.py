from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
from loguru import logger

from .config import settings
from .routes import upload_pdf, chat_with_pdf, delete_pdf, ChatRequest, ChatResponse, UploadResponse

# Initialize FastAPI app
logger.info(f"Initializing FastAPI app: {settings.APP_NAME}")
app = FastAPI(title=settings.APP_NAME)

# Ensure PDF storage directory exists
os.makedirs(settings.PDF_STORAGE_PATH, exist_ok=True)
logger.info(f"PDF storage directory ensured: {settings.PDF_STORAGE_PATH}")


@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": f"Welcome to {settings.APP_NAME}"}


@app.post("/upload", response_model=UploadResponse)
async def upload_pdf_endpoint(file: UploadFile = File(...)):
    """
    Endpoint to upload a PDF file for RAG processing
    """
    logger.info(f"Upload endpoint accessed for file: {file.filename}")
    response = await upload_pdf(file=file)
    logger.success(f"File {file.filename} uploaded successfully with ID {response.pdf_id}")
    return response


@app.post("/chat", response_model=ChatResponse)
async def chat_with_pdf_endpoint(chat_request: ChatRequest):
    """
    Endpoint to chat with the uploaded PDF using RAG
    """
    logger.info(f"Chat endpoint accessed for PDF ID: {chat_request.pdf_id}")
    response = await chat_with_pdf(chat_request=chat_request)
    logger.debug(f"Chat response generated for session: {response.session_id}")
    return response


@app.delete("/pdf/{pdf_id}")
async def delete_pdf_endpoint(pdf_id: str):
    """
    Endpoint to delete a PDF and its associated data
    """
    logger.info(f"Delete endpoint accessed for PDF ID: {pdf_id}")
    response = await delete_pdf(pdf_id=pdf_id)
    logger.info(f"PDF ID {pdf_id} deleted successfully")
    return response


if __name__ == "__main__":
    import uvicorn
    from .config import settings
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )