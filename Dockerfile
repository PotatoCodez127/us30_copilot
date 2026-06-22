# Use an official, clean, secure Python runtime as our stable container foundation
FROM python:3.11-slim

# Force strict UTC timezone mapping, prevent bytecode writes, and ensure unbuffered logs
ENV TZ=UTC \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Initialize the functional application execution root workspace
WORKDIR /app

# Install system dependencies necessary for compiling dense math and quantitative wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy python dependency records first to leverage aggressive Docker build caching
COPY requirements.txt .

# Upgrade pip and install locked package configurations directly into the layer space
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Mirror the application codebase into the active image container workspace
COPY . .

# Expose standard port allocations for the Flask research UI and telemetry streams
EXPOSE 5000 8080

# Default container action launches the 24/7 continuous live execution sniper bot
CMD ["python", "main_live.py"]