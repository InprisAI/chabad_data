# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY search_maamar_with_openai.py .
COPY 2_maamarim_unified.pkl.gz maamarim_unified.pkl.gz

# Set environment variables (these will be overridden by Cloud Run)
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run with gunicorn for production
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app



