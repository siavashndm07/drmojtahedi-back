import uuid
from pathlib import Path

from django.db import models

from apps.archive.media_utils import DEFAULT_MEDIA_KIND, MEDIA_KINDS, media_upload_to
from apps.common.models import SluggedContentModel, TimeStampedModel


class ArchiveItem(SluggedContentModel):
    type = models.CharField(max_length=40, default="document")
    date_label = models.CharField(max_length=80, blank=True)
    creator = models.CharField(max_length=255, blank=True)
    collection = models.CharField(max_length=255, blank=True)


class OralHistoryInterview(SluggedContentModel):
    subtitle = models.CharField(max_length=255, blank=True)
    year = models.CharField(max_length=40, blank=True)
    duration_label = models.CharField(max_length=80, blank=True)
    narrator = models.CharField(max_length=255, blank=True)
    collection = models.CharField(max_length=255, blank=True)
    transcript_excerpt = models.TextField(blank=True)
    audio_src = models.URLField(blank=True)
    related_href = models.CharField(max_length=255, blank=True)
    related_label = models.CharField(max_length=120, blank=True)


def gallery_video_upload_to(instance, filename: str) -> str:
    ext = Path(filename or "").suffix.lower()
    if ext not in {".mp4", ".webm", ".mov"}:
        ext = ".mp4"
    return f"gallery/videos/{uuid.uuid4()}{ext}"


class Gallery(TimeStampedModel):
    """A titled album of images or videos, e.g. «تصاویر همایش»."""

    class Kind(models.TextChoices):
        IMAGES = "images", "تصاویر"
        VIDEOS = "videos", "ویدئو"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=180, unique=True, blank=True, allow_unicode=True)
    description = models.TextField(blank=True)
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.IMAGES)
    cover = models.ForeignKey(
        "MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gallery_covers",
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "-id"]
        verbose_name = "گالری"
        verbose_name_plural = "گالری‌ها"

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify

            base = slugify(self.title, allow_unicode=True) or "gallery"
            slug = base[:170]
            n = 1
            while Gallery.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                suffix = f"-{n}"
                slug = f"{base[:170 - len(suffix)]}{suffix}"
            self.slug = slug
        super().save(*args, **kwargs)


class GalleryItem(TimeStampedModel):
    gallery = models.ForeignKey(
        Gallery, on_delete=models.CASCADE, related_name="items"
    )
    caption = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    image = models.ForeignKey(
        "MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gallery_items",
    )
    video = models.FileField(upload_to=gallery_video_upload_to, blank=True)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "رسانه گالری"
        verbose_name_plural = "رسانه‌های گالری"

    def delete(self, *args, **kwargs):
        if self.video:
            self.video.delete(save=False)
        super().delete(*args, **kwargs)


class MediaAsset(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kind = models.CharField(
        max_length=32,
        choices=MEDIA_KINDS,
        default=DEFAULT_MEDIA_KIND,
        db_index=True,
    )
    file = models.ImageField(upload_to=media_upload_to, blank=True)
    src = models.CharField(max_length=500, blank=True)
    alt = models.CharField(max_length=255, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.kind}/{self.id}"

    @property
    def display_alt(self) -> str:
        return self.alt_text or self.alt or ""
