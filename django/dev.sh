#!/bin/bash

case "$1" in
    "up")
        echo "Starting Django development container..."
        docker-compose up --build
        ;;
    "down")
        echo "Stopping Django development container..."
        docker-compose down
        ;;
    "restart")
        echo "Restarting Django development container..."
        docker-compose down
        docker-compose up --build
        ;;
    "logs")
        echo "Showing Django container logs..."
        docker-compose logs -f web
        ;;
    "shell")
        echo "Opening Django shell in container..."
        docker-compose exec web python manage.py shell
        ;;
    "migrate")
        echo "Running Django migrations..."
        docker-compose exec web python manage.py migrate
        ;;
    "makemigrations")
        echo "Creating Django migrations..."
        docker-compose exec web python manage.py makemigrations
        ;;
    "superuser")
        echo "Creating Django superuser..."
        docker-compose exec web python manage.py createsuperuser
        ;;
    "clean")
        echo "Cleaning up containers and images..."
        docker-compose down --rmi all --volumes --remove-orphans
        ;;
    *)
        echo "Django Development Helper"
        echo "Usage: ./dev.sh [command]"
        echo ""
        echo "Commands:"
        echo "  up          - Start the development container"
        echo "  down        - Stop the development container"
        echo "  restart     - Restart the development container"
        echo "  logs        - Show container logs"
        echo "  shell       - Open Django shell in container"
        echo "  migrate     - Run database migrations"
        echo "  makemigrations - Create new migrations"
        echo "  superuser   - Create Django superuser"
        echo "  clean       - Clean up containers and images"
        ;;
esac
