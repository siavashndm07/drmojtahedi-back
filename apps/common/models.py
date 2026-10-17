from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ContentStatus(models.TextChoices):
    PUBLISHED = "published", "منتشر"
    DRAFT = "draft", "پیش‌نویس"
    PLACEHOLDER = "placeholder", "جایگزین"
    COMING_SOON = "coming-soon", "به‌زودی"


class SluggedContentModel(TimeStampedModel):
    slug = models.SlugField(max_length=160, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=ContentStatus.choices,
        default=ContentStatus.PUBLISHED,
    )
    source = models.CharField(max_length=255, blank=True)

    class Meta:
        abstract = True
        ordering = ["-updated_at"]
