"""
Turn an existing user account into the site's instructor.

    python manage.py createsuperuser            # make your own account first
    python manage.py setup_instructor ali --name "Mohammed Ali"

Uses the hourly rate and postcode areas from settings. Everything else
(photo, bio, hours, qualification) can then be edited on the site under
"Edit profile" or in the admin.
"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from instructors.models import Instructor

User = get_user_model()


class Command(BaseCommand):
    help = "Create or update the instructor profile for an existing user."

    def add_arguments(self, parser):
        parser.add_argument("username", help="The username of an existing account.")
        parser.add_argument("--name", required=True, help='Public name, e.g. "Mohammed Ali".')
        parser.add_argument(
            "--adi", action="store_true",
            help="Only use once you're on the ADI register. Without it you're shown as a trainee.",
        )

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username=options["username"])
        except User.DoesNotExist as error:
            raise CommandError(f"No user called {options['username']!r}. Run createsuperuser first.") from error

        name = options["name"].strip()
        instructor, created = Instructor.objects.update_or_create(
            user=user,
            defaults={
                "display_name": name,
                "slug": slugify(name) or user.username,
                "areas_covered": ", ".join(settings.COVERED_POSTCODE_DISTRICTS),
                "hourly_rate_pence": settings.STANDARD_HOURLY_RATE_PENCE,
                "qualification": (
                    Instructor.Qualification.ADI if options["adi"] else Instructor.Qualification.TRAINEE
                ),
            },
        )
        if not user.first_name:
            user.first_name = name.split()[0]
            user.save(update_fields=["first_name"])

        verb = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(
            f"{verb} instructor profile for {name} at /instructors/{instructor.slug}/"
        ))
