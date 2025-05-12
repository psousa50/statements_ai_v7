FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=1.8.2
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Disable Poetry virtualenvs
ENV POETRY_VIRTUALENVS_CREATE=false

# Copy files
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root

COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["./start_app.sh"]