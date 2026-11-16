#!/usr/bin/env bash
# Render build script. Every step must pass or the deploy is stopped,
# so a broken build or a failing test can never go live.
set -o errexit

echo "==> Installing requirements"
pip install -r requirements.txt

echo "==> Checking the models match the migrations"
python manage.py makemigrations --check --dry-run

echo "==> Running the automated tests (on a throwaway SQLite database)"
DATABASE_URL="sqlite:///build-tests.sqlite3" python manage.py test --noinput -v 2

echo "==> Deployment checks"
python manage.py check --deploy --fail-level ERROR

echo "==> Collecting static files"
python manage.py collectstatic --noinput

echo "==> Applying migrations to the live database"
python manage.py migrate --noinput

# Create the admin account and the instructor profile on first deploy.
# Values come from environment variables set in the Render dashboard.
if [[ -n "${DJANGO_SUPERUSER_USERNAME:-}" && -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]]; then
  echo "==> Making sure the admin account and instructor profile exist"
  python manage.py createsuperuser --noinput || echo "Admin account already exists"
  python manage.py setup_instructor "$DJANGO_SUPERUSER_USERNAME" --name "${INSTRUCTOR_NAME:-DRX Instructor}"
fi
