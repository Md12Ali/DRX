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
            name="Profile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("phone", models.CharField(blank=True, max_length=20, validators=[django.core.validators.RegexValidator(message="Enter a UK mobile number, for example 07700 900123.", regex="^(\\+44\\s?7\\d{3}|07\\d{3})\\s?\\d{3}\\s?\\d{3}$")])),
                ("pickup_address", models.CharField(blank=True, max_length=200)),
                ("postcode", models.CharField(blank=True, max_length=10, validators=[django.core.validators.RegexValidator(message="Enter a valid UK postcode, for example IG3 8XX.", regex="^[A-Za-z]{1,2}\\d[A-Za-z\\d]?\\s?\\d[A-Za-z]{2}$")])),
                ("transmission", models.CharField(choices=[("manual", "Manual"), ("automatic", "Automatic")], default="manual", max_length=10)),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
