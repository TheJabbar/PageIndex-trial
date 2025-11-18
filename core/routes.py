import uuid
import os
import json
from fastapi import UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from .config import settings
from .llm_engine import telkomllm_call
from memori import Memori
from pageindex import PageIndexClient
import pageindex.utils as pi_utils

# Initialize logging for the routes module
logger.info("Initializing PDF storage and memory components...")

# Initialize PageIndex client
pi_client = PageIndexClient(api_key=settings.PAGEINDEX_API_KEY)

# Global variables to store PDF metadata and PageIndex instances
pdf_storage = {}
doc_storage = {}  # Map pdf_id to doc_id for PageIndex

# Initialize Memori with database connection and memory features
logger.info("Initializing Memori with database connection...")
memori_client = Memori(
    database_connect=settings.DATABASE_URL,  # Using database from settings
    conscious_ingest=True,  # Short-term working memory
    auto_ingest=True,       # Dynamic search per query
)
logger.info("Memori initialized successfully")
memori_client.enable()
logger.info("Memori enabled")

class ChatRequest(BaseModel):
    message: str
    pdf_id: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: datetime

class UploadResponse(BaseModel):
    pdf_id: str
    filename: str
    status: str


async def upload_pdf(file: UploadFile = File(...)):
    """
    Endpoint to upload a PDF file for PageIndex processing
    """
    logger.info(f"Received upload request for file: {file.filename}")

    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        logger.warning(f"Invalid file type attempted: {file.filename}")
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Validate file size
    file_content = await file.read()
    if len(file_content) > settings.MAX_FILE_SIZE:
        logger.warning(f"File size too large: {len(file_content)} bytes for {file.filename}")
        raise HTTPException(status_code=400, detail="File size exceeds maximum allowed size")

    # Generate unique ID for this PDF
    pdf_id = str(uuid.uuid4())
    file_path = os.path.join(settings.PDF_STORAGE_PATH, f"{pdf_id}.pdf")
    logger.debug(f"Generated PDF ID: {pdf_id} for file: {file.filename}")

    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)
    logger.info(f"File saved to: {file_path}")

    # Process the PDF with PageIndex for vectorless RAG
    try:
        # Get your PageIndex API key from https://dash.pageindex.ai/api-keys
        logger.info(f"Processing PDF with PageIndex: {file.filename}")

        # Create PageIndex instance for this PDF
        doc_response = pi_client.submit_document(file_path)
        doc_id = doc_response["doc_id"]

        # Store the mapping between pdf_id and doc_id
        doc_storage[pdf_id] = doc_id

        # Also store PDF metadata in pdf_storage
        pdf_storage[pdf_id] = {
            "filename": file.filename,
            "file_path": file_path,
            "doc_id": doc_id,
            "upload_time": datetime.utcnow()
        }

        logger.success(f"PDF {file.filename} processed successfully with doc_id: {doc_id}")
        logger.info(f"Available PDFs in storage: {list(pdf_storage.keys())}")

        return UploadResponse(
            pdf_id=pdf_id,  # Return the actual pdf_id, not the file_path
            filename=file.filename,
            status="success"
        )
    except Exception as e:
        logger.error(f"Error processing PDF {file.filename}: {str(e)}")
        # Clean up if processing fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

