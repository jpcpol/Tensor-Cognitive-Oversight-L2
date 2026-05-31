FROM python:3.11-slim

WORKDIR /app

# Build context is ./src — the tco_engine package lives at /app/tco_engine
COPY tco_engine/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY tco_engine ./tco_engine

CMD ["uvicorn", "tco_engine.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
