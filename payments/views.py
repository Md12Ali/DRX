"""Paying for a booking: by card through Stripe, or with prepaid package hours."""
import logging

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from bookings.models import Booking
from packages.models import PackagePurchase, hours_display, package_minutes_balance

from .models import Payment
from .stripe_client import create_checkout_session, stripe_ready

logger = logging.getLogger(__name__)


def _payable_booking(request, pk):
    """
    The learner's booking if it can still be paid for, otherwise a redirect
    with a helpful message. Returns (booking, redirect_response).
    """
    booking = get_object_or_404(
        Booking.objects.select_related("instructor"), pk=pk, learner=request.user
    )
    if booking.status == Booking.Status.CONFIRMED:
        messages.info(request, "This lesson is already paid for.")
        return booking, redirect(booking)
    if not booking.is_awaiting_payment:
        Booking.objects.expire_stale_holds()
        messages.error(
            request,
            "The time we held for you has run out, so the slot has been released. "
            "You have not been charged. Please book again.",
        )
        return booking, redirect(booking.instructor)
    return booking, None


@login_required
def checkout(request, pk):
    """Show payment options (GET) and send the learner to Stripe (POST)."""
    booking, problem = _payable_booking(request, pk)
    if problem:
        return problem

    if request.method == "GET":
        balance = package_minutes_balance(request.user)
        context = {
            "booking": booking,
            "balance_hours": hours_display(balance),
            "can_use_package": balance >= booking.duration_minutes,
            "has_package_hours": balance > 0,
        }
        return render(request, "payments/checkout.html", context)

    if not stripe_ready():
        messages.error(request, "Card payments are not available right now. You have not been charged.")
        return redirect("payments:checkout", booking.pk)

    payment, _ = Payment.objects.get_or_create(
        booking=booking, defaults={"amount_pence": booking.price_pence}
    )
    local_start = timezone.localtime(booking.start)
    try:
        session = create_checkout_session(
            name=f"Driving lesson with {booking.instructor.display_name}",
            description=(
                f"{booking.get_duration_minutes_display()} on "
                f"{local_start:%a %d %b %Y at %H:%M} · {booking.reference}"
            ),
            amount_pence=booking.price_pence,
            email=request.user.email,
            reference=booking.reference,
            client_reference_id=booking.pk,
            success_url=request.build_absolute_uri(reverse("payments:success")),
            cancel_url=request.build_absolute_uri(reverse("payments:cancelled", args=[booking.pk])),
        )
    except stripe.StripeError as error:
        logger.warning("Stripe checkout failed for %s: %s", booking.reference, error)
        messages.error(
            request,
            "We couldn't reach our payment provider. You have not been charged. "
            "Please try again in a moment.",
        )
        return redirect("payments:checkout", booking.pk)

    payment.stripe_session_id = session.id
    payment.status = Payment.Status.PENDING
    payment.save(update_fields=["stripe_session_id", "status"])
    return redirect(session.url)


@login_required
@require_POST
def pay_with_package(request, pk):
    """Confirm a booking using the learner's prepaid package hours."""
    booking, problem = _payable_booking(request, pk)
    if problem:
        return problem

    with transaction.atomic():
        balance = package_minutes_balance(request.user)
        if balance < booking.duration_minutes:
            messages.error(
                request,
                f"You have {hours_display(balance)} hours left, but this lesson needs "
                f"{booking.hours_display}. Please pay by card or buy a package.",
            )
            return redirect("payments:checkout", booking.pk)
        booking.payment_method = Booking.PaymentMethod.PACKAGE
        booking.status = Booking.Status.CONFIRMED
        booking.save(update_fields=["payment_method", "status", "updated_on"])

    remaining = package_minutes_balance(request.user)
    messages.success(
        request,
        f"Lesson booked using {booking.hours_label} from your package. "
        f"You have {hours_display(remaining)} hours left.",
    )
    return redirect(booking)


@login_required
def checkout_success(request):
    """Stripe sends the learner here after paying. Verify with Stripe first."""
    session_id = request.GET.get("session_id", "")
    payment = (
        Payment.objects.select_related("booking", "booking__instructor")
        .filter(stripe_session_id=session_id, booking__learner=request.user)
        .first()
    )
    if not session_id or payment is None:
        messages.error(request, "We couldn't find that payment.")
        return redirect("bookings:dashboard")

    if payment.status != Payment.Status.PAID:
        if not stripe_ready():
            messages.error(request, "Card payments are not available right now.")
            return redirect("bookings:dashboard")
        try:
            session = stripe.checkout.Session.retrieve(session_id)
        except stripe.StripeError as error:
            logger.warning("Stripe lookup failed for %s: %s", session_id, error)
            messages.warning(
                request,
                "We couldn't confirm your payment yet. If you were charged, your lesson "
                "will show as confirmed within a few minutes.",
            )
            return redirect(payment.booking)
        if session.payment_status != "paid":
            messages.warning(request, "Your payment hasn't gone through yet.")
            return redirect("payments:checkout", payment.booking.pk)
        payment.mark_paid(getattr(session, "payment_intent", "") or "")

    messages.success(request, f"Payment of {payment.amount_display} received. Your lesson is booked!")
    return render(request, "payments/success.html", {"payment": payment, "booking": payment.booking})


@login_required
def checkout_cancelled(request, pk):
    """Stripe sends the learner here if they leave the checkout page."""
    booking = get_object_or_404(Booking, pk=pk, learner=request.user)
    payment = getattr(booking, "payment", None)
    if payment is not None:
        payment.mark_failed()
    messages.info(request, "Payment cancelled. You have not been charged.")
    return render(request, "payments/cancelled.html", {"booking": booking})


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Stripe calls this directly, so payments for lessons and packages are
    recorded even if the learner closes their browser before returning.
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        return HttpResponseBadRequest("Webhook not configured.")

    try:
        event = stripe.Webhook.construct_event(
            request.body,
            request.headers.get("stripe-signature", ""),
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except (ValueError, stripe.SignatureVerificationError):
        return HttpResponseBadRequest("Invalid payload or signature.")

    session = event["data"]["object"]
    session_id = session.get("id")
    record = (
        Payment.objects.filter(stripe_session_id=session_id).first()
        or PackagePurchase.objects.filter(stripe_session_id=session_id).first()
    )
    if record is not None:
        if event["type"] in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
            if session.get("payment_status") == "paid":
                record.mark_paid(session.get("payment_intent") or "")
        elif event["type"] in ("checkout.session.expired", "checkout.session.async_payment_failed"):
            record.mark_failed()

    return HttpResponse(status=200)
