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
            name="Skill",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True)),
                ("category", models.CharField(choices=[("controls", "Car control"), ("roads", "Roads and junctions"), ("manoeuvres", "Manoeuvres"), ("test", "Test readiness")], max_length=12)),
                ("description", models.CharField(blank=True, max_length=200)),
                ("order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                "ordering": ["order", "name"],
            },
        ),
        migrations.CreateModel(
            name="SkillRating",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("level", models.PositiveSmallIntegerField(choices=[(1, "Introduced"), (2, "Under full instruction"), (3, "Prompted"), (4, "Seldom prompted"), (5, "Independent")], default=1)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                ("learner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="skill_ratings", to=settings.AUTH_USER_MODEL)),
                ("skill", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ratings", to="progress.skill")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["skill__order"],
                "constraints": [models.UniqueConstraint(fields=("learner", "skill"), name="one_rating_per_skill")],
            },
        ),
    ]
