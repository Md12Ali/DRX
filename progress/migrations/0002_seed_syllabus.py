"""Load the driving syllabus that progress is measured against."""
from django.db import migrations

SYLLABUS = [
    ("Cockpit drill and controls", "controls", "Doors, seat, steering, seatbelt, mirrors, and the main controls."),
    ("Moving off and stopping", "controls", "Safely, under control, with good observation."),
    ("Clutch control and gears", "controls", "Smooth gear changes and holding the car on a hill."),
    ("Mirrors, signals and observation", "controls", "Using the MSM routine at the right time."),
    ("Speed and road positioning", "roads", "Keeping to limits and the correct position in the lane."),
    ("Junctions", "roads", "Approaching, turning and emerging at T-junctions and crossroads."),
    ("Roundabouts", "roads", "Lane choice, signalling and judging gaps."),
    ("Pedestrian crossings", "roads", "Zebra, pelican, puffin and toucan crossings."),
    ("Meeting and overtaking traffic", "roads", "Narrow roads, parked cars and safe overtaking."),
    ("Dual carriageways", "roads", "Joining, lane discipline and leaving at speed."),
    ("Emergency stop", "manoeuvres", "Stopping quickly and safely under control."),
    ("Parallel parking", "manoeuvres", "Parking behind a car at the side of the road."),
    ("Bay parking", "manoeuvres", "Forward and reverse into a parking bay."),
    ("Pull up on the right", "manoeuvres", "Stopping on the right, reversing two car lengths, rejoining."),
    ("Independent driving", "test", "Following a sat nav or road signs without instruction."),
    ("Show me, tell me questions", "test", "Vehicle safety questions asked on the test."),
]


def add_skills(apps, schema_editor):
    Skill = apps.get_model("progress", "Skill")
    for order, (name, category, description) in enumerate(SYLLABUS, start=1):
        Skill.objects.update_or_create(
            name=name,
            defaults={"category": category, "description": description, "order": order},
        )


def remove_skills(apps, schema_editor):
    Skill = apps.get_model("progress", "Skill")
    Skill.objects.filter(name__in=[row[0] for row in SYLLABUS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("progress", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(add_skills, remove_skills),
    ]
