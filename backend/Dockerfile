FROM python:3.12-slim

WORKDIR /app

# System dependencies for psycopg2-binary / asyncpg / shap
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Directory for saved ML model artifacts (can be mounted as volume)
RUN mkdir -p app/ml/models

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
