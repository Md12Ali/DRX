# Lessons are now 1 or 2 hours: the 1.5-hour option is removed.
# Any 1.5-hour booking already made is kept as it is; only new bookings are limited.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0002_pickup_postcode_payment_method"),
    ]

    operations = [
        migrations.AlterField(
            model_name="booking",
            name="duration_minutes",
            field=models.PositiveSmallIntegerField(choices=[(60, "1 hour"), (120, "2 hours")], default=60),
        ),
    ]
