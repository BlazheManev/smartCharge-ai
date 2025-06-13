# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Set environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git curl build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy project files
COPY . .

# Install pipx & poetry
RUN pip install --no-cache-dir pipx \
  && pipx ensurepath \
  && pipx install poetry

# Configure poetry
ENV PATH="/root/.local/bin:$PATH"
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-root

# Install DVC (with S3 support, adjust if needed)
RUN pip install dvc[s3]

# Set default environment variables (can override at runtime)
ENV MONGO_URI=replace_me
ENV DAGSHUB_ACCESS_KEY_ID=replace_me
ENV DAGSHUB_SECRET_ACCESS_KEY=replace_me

# Default command: run full pipeline
CMD ["poetry", "run", "dvc", "repro"]
