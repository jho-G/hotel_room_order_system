#!/usr/bin/env bash
# Render build script — runs once per deploy before the service starts.
set -o errexit  # Abort immediately on any error

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --noinput

python manage.py migrate



python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        'jo',
        'yohanneshailegiorgis0@gmail.com',
        'dire@Adama'
    )
"