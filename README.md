# PageIndex Memori Chatbot API

A powerful document chatbot API built with FastAPI, leveraging PageIndex for vectorless RAG (Retrieval-Augmented Generation) and Memori for memory management. This system allows users to upload PDF documents and engage in natural language conversations with their content.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Usage](#usage)
- [Environment Variables](#environment-variables)
- [Development](#development)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Overview

The PageIndex Memori Chatbot API enables natural language interactions with PDF documents using advanced RAG technology. It combines PageIndex's vectorless retrieval system with Telkom's AI LLM to provide accurate and context-aware responses to user queries about uploaded documents.

## Features

- **PDF Upload & Processing**: Upload PDF documents for intelligent processing and indexing
- **Vectorless RAG**: Uses PageIndex technology for document understanding without traditional vector embeddings
- **Natural Language Chat**: Engage in conversations with your documents using natural language
- **Session Management**: Maintain conversation context with session IDs
- **Document Metadata Storage**: Keeps track of uploaded documents and their processing status
- **Memory Management**: Uses Memori for conversation history and context
- **Asynchronous Processing**: Handles document processing and AI calls asynchronously
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## Architecture

The system consists of several key components:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │────│   FastAPI API    │────│   PageIndex     │
│   (Client)      │    │   (Backend)      │    │   (Retrieval)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                    ┌──────────────────┐
                    │   Memori         │
                    │   (Memory)       │
                    └──────────────────┘
                              │
                    ┌──────────────────┐
                    │   LLM Service    │
                    │   (Generation)   │
                    └──────────────────┘
```

### Key Components:

- **FastAPI**: Web framework providing RESTful API endpoints
- **PageIndex**: Vectorless RAG system for document processing and retrieval
- **Memori**: Memory management system for conversation context
- **Telkom LLM**: Large Language Model for response generation
- **Loguru**: Structured logging system
- **SQLAlchemy**: Database ORM for persistent storage

## Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager
- Access to PageIndex API (https://dash.pageindex.ai/api-keys)
- Access to Telkom AI LLM service

### Setup

1. Clone the repository:
```bash
git clone [repository-url]
cd pageindex-trial
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
# Or if using poetry:
poetry install
```

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# PageIndex Configuration
PAGEINDEX_API_KEY=your_pageindex_api_key_here

# LLM Configuration
URL_CUSTOM_LLM=https://your-llm-endpoint.com/api/v1/chat/completions
TOKEN_CUSTOM_LLM=your_llm_api_token_here

# Database Configuration
DATABASE_URL=sqlite:///./memori.db

# Application Configuration
APP_NAME=PageIndex RAG Chatbot
DEBUG=False
HOST=0.0.0.0
PORT=8000
PDF_STORAGE_PATH=./uploaded_pdfs
MAX_FILE_SIZE=10485760  # 10MB in bytes
LLM_MODEL_NAME=telkom-ai-instruct
LLM_TEMPERATURE=0
LLM_MAX_TOKENS=3000
MAX_HISTORY_LENGTH=10
```

### Configuration Options

- `APP_NAME`: Name of your application
- `DEBUG`: Enable/disable debug mode
- `HOST`: Host address for the API server
- `PORT`: Port number for the API server
- `PDF_STORAGE_PATH`: Directory to store uploaded PDFs
- `MAX_FILE_SIZE`: Maximum allowed PDF file size in bytes
- `LLM_TEMPERATURE`: Temperature setting for LLM responses (0-1)
- `LLM_MAX_TOKENS`: Maximum tokens for LLM responses
- `MAX_HISTORY_LENGTH`: Number of conversation turns to maintain in memory

## API Endpoints

### Upload PDF
- **Endpoint**: `POST /upload`
- **Description**: Upload a PDF document for processing
- **Request**: Multipart form data with PDF file
- **Response**: PDF ID and upload status

```bash
curl -X POST "http://localhost:8000/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

### Chat with PDF
- **Endpoint**: `POST /chat`
- **Description**: Chat with an uploaded PDF document
- **Request**: JSON with message, PDF ID, and optional session ID
- **Response**: AI-generated response and session information

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is this document about?",
    "pdf_id": "generated-uuid-here",
    "session_id": "optional-session-id"
  }'
```

### Delete PDF
- **Endpoint**: `DELETE /pdf/{pdf_id}`
- **Description**: Delete an uploaded PDF and its associated data
- **Request**: Path parameter with PDF ID
- **Response**: Deletion confirmation

```bash
curl -X DELETE "http://localhost:8000/pdf/{pdf_id}"
```

### Root Endpoint
- **Endpoint**: `GET /`
- **Description**: Health check and welcome message
- **Response**: Welcome message

```bash
curl -X GET "http://localhost:8000/"
```

## Usage

### Starting the Server

```bash
# Using uvicorn directly
uvicorn core.main:app --host 0.0.0.0 --port 8000 --reload

# Or run the main module
python -m core.main
```

### Basic Workflow

1. **Upload a PDF**: Send a POST request to `/upload` with your PDF file
2. **Wait for Processing**: The system will process the PDF using PageIndex
3. **Chat with Document**: Send messages to `/chat` with the PDF ID to get responses
4. **Manage Sessions**: Optionally provide session IDs to maintain conversation context
5. **Clean Up**: Delete PDFs when no longer needed using the delete endpoint

### Example Python Client

```python
import requests

# Upload PDF
with open('document.pdf', 'rb') as f:
    upload_response = requests.post(
        'http://localhost:8000/upload',
        files={'file': f}
    )
pdf_id = upload_response.json()['pdf_id']

# Chat with PDF
chat_response = requests.post(
    'http://localhost:8000/chat',
    json={
        'message': 'Summarize this document',
        'pdf_id': pdf_id
    }
)
print(chat_response.json()['response'])
```

## Development

### Project Structure

```
pageindex-trial/
├── core/                 # Core application modules
│   ├── __init__.py
│   ├── config.py         # Application configuration
│   ├── llm_engine.py     # LLM integration
│   ├── main.py          # FastAPI application
│   └── routes.py        # API route definitions
├── data/                # Data files
├── uploaded_pdfs/       # Storage for uploaded PDFs
├── .env                # Environment variables
├── .gitignore
├── README.md
├── requirements.txt      # Python dependencies
├── pyproject.toml       # Poetry configuration
└── uv.lock             # Dependency lock file
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=core
```

### Code Formatting

The project uses standard Python formatting. Run the following to format code:

```bash
# Using black
black .

# Using ruff
ruff check .
ruff format .
```

## Deployment

### Production Deployment

For production deployment, consider:

1. **Use a production ASGI server** like Gunicorn:
```bash
gunicorn core.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

2. **Set DEBUG=False** in production
3. **Use a proper database** instead of SQLite
4. **Configure logging** for production
5. **Implement proper authentication/authorization**
6. **Set up monitoring and alerting**

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "core.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### Common Issues

1. **PageIndex API Key Issues**:
   - Ensure your API key is correctly set in the environment
   - Check that you have access to the PageIndex service

2. **LLM Connection Issues**:
   - Verify the LLM endpoint URL and token are correct
   - Check network connectivity to the LLM service

3. **PDF Processing Failures**:
   - Ensure PDF files are not corrupted
   - Check that file sizes are within the allowed limit

4. **Memory Issues**:
   - Monitor memory usage during document processing
   - Consider increasing server resources for large documents

### Logging

The application uses Loguru for detailed logging. Check the logs to diagnose issues:

- Info logs: General application flow
- Debug logs: Detailed information (when DEBUG=True)
- Warning logs: Potential issues
- Error logs: Failed operations

### Performance Considerations

- Large PDF files will take longer to process
- Complex documents may require more LLM calls
- Consider implementing document size limits for better performance
- Monitor API usage limits for PageIndex and LLM services

## License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.

---

**Note**: This is a trial implementation. For production use, additional security measures, rate limiting, and comprehensive error handling should be implemented.