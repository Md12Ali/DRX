"""ASGI config for the DRX project."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "drx.settings")

application = get_asgi_application()
