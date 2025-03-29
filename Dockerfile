FROM python:3.9-slim

# Install necessary system dependencies
RUN apt-get update && apt-get install -y \
    g++ \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories and set permissions
RUN mkdir -p logs submissions

# Set environment variable to ensure Python prints output immediately
ENV PYTHONUNBUFFERED=1

# Command to run when container starts
CMD ["python", "main.py"]