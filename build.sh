#!/usr/bin/env bash
# Render build script — runs once per deploy before the service starts.
set -o errexit  # Abort immediately on any error

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --noinput

python manage.py migrate
