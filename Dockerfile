FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements-engine.txt .
RUN pip install --no-cache-dir -r requirements-engine.txt

COPY app.py .
COPY engine/ engine/
COPY ui/ ui/
COPY data/ data/

EXPOSE 8765
USER nobody
CMD ["python3", "app.py", "--http", "0.0.0.0:8765", "--i-understand-lan"]
