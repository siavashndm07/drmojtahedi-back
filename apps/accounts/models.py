from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.common.models import TimeStampedModel


class MembershipTier(TimeStampedModel):
    """Foundation organ / membership role with yearly fee (ارکان / نوع عضویت)."""

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    annual_fee_rials = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "نوع عضویت"
        verbose_name_plural = "انواع عضویت"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title, allow_unicode=True) or f"tier-{self.pk or 'new'}"
            slug = base
            n = 1
            while MembershipTier.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f"{base}-{n}"
            self.slug = slug
        super().save(*args, **kwargs)


class MemberProfile(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="member_profile",
        null=True,
        blank=True,
    )
    phone = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=80, blank=True)
    last_name = models.CharField(max_length=80, blank=True)
    education = models.CharField(max_length=40, blank=True)
    city = models.CharField(max_length=80, blank=True)
    membership_tier = models.ForeignKey(
        MembershipTier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members",
    )
    membership_type = models.CharField(max_length=255, blank=True)
    membership_number = models.CharField(max_length=40, blank=True)
    membership_status = models.CharField(
        max_length=20,
        default="pending",
        blank=True,
    )
    membership_valid_until = models.DateField(null=True, blank=True)
    annual_fee_rials = models.PositiveIntegerField(default=0)
    email = models.EmailField(blank=True)
    national_id = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    how_met = models.CharField(max_length=40, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.CharField(max_length=45, blank=True)

    def __str__(self):
        return self.phone

    def resolve_annual_fee(self) -> int:
        if self.membership_tier_id:
            return int(self.membership_tier.annual_fee_rials or 0)
        return int(self.annual_fee_rials or 0)

    def sync_tier_fields(self):
        if self.membership_tier_id:
            self.membership_type = self.membership_tier.title
            self.annual_fee_rials = int(self.membership_tier.annual_fee_rials or 0)


class MembershipFeePayment(TimeStampedModel):
    """Yearly membership fee payment history."""

    class Method(models.TextChoices):
        ONLINE = "online", "پرداخت آنلاین"
        CARD_TO_CARD = "card_to_card", "کارت‌به‌کارت"

    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار"
        REDIRECTED = "redirected", "هدایت به درگاه"
        AWAITING_TRANSFER = "awaiting_transfer", "در انتظار واریز"
        PAID = "paid", "پرداخت‌شده"
        CANCELLED = "cancelled", "لغوشده"
        FAILED = "failed", "ناموفق"

    member = models.ForeignKey(
        MemberProfile,
        on_delete=models.CASCADE,
        related_name="fee_payments",
    )
    tier = models.ForeignKey(
        MembershipTier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fee_payments",
    )
    tier_title = models.CharField(max_length=255, blank=True)
    amount = models.PositiveIntegerField(default=0)
    method = models.CharField(
        max_length=20,
        choices=Method.choices,
        default=Method.ONLINE,
    )
    gateway = models.CharField(max_length=16, blank=True)
    authority = models.CharField(max_length=120, blank=True)
    transaction_id = models.CharField(max_length=120, blank=True)
    status = models.CharField(
        max_length=40,
        choices=Status.choices,
        default=Status.PENDING,
    )
    period_year = models.PositiveIntegerField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "پرداخت حق عضویت"
        verbose_name_plural = "پرداخت‌های حق عضویت"

    def __str__(self):
        return f"{self.member_id}:{self.amount}:{self.status}"


class OtpChallenge(TimeStampedModel):
    phone = models.CharField(max_length=20, db_index=True)
    code = models.CharField(max_length=10)
    consumed = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]


class StaffProfile(models.Model):
    """Panel access limits for Django staff users (non-superuser)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="staff_profile",
    )
    permissions = models.JSONField(
        default=list,
        blank=True,
        help_text="لیست کلیدهای دسترسی بخش‌های پنل",
    )
    last_login_ip = models.CharField(max_length=45, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "پروفایل دسترسی پنل"
        verbose_name_plural = "پروفایل‌های دسترسی پنل"

    def __str__(self) -> str:
        return f"دسترسی {self.user.username}"
