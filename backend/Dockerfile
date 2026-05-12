FROM python:3.11-slim

WORKDIR /app

# Set PYTHONPATH so absolute imports like 'from backend.logic' work
ENV PYTHONPATH=/app

# Copy requirements from the backend folder
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code and the tests
COPY backend/ backend/
COPY tests/ tests/

# Run automated tests during build (Logic & API)
RUN python tests/test_logic.py
RUN python tests/test_api.py

EXPOSE 8000

# Start the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
