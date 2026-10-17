from rest_framework import serializers

from apps.archive.media_utils import absolute_media_url, asset_absolute_url
from apps.archive.models import MediaAsset
from apps.content.models import (
    Article,
    ArticleCategory,
    LibraryItem,
    NewsCategory,
    NewsItem,
)


class NewsCategorySerializer(serializers.ModelSerializer):
    isActive = serializers.BooleanField(source="is_active", required=False)
    sortOrder = serializers.IntegerField(source="sort_order", required=False)

    class Meta:
        model = NewsCategory
        fields = (
            "id",
            "slug",
            "title",
            "description",
            "sort_order",
            "sortOrder",
            "is_active",
            "isActive",
            "created_at",
            "updated_at",
        )


class ArticleCategorySerializer(serializers.ModelSerializer):
    isActive = serializers.BooleanField(source="is_active", required=False)
    sortOrder = serializers.IntegerField(source="sort_order", required=False)

    class Meta:
        model = ArticleCategory
        fields = (
            "id",
            "slug",
            "title",
            "description",
            "sort_order",
            "sortOrder",
            "is_active",
            "isActive",
            "created_at",
            "updated_at",
        )


def cover_url_for(item, request=None) -> str:
    if getattr(item, "cover_image_id", None):
        url = asset_absolute_url(item.cover_image, request)
        if url:
            return url
    return absolute_media_url(getattr(item, "cover", "") or "", request)


def _resolve_media_asset(value):
    if value is None:
        return None
    asset = MediaAsset.objects.filter(pk=value).first()
    if not asset:
        raise serializers.ValidationError("فایل رسانه یافت نشد.")
    return asset


class NewsItemSerializer(serializers.ModelSerializer):
    dateLabel = serializers.CharField(source="date_label", required=False, allow_blank=True)
    coverTone = serializers.CharField(source="cover_tone", required=False, allow_blank=True)
    publishedAt = serializers.DateTimeField(
        source="published_at", required=False, allow_null=True
    )
    blocks = serializers.JSONField(required=False)
    tags = serializers.JSONField(required=False)
    coverImageId = serializers.UUIDField(
        source="cover_image_id",
        required=False,
        allow_null=True,
    )
    cover = serializers.SerializerMethodField()
    heroImage = serializers.SerializerMethodField()

    class Meta:
        model = NewsItem
        fields = (
            "id",
            "slug",
            "title",
            "description",
            "status",
            "source",
            "category",
            "body",
            "blocks",
            "tags",
            "author",
            "date_label",
            "dateLabel",
            "published_at",
            "publishedAt",
            "cover_tone",
            "coverTone",
            "cover",
            "coverImageId",
            "heroImage",
            "created_at",
            "updated_at",
        )

    def get_cover(self, obj: NewsItem) -> str:
        return cover_url_for(obj, self.context.get("request"))

    def get_heroImage(self, obj: NewsItem):
        url = cover_url_for(obj, self.context.get("request"))
        if not url:
            return None
        alt = ""
        if obj.cover_image_id:
            alt = obj.cover_image.display_alt
        return {
            "id": str(obj.cover_image_id) if obj.cover_image_id else None,
            "src": url,
            "alt": alt or obj.title,
        }

    def validate_cover_image_id(self, value):
        if value is None:
            return None
        _resolve_media_asset(value)
        return value


class ArticleSerializer(serializers.ModelSerializer):
    dateLabel = serializers.CharField(source="date_label", required=False, allow_blank=True)
    coverTone = serializers.CharField(source="cover_tone", required=False, allow_blank=True)
    publishedAt = serializers.DateTimeField(
        source="published_at", required=False, allow_null=True
    )
    readingTimeMinutes = serializers.IntegerField(
        source="reading_time_minutes", required=False, allow_null=True
    )
    blocks = serializers.JSONField(required=False)
    tags = serializers.JSONField(required=False)
    coverImageId = serializers.UUIDField(
        source="cover_image_id",
        required=False,
        allow_null=True,
    )
    cover = serializers.SerializerMethodField()
    heroImage = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = (
            "id",
            "slug",
            "title",
            "subtitle",
            "description",
            "status",
            "source",
            "category",
            "body",
            "blocks",
            "tags",
            "author",
            "date_label",
            "dateLabel",
            "published_at",
            "publishedAt",
            "reading_time_minutes",
            "readingTimeMinutes",
            "cover_tone",
            "coverTone",
            "cover",
            "coverImageId",
            "heroImage",
            "created_at",
            "updated_at",
        )

    def get_cover(self, obj: Article) -> str:
        return cover_url_for(obj, self.context.get("request"))

    def get_heroImage(self, obj: Article):
        url = cover_url_for(obj, self.context.get("request"))
        if not url:
            return None
        alt = ""
        if obj.cover_image_id:
            alt = obj.cover_image.display_alt
        return {
            "id": str(obj.cover_image_id) if obj.cover_image_id else None,
            "src": url,
            "alt": alt or obj.title,
        }

    def validate_cover_image_id(self, value):
        if value is None:
            return None
        _resolve_media_asset(value)
        return value


class LibraryItemSerializer(serializers.ModelSerializer):
    itemType = serializers.CharField(source="item_type", required=False, allow_blank=True)
    tags = serializers.JSONField(required=False)
    coverImageId = serializers.UUIDField(
        source="cover_image_id",
        required=False,
        allow_null=True,
    )
    cover = serializers.SerializerMethodField()
    heroImage = serializers.SerializerMethodField()

    class Meta:
        model = LibraryItem
        fields = (
            "id",
            "slug",
            "title",
            "description",
            "status",
            "source",
            "author",
            "year",
            "item_type",
            "itemType",
            "tags",
            "cover",
            "coverImageId",
            "heroImage",
            "created_at",
            "updated_at",
        )

    def get_cover(self, obj: LibraryItem) -> str:
        return cover_url_for(obj, self.context.get("request"))

    def get_heroImage(self, obj: LibraryItem):
        url = cover_url_for(obj, self.context.get("request"))
        if not url:
            return None
        alt = ""
        if obj.cover_image_id:
            alt = obj.cover_image.display_alt
        return {
            "id": str(obj.cover_image_id) if obj.cover_image_id else None,
            "src": url,
            "alt": alt or obj.title,
        }

    def validate_cover_image_id(self, value):
        if value is None:
            return None
        _resolve_media_asset(value)
        return value
