# Lessons are taught in an automatic car, so new learners default to automatic.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="transmission",
            field=models.CharField(
                choices=[("manual", "Manual"), ("automatic", "Automatic")],
                default="automatic",
                max_length=10,
            ),
        ),
    ]
