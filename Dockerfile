FROM python:3.10

# Set working directory
WORKDIR /app

# Copy all files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 7860

# Run FastAPI server
CMD ["uvicorn", "environment:app", "--host", "0.0.0.0", "--port", "7860"]