FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CHARON_DB_TYPE=sqlite \
    CHARON_DB_PATH=/app/data/charon.db

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libcap-dev \
    procps \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p data logs

# Initialize database
RUN python -m charon.scripts.init_config

# Expose the port
EXPOSE 5000

# Set default command
CMD ["python", "-m", "charon.src.web.server"] 