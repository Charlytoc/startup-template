# Django Service

This directory contains the Django REST API, Celery workers, and related configuration.

For installation, setup instructions, and all development commands, see the [root README](../README.md).

## Service-specific notes

- **Settings**: [config/settings.py](config/settings.py)
- **URL routing**: [config/urls.py](config/urls.py)
- **Celery config**: [config/celery.py](config/celery.py)
- **Django apps**: [core/](core/)
- **Postgres data volume**: [data/postgres/](data/postgres/) (gitignored)
- **Media uploads**: [media/](media/) (gitignored)

## Storage

See [STORAGE.md](STORAGE.md) for details on file/media storage configuration.
