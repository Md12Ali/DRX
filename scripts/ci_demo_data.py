"""
Sample data for the automated screenshots taken in GitHub Actions.
Runs ONLY against the throwaway database of the CI runner, never the live site.
Usage: python manage.py shell < scripts/ci_demo_data.py
"""
import datetime
import json

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

from bookings.models import Booking
from instructors.models import Instructor
from packages.models import LessonPackage, PackagePurchase
from payments.models import Payment
from progress.models import Skill, SkillRating

User = get_user_model()
PASSWORD = "Screenshot-pass-2026"


def at(days, hour, minute=0):
    date = timezone.localdate() + datetime.timedelta(days=days)
    return timezone.make_aware(datetime.datetime.combine(date, datetime.time(hour, minute)))


ali = User.objects.create_user("ali", "ali@example.com", PASSWORD, first_name="Mohammed", last_name="Ali")
call_command("setup_instructor", "ali", "--name", "Mohammed Ali")
instructor = Instructor.objects.get(user=ali)
instructor.tagline = "Calm, patient lessons for nervous beginners and test-ready learners."
instructor.bio = (
    "Born and raised in East London, I know these roads and test routes inside out. "
    "My lessons are calm and patient, and every one is planned around what you need to work on next."
)
instructor.car = "VW Polo, dual controls"
instructor.working_days = "0123456"
instructor.save()

jamil = User.objects.create_user("jamil", "jamil@example.com", PASSWORD, first_name="Jamil")
profile = jamil.profile
profile.phone = "07700 900123"
profile.pickup_address = "12 Roman Road, London"
profile.postcode = "E3 5AA"
profile.save()

PackagePurchase.objects.create(
    learner=jamil, package=LessonPackage.objects.get(slug="popular-10"), hours=10, price_pence=33000,
    status=PackagePurchase.Status.PAID, stripe_session_id="cs_demo_pkg", paid_on=timezone.now(),
)


def booking(start, minutes=60, status=Booking.Status.CONFIRMED, method=Booking.PaymentMethod.CARD, notes=""):
    return Booking.objects.create(
        learner=jamil, instructor=instructor, start=start, duration_minutes=minutes,
        pickup_address="12 Roman Road, London", pickup_postcode="E3 5AA",
        price_pence=instructor.lesson_price_pence(minutes), status=status,
        payment_method=method, instructor_notes=notes,
    )


done1 = booking(at(-9, 10), 90, Booking.Status.COMPLETED, notes="Great start. Smooth clutch control; practise hill starts.")
done2 = booking(at(-2, 16), 120, Booking.Status.COMPLETED, Booking.PaymentMethod.PACKAGE,
                notes="Roundabouts much better. Next time: parallel parking and pedestrian crossings.")
Payment.objects.create(booking=done1, amount_pence=done1.price_pence, status=Payment.Status.PAID,
                       stripe_session_id="cs_demo_1", paid_on=timezone.now())
next_lesson = booking(at(2, 9, 30), 90)
Payment.objects.create(booking=next_lesson, amount_pence=next_lesson.price_pence, status=Payment.Status.PAID,
                       stripe_session_id="cs_demo_2", paid_on=timezone.now())
booking(at(4, 17), 60, method=Booking.PaymentMethod.PACKAGE)
pending = booking(at(6, 11), 120, Booking.Status.PENDING)
to_sign_off = booking(timezone.now() - datetime.timedelta(hours=3), 60)

levels = [5, 5, 4, 4, 4, 3, 3, 4, 2, 1, 3, 2, 2, 1, 0, 3]
for skill, level in zip(Skill.objects.all(), levels):
    if level:
        SkillRating.objects.create(learner=jamil, skill=skill, level=level, updated_by=ali)

with open("ci-demo.json", "w") as handle:
    json.dump({
        "password": PASSWORD, "slug": instructor.slug, "pending": pending.pk,
        "next": next_lesson.pk, "sign_off": to_sign_off.pk,
        "free_date": (timezone.localdate() + datetime.timedelta(days=3)).isoformat(),
    }, handle)
print("Demo data ready")
