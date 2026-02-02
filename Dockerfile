# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set timezone to avoid timezone issues
ENV TZ=UTC

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY trading_bot_webhooking_v2.py .

# Set default webhook port (can be overridden)
ARG WEBHOOK_PORT=8001
ENV WEBHOOK_PORT=${WEBHOOK_PORT}

# Expose the webhook port (documentation only)
EXPOSE ${WEBHOOK_PORT}

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "trading_bot_webhooking_v2.py"]