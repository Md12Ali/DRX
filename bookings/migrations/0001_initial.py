import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("instructors", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Booking",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("start", models.DateTimeField()),
                ("end", models.DateTimeField()),
                ("duration_minutes", models.PositiveSmallIntegerField(choices=[(60, "1 hour"), (90, "1.5 hours"), (120, "2 hours")], default=60)),
                ("pickup_address", models.CharField(max_length=200)),
                ("learner_notes", models.TextField(blank=True, max_length=500)),
                ("instructor_notes", models.TextField(blank=True, max_length=1000)),
                ("price_pence", models.PositiveIntegerField()),
                ("status", models.CharField(choices=[("pending", "Awaiting payment"), ("confirmed", "Confirmed"), ("completed", "Completed"), ("cancelled", "Cancelled"), ("expired", "Expired (not paid)")], default="pending", max_length=10)),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                ("instructor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="bookings", to="instructors.instructor")),
                ("learner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="bookings", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["start"],
                "constraints": [models.CheckConstraint(condition=models.Q(("end__gt", models.F("start"))), name="booking_ends_after_start")],
            },
        ),
    ]
