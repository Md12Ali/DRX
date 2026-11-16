"""Admin configuration for lesson packages and purchases."""
from django.contrib import admin

from .models import LessonPackage, PackagePurchase


@admin.register(LessonPackage)
class LessonPackageAdmin(admin.ModelAdmin):
    list_display = ("name", "hours", "price_display", "per_hour_display", "is_popular", "is_active", "order")
    list_editable = ("is_popular", "is_active", "order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(PackagePurchase)
class PackagePurchaseAdmin(admin.ModelAdmin):
    list_display = ("learner", "package", "hours", "price_display", "status", "created_on", "paid_on")
    list_filter = ("status", "package")
    search_fields = ("learner__username", "learner__email", "stripe_session_id")
    readonly_fields = ("stripe_session_id", "stripe_payment_intent", "created_on", "paid_on")
