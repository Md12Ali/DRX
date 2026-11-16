"""Stripe Checkout for lesson bookings."""
import logging
import time

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from bookings.models import Booking

from .models import Payment

logger = logging.getLogger(__name__)

# Stripe Checkout sessions must stay open for at least 30 minutes.
CHECKOUT_SESSION_MINUTES = 30


def _stripe_ready():
    """True if the secret key needed to talk to Stripe is configured."""
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return bool(settings.STRIPE_SECRET_KEY)


@login_required
def checkout(request, pk):
    """Show the booking summary (GET) and send the learner to Stripe (POST)."""
    booking = get_object_or_404(
        Booking.objects.select_related("instructor"), pk=pk, learner=request.user
    )

    if booking.status == Booking.Status.CONFIRMED:
        messages.info(request, "This lesson is already paid for.")
        return redirect(booking)
    if not booking.is_awaiting_payment:
        Booking.objects.expire_stale_holds()
        messages.error(
            request,
            "The time we held for you has run out, so the slot has been released. "
            "You have not been charged. Please book again.",
        )
        return redirect(booking.instructor)

    if request.method == "GET":
        return render(request, "payments/checkout.html", {"booking": booking})

    if not _stripe_ready():
        messages.error(request, "Card payments are not available right now. You have not been charged.")
        return redirect("payments:checkout", booking.pk)

    payment, _ = Payment.objects.get_or_create(
        booking=booking, defaults={"amount_pence": booking.price_pence}
    )
    local_start = timezone.localtime(booking.start)
    success_url = request.build_absolute_uri(reverse("payments:success"))
    cancel_url = request.build_absolute_uri(reverse("payments:cancelled", args=[booking.pk]))

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": settings.STRIPE_CURRENCY,
                    "unit_amount": booking.price_pence,
                    "product_data": {
                        "name": f"Driving lesson with {booking.instructor.display_name}",
                        "description": (
                            f"{booking.get_duration_minutes_display()} on "
                            f"{local_start:%a %d %b %Y at %H:%M} · {booking.reference}"
                        ),
                    },
                },
                "quantity": 1,
            }],
            customer_email=request.user.email or None,
            client_reference_id=str(booking.pk),
            metadata={"booking_reference": booking.reference},
            expires_at=int(time.time()) + CHECKOUT_SESSION_MINUTES * 60,
            success_url=f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=cancel_url,
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
        if not _stripe_ready():
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
    Stripe calls this directly, so payments are recorded even if the
    learner closes their browser before reaching the success page.
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
    payment = Payment.objects.filter(stripe_session_id=session.get("id")).first()
    if payment is not None:
        if event["type"] in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
            if session.get("payment_status") == "paid":
                payment.mark_paid(session.get("payment_intent") or "")
        elif event["type"] in ("checkout.session.expired", "checkout.session.async_payment_failed"):
            payment.mark_failed()

    return HttpResponse(status=200)
