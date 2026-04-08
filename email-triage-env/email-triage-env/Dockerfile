FROM python:3.11-slim

# HF Spaces runs on port 7860
ENV PORT=7860

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Expose port
EXPOSE 7860

# Start the FastAPI server
CMD ["uvicorn", "environment:app", "--host", "0.0.0.0", "--port", "7860"]
