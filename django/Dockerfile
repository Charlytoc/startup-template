FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create staticfiles directory and collect static files
RUN mkdir -p staticfiles && python manage.py collectstatic --noinput || echo "No static files to collect"

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
