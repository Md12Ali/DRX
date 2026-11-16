"""One place that talks to Stripe Checkout, used by lessons and packages."""
import time

import stripe
from django.conf import settings

# Stripe Checkout sessions must stay open for at least 30 minutes.
CHECKOUT_SESSION_MINUTES = 30


def stripe_ready():
    """True if the secret key needed to talk to Stripe is configured."""
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return bool(settings.STRIPE_SECRET_KEY)


def create_checkout_session(*, name, description, amount_pence, email, reference,
                            client_reference_id, success_url, cancel_url):
    """
    Create a one-off Stripe Checkout payment and return the session.
    Raises stripe.StripeError if Stripe can't be reached.
    """
    return stripe.checkout.Session.create(
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": settings.STRIPE_CURRENCY,
                "unit_amount": amount_pence,
                "product_data": {"name": name, "description": description},
            },
            "quantity": 1,
        }],
        customer_email=email or None,
        client_reference_id=str(client_reference_id),
        metadata={"reference": reference},
        expires_at=int(time.time()) + CHECKOUT_SESSION_MINUTES * 60,
        success_url=f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=cancel_url,
    )
