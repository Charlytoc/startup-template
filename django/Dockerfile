FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project

COPY . .
RUN uv sync --frozen

ENV PATH="/app/.venv/bin:$PATH"

RUN mkdir -p staticfiles && python manage.py collectstatic --noinput || echo "No static files to collect"

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
