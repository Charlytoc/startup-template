FROM python:3.12-slim-bullseye AS builder

# Install build dependencies
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
    build-essential \
    postgresql-client \
    libpq-dev \
    postgresql-server-dev-all \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.12-slim-bullseye

# Install runtime dependencies
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependencies and entry points from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY . .

# Create staticfiles directory and collect static files
RUN mkdir -p staticfiles && python manage.py collectstatic --noinput || echo "No static files to collect"

# Create a non-root user and group
RUN groupadd -r django && useradd -r -g django django
RUN chown -R django:django /app

# Switch to non-root user
USER django

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
