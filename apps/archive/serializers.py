from rest_framework import serializers
from apps.archive.models import ArchiveItem, OralHistoryInterview


class ArchiveItemSerializer(serializers.ModelSerializer):
    dateLabel = serializers.CharField(source="date_label", required=False, allow_blank=True)

    class Meta:
        model = ArchiveItem
        fields = (
            "id",
            "slug",
            "title",
            "description",
            "status",
            "source",
            "type",
            "date_label",
            "dateLabel",
            "creator",
            "collection",
            "created_at",
            "updated_at",
        )


class OralHistorySerializer(serializers.ModelSerializer):
    durationLabel = serializers.CharField(source="duration_label", required=False, allow_blank=True)
    transcriptExcerpt = serializers.CharField(
        source="transcript_excerpt", required=False, allow_blank=True
    )
    audioSrc = serializers.CharField(source="audio_src", required=False, allow_blank=True)
    relatedHref = serializers.CharField(source="related_href", required=False, allow_blank=True)
    relatedLabel = serializers.CharField(source="related_label", required=False, allow_blank=True)

    class Meta:
        model = OralHistoryInterview
        fields = (
            "id",
            "slug",
            "title",
            "description",
            "status",
            "source",
            "subtitle",
            "year",
            "duration_label",
            "durationLabel",
            "narrator",
            "collection",
            "transcript_excerpt",
            "transcriptExcerpt",
            "audio_src",
            "audioSrc",
            "related_href",
            "relatedHref",
            "related_label",
            "relatedLabel",
            "created_at",
            "updated_at",
        )

