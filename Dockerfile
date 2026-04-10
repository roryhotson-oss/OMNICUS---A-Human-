# OMNICUS Ultimate - Production Dockerfile
FROM python:3.11-slim

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
 build-essential \
 curl \
 git 
 && rm -rf /var/lib/apt/lists/*

# Install audio dependencies for voice calls
RUN apt-get update && apt-get install -y --no-install-recommends \
 alsa-utils \
 libespeak1 \
 espeak 
 ffmpeg 
 && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
 pip install --no-cache-dir -r requirements.txt

# Install additional dependencies
RUN pip install --no-cache-dir \
 fastapi 
 uvicorn[standard] 
 python-telegram-bot 
 aiohttp 
 websockets 
 python-dotenv 
 pydantic 
 redis 
 psycopg2-binary

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data

# Expose ports
EXPOSE 8000 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 
 CMD curl -f http://localhost:8000/api/status || exit 1

# Default command
CMD ["python", "omnicus_master.py"]
