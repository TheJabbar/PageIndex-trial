# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install --no-cache-dir uv

# Set UV environment variables
ENV UV_COMPILE_BYTECODE=true \
    UV_SYSTEM_PYTHON=true \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

COPY pyproject.toml uv.lock ./

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --compile-bytecode --no-install-project

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --compile-bytecode && \
    uv pip uninstall setuptools wheel pip --system

# Copy the rest of the application code
COPY . /app/

# Expose port 8000
EXPOSE 8000

# Create directories for PDF storage and database
RUN mkdir -p /app/uploaded_pdfs /app/data

# Set environment variables
ENV PYTHONPATH=/app

# Run the application using the virtual environment's uvicorn
CMD ["/app/.venv/bin/uvicorn", "core.main:app", "--host", "0.0.0.0", "--port", "8000"]