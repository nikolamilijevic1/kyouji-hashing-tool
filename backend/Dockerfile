FROM python:3.11-slim

WORKDIR /app

# Set PYTHONPATH to the root so absolute imports like 'from backend.logic' work
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run automated tests during build (Logic & API)
RUN python tests/test_logic.py
RUN python tests/test_api.py

EXPOSE 8000

# Start the application using the full package path
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
