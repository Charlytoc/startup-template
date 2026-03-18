#!/usr/bin/env bash

set -e

cd /app/
python manage.py runserver 0.0.0.0:8000
