from django.db import models

from apps.common.models import SluggedContentModel, TimeStampedModel


class NewsCategory(TimeStampedModel):
    slug = models.SlugField(max_length=80, unique=True)
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title


class ArticleCategory(TimeStampedModel):
    slug = models.SlugField(max_length=80, unique=True)
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title


class NewsItem(SluggedContentModel):
    category = models.CharField(max_length=80, blank=True)
    body = models.TextField(blank=True)
    blocks = models.JSONField(default=list, blank=True)
    tags = models.JSONField(default=list, blank=True)
    author = models.CharField(max_length=120, blank=True)
    date_label = models.CharField(max_length=80, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    cover_tone = models.CharField(max_length=40, blank=True)
    cover = models.CharField(max_length=500, blank=True)
    cover_image = models.ForeignKey(
        "archive_app.MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="news_covers",
    )


class Article(SluggedContentModel):
    subtitle = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=80, blank=True)
    body = models.TextField(blank=True)
    blocks = models.JSONField(default=list, blank=True)
    tags = models.JSONField(default=list, blank=True)
    author = models.CharField(max_length=120, blank=True)
    date_label = models.CharField(max_length=80, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    reading_time_minutes = models.PositiveSmallIntegerField(null=True, blank=True)
    cover_tone = models.CharField(max_length=40, blank=True)
    cover = models.CharField(max_length=500, blank=True)
    cover_image = models.ForeignKey(
        "archive_app.MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="article_covers",
    )


class LibraryItem(SluggedContentModel):
    author = models.CharField(max_length=255, blank=True)
    year = models.CharField(max_length=80, blank=True)
    item_type = models.CharField(max_length=40, blank=True, default="book")
    tags = models.JSONField(default=list, blank=True)
    cover = models.CharField(max_length=500, blank=True)
    cover_image = models.ForeignKey(
        "archive_app.MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="library_covers",
    )
