"""
Load the starting packages. Prices are based on £35 an hour pay-as-you-go,
with a bigger discount for bigger packages. Change them any time in the admin.
"""
from django.db import migrations

PACKAGES = [
    ("starter-5", "Starter", 5, 17000, "Five hours to get you moving. Great for complete beginners.", False),
    ("popular-10", "Confidence", 10, 33000, "Ten hours: the most popular choice for steady weekly learners.", True),
    ("test-ready-20", "Test Ready", 20, 64000, "Twenty hours to take you from roundabouts to test day.", False),
    ("intensive-30", "Intensive", 30, 93000, "Thirty hours for intensive courses or learners starting from scratch.", False),
]


def add_packages(apps, schema_editor):
    LessonPackage = apps.get_model("packages", "LessonPackage")
    for order, (slug, name, hours, price, description, popular) in enumerate(PACKAGES, start=1):
        LessonPackage.objects.update_or_create(
            slug=slug,
            defaults={
                "name": name, "hours": hours, "price_pence": price,
                "description": description, "is_popular": popular, "order": order,
            },
        )


def remove_packages(apps, schema_editor):
    LessonPackage = apps.get_model("packages", "LessonPackage")
    LessonPackage.objects.filter(slug__in=[row[0] for row in PACKAGES], purchases__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("packages", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(add_packages, remove_packages),
    ]
