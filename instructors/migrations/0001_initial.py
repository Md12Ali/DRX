import datetime

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Instructor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField(max_length=60, unique=True)),
                ("display_name", models.CharField(max_length=60)),
                ("tagline", models.CharField(blank=True, max_length=120)),
                ("bio", models.TextField(blank=True, max_length=1200)),
                ("areas_covered", models.CharField(help_text="Comma-separated towns or postcode areas, e.g. Ilford, Romford, IG3", max_length=200)),
                ("teaches", models.CharField(choices=[("manual", "Manual"), ("automatic", "Automatic"), ("both", "Manual and automatic")], default="manual", max_length=10)),
                ("car", models.CharField(blank=True, max_length=80)),
                ("photo", models.ImageField(blank=True, upload_to="instructors/")),
                ("hourly_rate_pence", models.PositiveIntegerField(default=4000, validators=[django.core.validators.MinValueValidator(1000), django.core.validators.MaxValueValidator(20000)])),
                ("working_days", models.CharField(default="012345", help_text="Days worked: 0 = Monday ... 6 = Sunday. '012345' is Monday to Saturday.", max_length=7)),
                ("day_start", models.TimeField(default=datetime.time(8, 0))),
                ("day_end", models.TimeField(default=datetime.time(20, 0))),
                ("is_accepting_pupils", models.BooleanField(default=True)),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="instructor", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["display_name"],
            },
        ),
        migrations.CreateModel(
            name="Review",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rating", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ("comment", models.TextField(max_length=600)),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                ("instructor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reviews", to="instructors.instructor")),
                ("learner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reviews", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_on"],
                "constraints": [models.UniqueConstraint(fields=("instructor", "learner"), name="one_review_per_learner")],
            },
        ),
    ]
