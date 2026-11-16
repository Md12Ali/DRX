import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("instructors", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="instructor",
            name="qualification",
            field=models.CharField(
                choices=[
                    ("trainee", "Trainee driving instructor (DVSA trainee licence)"),
                    ("adi", "DVSA Approved Driving Instructor (ADI)"),
                ],
                default="trainee",
                help_text="Only choose ADI once you're on the ADI register. Trainees must not advertise as ADIs.",
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name="instructor",
            name="hourly_rate_pence",
            field=models.PositiveIntegerField(
                default=3500,
                validators=[
                    django.core.validators.MinValueValidator(1000),
                    django.core.validators.MaxValueValidator(20000),
                ],
            ),
        ),
    ]
