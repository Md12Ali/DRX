"""
Create demo instructor accounts so a fresh install has something to book.

    python manage.py seed_demo

Every demo account is clearly labelled as a demo. Remove them in the
admin before taking real bookings. No reviews are created, because
reviews must come from real learners.
"""
import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from instructors.models import Instructor

User = get_user_model()

DEMO_INSTRUCTORS = [
    {
        "username": "demo-ali",
        "display_name": "Ali M (demo)",
        "tagline": "Calm, patient lessons for nervous beginners.",
        "areas_covered": "Ilford, Goodmayes, Seven Kings, IG3",
        "teaches": Instructor.Teaches.MANUAL,
        "car": "VW Polo, dual controls",
        "hourly_rate_pence": 4000,
        "working_days": "012345",
    },
    {
        "username": "demo-priya",
        "display_name": "Priya S (demo)",
        "tagline": "Automatic specialist. Test routes around Barking and Hornchurch.",
        "areas_covered": "Barking, Romford, Hornchurch, RM1",
        "teaches": Instructor.Teaches.AUTOMATIC,
        "car": "Toyota Yaris Hybrid, automatic",
        "hourly_rate_pence": 4500,
        "working_days": "01234",
    },
    {
        "username": "demo-tom",
        "display_name": "Tom R (demo)",
        "tagline": "Intensive courses and motorway lessons.",
        "areas_covered": "Stratford, Leyton, Walthamstow, E15",
        "teaches": Instructor.Teaches.BOTH,
        "car": "Ford Fiesta (manual) and Kia Niro (automatic)",
        "hourly_rate_pence": 4200,
        "working_days": "123456",
    },
]


class Command(BaseCommand):
    help = "Create clearly-labelled demo instructor accounts for testing."

    def handle(self, *args, **options):
        created = 0
        for data in DEMO_INSTRUCTORS:
            user, user_created = User.objects.get_or_create(
                username=data["username"],
                defaults={"first_name": data["display_name"].split()[0]},
            )
            if user_created:
                user.set_unusable_password()
                user.save()
            _, instructor_created = Instructor.objects.get_or_create(
                user=user,
                defaults={
                    "slug": data["username"],
                    "display_name": data["display_name"],
                    "tagline": data["tagline"],
                    "bio": (
                        "This is a demo instructor account used to test DRX. "
                        "Replace it with a real instructor profile in the admin."
                    ),
                    "areas_covered": data["areas_covered"],
                    "teaches": data["teaches"],
                    "car": data["car"],
                    "hourly_rate_pence": data["hourly_rate_pence"],
                    "working_days": data["working_days"],
                    "day_start": datetime.time(8, 0),
                    "day_end": datetime.time(19, 0),
                },
            )
            created += int(instructor_created)
        self.stdout.write(self.style.SUCCESS(f"Created {created} demo instructor(s)."))
