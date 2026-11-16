import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("bookings", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("stripe_session_id", models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ("stripe_payment_intent", models.CharField(blank=True, max_length=255)),
                ("amount_pence", models.PositiveIntegerField()),
                ("status", models.CharField(choices=[("pending", "Pending"), ("paid", "Paid"), ("failed", "Failed or cancelled"), ("refunded", "Refunded"), ("refund_failed", "Refund needs manual action")], default="pending", max_length=15)),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("paid_on", models.DateTimeField(blank=True, null=True)),
                ("booking", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="payment", to="bookings.booking")),
            ],
            options={
                "ordering": ["-created_on"],
            },
        ),
    ]
