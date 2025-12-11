#!/bin/sh
set -e

# Ensure log directory exists for Django file logging
mkdir -p /var/log/linky

# Apply database migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser from environment variables if provided and missing
python manage.py shell <<'PYCODE'
import os
from django.contrib.auth import get_user_model

username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL")

if username and password:
    User = get_user_model()
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"Superuser '{username}' created.")
    else:
        print(f"Superuser '{username}' already exists; skipping creation.")
else:
    print("Superuser credentials not provided; skipping creation.")
PYCODE

# Start Gunicorn
exec gunicorn linkbio.wsgi:application --bind 0.0.0.0:8000
