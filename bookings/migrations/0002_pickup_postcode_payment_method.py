from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="pickup_postcode",
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name="booking",
            name="payment_method",
            field=models.CharField(
                choices=[("card", "Card"), ("package", "Package hours")],
                default="card",
                max_length=10,
            ),
        ),
    ]
