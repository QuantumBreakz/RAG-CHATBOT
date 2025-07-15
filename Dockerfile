# Dockerfile for PITB RAG Chatbot (Backend)

# Use official Python base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_MODE=production  # Set to 'debug' to run Streamlit UI

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        git \
        libmagic1 \
        libgl1-mesa-glx \
        libglib2.0-0 \
        && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose FastAPI and Streamlit ports
EXPOSE 8000 8501

# Entrypoint: run FastAPI (production) or Streamlit (debug)
CMD if [ "$APP_MODE" = "debug" ]; then \
      streamlit run app.py --server.port=8501 --server.headless=true --server.enableCORS=false; \
    else \
      uvicorn backend.main:app --host 0.0.0.0 --port 8000; \
    fi 