"""
Copy this file to env.py (git-ignored) and fill in your own values.

    cp env_example.py env.py
"""
import os

os.environ.setdefault("SECRET_KEY", "replace-with-a-long-random-string")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1")
# DATABASE_URL is optional here: leave it unset to use a local SQLite file, or set it
# to a PostgreSQL connection string (postgres://user:password@host:5432/dbname).
os.environ.setdefault("STRIPE_PUBLIC_KEY", "pk_test_...")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_...")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_...")
