# Stage 1: Build
FROM python:3.12-slim as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml poetry.lock* ./

# Generate requirements.txt to avoid installing Poetry in the final image
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# Stage 2: Final
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /backend/app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY .. .

# Script to wait for DB and run migrations (to be created)
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]