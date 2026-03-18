#!/bin/bash

set -e

cd /app/
gunicorn --workers=4 --threads=2 --bind=0.0.0.0:8000 --log-level info config.wsgi:application
