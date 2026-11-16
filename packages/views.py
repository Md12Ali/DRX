"""Prices page and buying lesson packages through Stripe."""
import logging

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from payments.stripe_client import create_checkout_session, stripe_ready

from .models import LessonPackage, PackagePurchase, hours_display, package_minutes_balance

logger = logging.getLogger(__name__)


def package_list(request):
    """Pay-as-you-go price, every active package, and the learner's balance."""
    context = {
        "packages": LessonPackage.objects.filter(is_active=True),
        "hourly_rate": f"£{settings.STANDARD_HOURLY_RATE_PENCE / 100:.0f}",
        "payg_prices": [
            (label, f"£{settings.STANDARD_HOURLY_RATE_PENCE * minutes / 60 / 100:.2f}")
            for minutes, label in ((60, "1 hour"), (90, "1.5 hours"), (120, "2 hours"))
        ],
    }
    if request.user.is_authenticated:
        context["balance_hours"] = hours_display(package_minutes_balance(request.user))
        context["purchases"] = request.user.package_purchases.select_related("package").exclude(
            status=PackagePurchase.Status.PENDING
        )[:10]
    return render(request, "packages/package_list.html", context)


@login_required
@require_POST
def buy_package(request, slug):
    """Create a pending purchase and send the learner to Stripe Checkout."""
    package = get_object_or_404(LessonPackage, slug=slug, is_active=True)

    if hasattr(request.user, "instructor"):
        messages.info(request, "Instructor accounts can't buy packages.")
        return redirect("packages:list")
    if not stripe_ready():
        messages.error(request, "Card payments are not available right now. You have not been charged.")
        return redirect("packages:list")

    purchase = PackagePurchase.objects.create(
        learner=request.user, package=package, hours=package.hours, price_pence=package.price_pence
    )
    try:
        session = create_checkout_session(
            name=f"{package.name} package: {package.hours} hours of driving lessons",
            description=f"{package.per_hour_display} per hour. Book lessons with your hours any time.",
            amount_pence=package.price_pence,
            email=request.user.email,
            reference=f"PKG-{purchase.pk:05d}",
            client_reference_id=purchase.pk,
            success_url=request.build_absolute_uri(reverse("packages:success")),
            cancel_url=request.build_absolute_uri(reverse("packages:cancelled", args=[purchase.pk])),
        )
    except stripe.StripeError as error:
        logger.warning("Stripe checkout failed for package purchase %s: %s", purchase.pk, error)
        purchase.mark_failed()
        messages.error(
            request,
            "We couldn't reach our payment provider. You have not been charged. Please try again.",
        )
        return redirect("packages:list")

    purchase.stripe_session_id = session.id
    purchase.save(update_fields=["stripe_session_id"])
    return redirect(session.url)


@login_required
def purchase_success(request):
    """Stripe sends the learner here after paying. Verify with Stripe first."""
    session_id = request.GET.get("session_id", "")
    purchase = (
        PackagePurchase.objects.select_related("package")
        .filter(stripe_session_id=session_id, learner=request.user)
        .first()
    )
    if not session_id or purchase is None:
        messages.error(request, "We couldn't find that payment.")
        return redirect("packages:list")

    if purchase.status != PackagePurchase.Status.PAID:
        if not stripe_ready():
            messages.error(request, "Card payments are not available right now.")
            return redirect("packages:list")
        try:
            session = stripe.checkout.Session.retrieve(session_id)
        except stripe.StripeError as error:
            logger.warning("Stripe lookup failed for %s: %s", session_id, error)
            messages.warning(
                request,
                "We couldn't confirm your payment yet. If you were charged, your hours "
                "will appear within a few minutes.",
            )
            return redirect("packages:list")
        if session.payment_status != "paid":
            messages.warning(request, "Your payment hasn't gone through yet.")
            return redirect("packages:list")
        purchase.mark_paid(getattr(session, "payment_intent", "") or "")

    messages.success(request, f"Payment of {purchase.price_display} received. {purchase.hours} hours added!")
    context = {
        "purchase": purchase,
        "balance_hours": hours_display(package_minutes_balance(request.user)),
    }
    return render(request, "packages/success.html", context)


@login_required
def purchase_cancelled(request, pk):
    """Stripe sends the learner here if they leave the checkout page."""
    purchase = get_object_or_404(PackagePurchase, pk=pk, learner=request.user)
    purchase.mark_failed()
    messages.info(request, "Payment cancelled. You have not been charged.")
    return redirect("packages:list")
