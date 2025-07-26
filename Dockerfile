FROM python:3.12-slim

# Install system dependencies
RUN apt update && apt install -y curl

# Set up working directory (your app will be mounted here via Docker Compose)
WORKDIR /app

# Copy requirements.txt into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Default command to run the app
CMD ["python", "app.py"]
