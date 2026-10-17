from django.contrib import admin
from apps.accounts.models import (
    MemberProfile,
    MembershipFeePayment,
    MembershipTier,
    OtpChallenge,
)


@admin.register(MembershipTier)
class MembershipTierAdmin(admin.ModelAdmin):
    list_display = ("title", "annual_fee_rials", "sort_order", "is_active")
    list_editable = ("annual_fee_rials", "sort_order", "is_active")
    search_fields = ("title",)


@admin.register(MemberProfile)
class MemberProfileAdmin(admin.ModelAdmin):
    list_display = (
        "phone",
        "first_name",
        "last_name",
        "membership_tier",
        "membership_status",
        "created_at",
    )
    list_filter = ("membership_tier", "membership_status")
    search_fields = ("phone", "first_name", "last_name")
    raw_id_fields = ("membership_tier",)


@admin.register(MembershipFeePayment)
class MembershipFeePaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "member",
        "tier_title",
        "amount",
        "method",
        "status",
        "period_year",
        "created_at",
    )
    list_filter = ("status", "method", "period_year")
    search_fields = ("member__phone", "tier_title", "transaction_id")
    raw_id_fields = ("member", "tier")


@admin.register(OtpChallenge)
class OtpChallengeAdmin(admin.ModelAdmin):
    list_display = ("phone", "code", "consumed", "expires_at", "created_at")
