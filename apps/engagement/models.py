from django.db import models

from apps.common.models import TimeStampedModel
from apps.engagement.analytics_models import (  # noqa: F401
    SiteVisitDaily,
    SiteVisitHit,
    SiteVisitVisitor,
)


class NewsletterSubscriber(TimeStampedModel):
    email = models.EmailField(unique=True)
    active = models.BooleanField(default=True)


class Contribution(TimeStampedModel):
    type = models.CharField(max_length=40, default="memory")
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    title = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(max_length=40, default="new")


class ContactMessage(TimeStampedModel):
    name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()


class DonationGoal(TimeStampedModel):
    """Selectable «هدف کمک» options for the donate form."""

    title = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "هدف کمک"
        verbose_name_plural = "اهداف کمک"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify

            base = slugify(self.title, allow_unicode=True) or f"goal-{self.pk or 'new'}"
            slug = base
            n = 1
            while DonationGoal.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f"{base}-{n}"
            self.slug = slug
        super().save(*args, **kwargs)


class DonationRecord(TimeStampedModel):
    class Method(models.TextChoices):
        ONLINE = "online", "پرداخت آنلاین"
        CARD_TO_CARD = "card_to_card", "کارت‌به‌کارت"

    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار"
        REDIRECTED = "redirected", "هدایت به درگاه"
        AWAITING_TRANSFER = "awaiting_transfer", "در انتظار واریز"
        PAID = "paid", "پرداخت‌شده"
        FAILED = "failed", "ناموفق"

    amount = models.PositiveIntegerField(default=0)
    donor_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    national_id = models.CharField(max_length=20, blank=True)
    goal = models.CharField(max_length=80, blank=True)
    goals = models.JSONField(default=list, blank=True)
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
