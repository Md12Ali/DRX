# DRX lessons are in an automatic car: new instructors default to automatic,
# and the existing instructor and learners are switched over.
from django.db import migrations, models


def use_automatic(apps, schema_editor):
    Instructor = apps.get_model("instructors", "Instructor")
    Profile = apps.get_model("accounts", "Profile")
    Instructor.objects.filter(teaches="manual").update(teaches="automatic")
    Profile.objects.filter(transmission="manual").update(transmission="automatic")


class Migration(migrations.Migration):

    dependencies = [
        ("instructors", "0002_qualification_and_rate"),
        ("accounts", "0002_default_automatic"),
    ]

    operations = [
        migrations.AlterField(
            model_name="instructor",
            name="teaches",
            field=models.CharField(
                choices=[("manual", "Manual"), ("automatic", "Automatic"), ("both", "Manual and automatic")],
                default="automatic",
                max_length=10,
            ),
        ),
        migrations.RunPython(use_automatic, migrations.RunPython.noop),
    ]
