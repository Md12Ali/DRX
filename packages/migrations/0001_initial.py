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
            name="LessonPackage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField(max_length=40, unique=True)),
                ("name", models.CharField(max_length=60)),
                ("hours", models.PositiveSmallIntegerField()),
                ("price_pence", models.PositiveIntegerField()),
                ("description", models.CharField(blank=True, max_length=200)),
                ("is_popular", models.BooleanField(default=False, help_text="Highlight as the most popular package.")),
                ("is_active", models.BooleanField(default=True)),
                ("order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                "ordering": ["order", "hours"],
            },
        ),
        migrations.CreateModel(
            name="PackagePurchase",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("hours", models.PositiveSmallIntegerField(help_text="Copied from the package when bought.")),
                ("price_pence", models.PositiveIntegerField(help_text="Copied from the package when bought.")),
                ("status", models.CharField(choices=[("pending", "Pending"), ("paid", "Paid"), ("failed", "Failed or cancelled")], default="pending", max_length=10)),
                ("stripe_session_id", models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ("stripe_payment_intent", models.CharField(blank=True, max_length=255)),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("paid_on", models.DateTimeField(blank=True, null=True)),
                ("learner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="package_purchases", to=settings.AUTH_USER_MODEL)),
                ("package", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="purchases", to="packages.lessonpackage")),
            ],
            options={
                "ordering": ["-created_on"],
            },
        ),
    ]
