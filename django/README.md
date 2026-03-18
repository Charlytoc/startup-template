# Speaky.ai Django Project

A Django project with Docker containerization, PostgreSQL, Redis, and Celery for background task processing.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Git

### Initial Setup
```bash
# Navigate to django directory
cd django

# Make taskfile executable (Linux/Mac)
chmod +x taskfile.sh

# Set up environment variables
./taskfile.sh setup-env

# Start development environment
./taskfile.sh dev

# Initialize Django (first time only)
./taskfile.sh setup-django
```

### Development Commands

```bash
# Start development environment (runs in background)
./taskfile.sh dev

# Start without rebuilding images
./taskfile.sh dev --skip-build

# View logs
./taskfile.sh logs

# Check service health
./taskfile.sh health
```

### Production Commands

```bash
# Start production environment
./taskfile.sh prod

# Stop production environment
./taskfile.sh prod-stop

# Restart production environment
./taskfile.sh prod-restart
```

## 🏗️ Architecture

### Services
- **Django Web App** - Main application server
- **PostgreSQL** - Primary database
- **Redis** - Cache and Celery message broker
- **Celery Worker** - Background task processing
- **Celery Beat** - Scheduled task scheduler

### Ports
- Django: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## 📋 Available Commands

### Development
- `dev` - Start development environment
- `dev-build` - Build and start development environment
- `dev-stop` - Stop development environment
- `dev-restart` - Restart development environment

### Production
- `prod` - Start production environment
- `prod-stop` - Stop production environment
- `prod-restart` - Restart production environment

### Database
- `migrate` - Run database migrations
- `makemigrations` - Create new migrations
- `migrate-prod` - Run production migrations

### Django
- `shell` - Open Django shell
- `dbshell` - Open database shell
- `createsuperuser` - Create Django superuser
- `collectstatic` - Collect static files

### Celery
- `celery-logs` - Show Celery worker logs
- `celery-beat-logs` - Show Celery beat logs
- `celery-shell` - Open Celery shell

### Logging
- `logs` - Show all logs
- `logs-web` - Show web logs
- `logs-db` - Show database logs
- `logs-redis` - Show Redis logs

### Utility
- `ps` - Show running containers
- `exec <container> <command>` - Execute command in container
- `health` - Check service health
- `clean` - Clean up Docker resources
- `setup` - Initial setup
- `help` - Show help

## 🔧 Configuration

### Environment Variables
Create a `.env` file based on `.env.example`:

```bash
# Database Configuration
POSTGRES_DB=startup_db
POSTGRES_USER=startup_user
POSTGRES_PASSWORD=startup_password
POSTGRES_HOST=postgres

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Django Configuration
DEBUG=1
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
```

## 🐳 Docker Commands

### Manual Docker Commands
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Execute command in container
docker-compose exec web python manage.py shell
docker-compose exec postgres psql -U startup_user -d startup_db
docker-compose exec redis redis-cli
```

### Docker Commands
```bash
# Start services
docker-compose -f docker-compose.yml up -d

# Stop services
docker-compose -f docker-compose.yml down
```

## 📁 Project Structure

```
django/
├── config/                 # Django settings and configuration
│   ├── celery.py          # Celery configuration
│   ├── settings.py        # Django settings
│   └── urls.py           # URL routing
├── core/                  # Django apps
├── docker-compose.yml     # Single Docker Compose stack
├── Dockerfile            # Docker image definition
├── taskfile.sh           # Development automation script
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
└── README.md            # This file
```

## 🔄 Background Tasks

### Creating Tasks
Create tasks in your Django apps:

```python
# core/tasks.py
from celery import shared_task

@shared_task
def my_background_task(param1, param2):
    # Your task logic here
    return f"Task completed with {param1} and {param2}"
```

### Scheduling Tasks
Use Celery Beat for scheduled tasks:

```python
# config/celery.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    'my-scheduled-task': {
        'task': 'core.tasks.my_background_task',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
}
```

## 🛠️ Development Workflow

1. **Start development environment**: `./taskfile.sh dev`
2. **Make changes** to your code
3. **View logs** if needed: `./taskfile.sh logs`
4. **Run migrations** if database changes: `./taskfile.sh migrate`
5. **Test your changes** at http://localhost:8000
6. **Stop when done**: `./taskfile.sh dev-stop`

## 🚨 Troubleshooting

### Common Issues

1. **Port already in use**: Stop other services using ports 8000, 5432, or 6379
2. **Database connection issues**: Wait for PostgreSQL to fully start (check with `./taskfile.sh health`)
3. **Permission errors**: Make sure taskfile.sh is executable: `chmod +x taskfile.sh`

### Reset Everything
```bash
./taskfile.sh clean
./taskfile.sh setup
```

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
