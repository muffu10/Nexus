
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python dependencies first.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application.
COPY app/ ./app/

EXPOSE 8000

# Start the FastAPI API server.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
