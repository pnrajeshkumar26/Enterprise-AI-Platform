# Base Python image
FROM python:3.11-slim

# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Ensure Python output is sent straight to the terminal
ENV PYTHONUNBUFFERED=1

# Working directory inside the container
WORKDIR /app

# Copy dependency list first
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# FastAPI listens on port 8000
EXPOSE 8000

# Start Runtime API
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]