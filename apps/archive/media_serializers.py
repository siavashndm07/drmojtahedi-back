from rest_framework import serializers

from apps.archive.media_utils import (
    asset_absolute_url,
    normalize_media_kind,
    to_webp_upload,
)
from apps.archive.models import MediaAsset


class MediaAssetSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    altText = serializers.CharField(source="alt_text", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = MediaAsset
        fields = ("id", "kind", "url", "altText", "createdAt")

    def get_url(self, obj: MediaAsset) -> str:
        return asset_absolute_url(obj, self.context.get("request"))


class MediaAssetUploadSerializer(serializers.ModelSerializer):
    kind = serializers.CharField(required=False, allow_blank=True, default="news")
    altText = serializers.CharField(
        source="alt_text", required=False, allow_blank=True, default=""
    )

    class Meta:
        model = MediaAsset
        fields = ("file", "kind", "alt_text", "altText")
        extra_kwargs = {
            "alt_text": {"required": False, "allow_blank": True},
        }

    def validate_kind(self, value: str) -> str:
        return normalize_media_kind(value)

    def validate_file(self, value):
        kind = normalize_media_kind(self.initial_data.get("kind"))
        try:
            return to_webp_upload(value, kind=kind)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def create(self, validated_data):
        kind = normalize_media_kind(validated_data.pop("kind", None))
        alt_text = validated_data.get("alt_text", "")
        asset = MediaAsset(kind=kind, alt_text=alt_text, alt=alt_text)
        uploaded = validated_data["file"]
        asset.file.save(uploaded.name, uploaded, save=True)
        return asset

    def to_representation(self, instance):
        return MediaAssetSerializer(instance, context=self.context).data
