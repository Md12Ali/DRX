"""Refunding cancelled lessons through Stripe."""
import logging

import stripe
from django.conf import settings

logger = logging.getLogger(__name__)


def refund_booking(booking):
    """
    Refund a cancelled booking's payment in full.

    Returns True if Stripe accepted the refund (or there was nothing to
    refund). Returns False if it failed, in which case the payment is
    flagged so the office can refund it by hand.
    """
    payment = getattr(booking, "payment", None)
    if payment is None or payment.status != payment.Status.PAID:
        return True

    if not settings.STRIPE_SECRET_KEY or not payment.stripe_payment_intent:
        payment.status = payment.Status.REFUND_FAILED
        payment.save(update_fields=["status"])
        return False

    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        stripe.Refund.create(payment_intent=payment.stripe_payment_intent)
    except stripe.StripeError as error:
        logger.warning("Refund failed for %s: %s", booking.reference, error)
        payment.status = payment.Status.REFUND_FAILED
        payment.save(update_fields=["status"])
        return False

    payment.status = payment.Status.REFUNDED
    payment.save(update_fields=["status"])
    return True
