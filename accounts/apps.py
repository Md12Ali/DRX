"""App configuration for the accounts app."""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Registers the accounts app and wires up its signals."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        # Importing the module connects the signal receivers.
        from . import signals  # noqa: F401  pylint: disable=import-outside-toplevel,unused-import
