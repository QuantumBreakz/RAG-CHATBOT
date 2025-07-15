# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install system dependencies for OCR and PDF processing
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose backend port
EXPOSE 8000

# Default command
CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"] 