FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    OPENSEARCH_URL=http://opensearch:9200 \
    RATE_LIMIT_PER_MIN=120

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src
COPY requests.http ./

EXPOSE 8080

CMD ["uvicorn", "src.main.app:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers"]