async def chat_with_pdf(chat_request: ChatRequest):
    """
    Endpoint to chat with the uploaded PDF using RAG
    """
    logger.info(f"Chat request for PDF ID: {chat_request.pdf_id}, message: {chat_request.message[:50]}...")
    logger.info(f"Available PDFs: {list(pdf_storage.keys())}")

    # Validate PDF exists
    if chat_request.pdf_id not in pdf_storage:
        logger.error(f"PDF not found: {chat_request.pdf_id}")
        raise HTTPException(status_code=404, detail="PDF not found")

    # Get the doc_id for this PDF from storage
    pdf_info = pdf_storage[chat_request.pdf_id]
    doc_id = pdf_info["doc_id"]

    # Check if retrieval is ready
    if pi_client.is_retrieval_ready(doc_id):
        tree = pi_client.get_tree(doc_id, node_summary=True)['result']
        logger.debug('Simplified Tree Structure of the Document:')
        pi_utils.print_tree(tree)
    else:
        logger.error("Processing document, please try again later...")
        raise HTTPException(status_code=400, detail="Document is still processing, please try again later.")

    # Generate or use session ID
    session_id = chat_request.session_id or str(uuid.uuid4())
    logger.debug(f"Using session ID: {session_id}")

    # Use PageIndex to retrieve relevant content
    try:
        logger.info(f"Querying PageIndex for PDF {chat_request.pdf_id} with doc_id: {doc_id}")

        # Create a prompt for the LLM with retrieved context
        tree_without_text = pi_utils.remove_fields(tree.copy(), fields=['text'])
        search_prompt = f"""
        You are given a question and a tree structure of a document.
        Each node contains a node id, node title, and a corresponding summary.
        Your task is to find all nodes that are likely to contain the answer to the question.

        Question: {chat_request.message}

        Document tree structure:
        {json.dumps(tree_without_text, indent=2)}

        Please reply in the following JSON format:
        {{
            "thinking": "<Your thinking process on which nodes are relevant to the question>",
            "node_list": ["node_id_1", "node_id_2", ..., "node_id_n"]
        }}
        Directly return the final JSON structure. Do not output anything else.
        """
        tree_search_result  = await telkomllm_call(
            prompt=search_prompt,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE
        )
        # Retrieve PDF index
        node_map = pi_utils.create_node_mapping(tree)
        tree_search_result_json = json.loads(tree_search_result)
        print('Reasoning Process:')
        pi_utils.print_wrapped(tree_search_result_json['thinking'])

        print('\nRetrieved Nodes:')
        for node_id in tree_search_result_json["node_list"]:
            node = node_map[node_id]
            print(f"Node ID: {node['node_id']}\t Page: {node['page_index']}\t Title: {node['title']}")

        node_list = json.loads(tree_search_result)["node_list"]
        relevant_content = "\n\n".join(node_map[node_id]["text"] for node_id in node_list)

        print('Retrieved Context:\n')
        print(relevant_content[:1000] + '...')

        answer_prompt = f"""
        Answer the question based on the context:

        Question: {chat_request.message}
        Context: {relevant_content}

        Provide a clear, concise answer based only on the context provided.
        """

        print('Generated Answer:\n')
        answer = await telkomllm_call(answer_prompt, max_tokens=settings.LLM_MAX_TOKENS, temperature=settings.LLM_TEMPERATURE)
        pi_utils.print_wrapped(answer)

        # Handle potential errors from LLM call
        if isinstance(answer, dict) and "error" in answer:
            logger.error(f"LLM error: {answer['error']}")
            raise HTTPException(status_code=500, detail=answer["error"])

        logger.info("Chat response generated successfully")

        return ChatResponse(
            response=answer,
            session_id=session_id,
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Error processing chat query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


async def delete_pdf(pdf_id: str):
    """
    Endpoint to delete a PDF and its associated data
    """
    logger.info(f"Delete request for PDF ID: {pdf_id}")
    logger.debug(f"Current stored PDFs: {list(pdf_storage.keys())}")
    if pdf_id not in pdf_storage:
        logger.warning(f"Attempt to delete non-existent PDF: {pdf_id}")
        raise HTTPException(status_code=404, detail="PDF not found")

    # Remove file from storage
    file_path = pdf_storage[pdf_id]["file_path"]
    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"File removed: {file_path}")

    # Remove from storage dictionaries
    del pdf_storage[pdf_id]
    if pdf_id in doc_storage:
        del doc_storage[pdf_id]

    logger.success(f"PDF {pdf_id} deleted successfully")

    return {"message": f"PDF {pdf_id} deleted successfully"}