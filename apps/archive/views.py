from rest_framework import serializers, viewsets
from rest_framework.permissions import AllowAny

from apps.accounts.permissions import IsStaffUser
from apps.archive.media_serializers import MediaAssetSerializer
from apps.archive.media_utils import asset_absolute_url
from apps.archive.models import ArchiveItem, MediaAsset, OralHistoryInterview
from apps.archive.serializers import ArchiveItemSerializer, OralHistorySerializer


class PublicArchiveViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ArchiveItem.objects.exclude(status="draft")
    serializer_class = ArchiveItemSerializer
    lookup_field = "slug"
    permission_classes = [AllowAny]


class AdminArchiveViewSet(viewsets.ModelViewSet):
    queryset = ArchiveItem.objects.all()
    serializer_class = ArchiveItemSerializer
    permission_classes = [IsStaffUser]


class OralHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OralHistoryInterview.objects.exclude(status="draft")
    serializer_class = OralHistorySerializer
    lookup_field = "slug"
    permission_classes = [AllowAny]


class AdminOralHistoryViewSet(viewsets.ModelViewSet):
    queryset = OralHistoryInterview.objects.all()
    serializer_class = OralHistorySerializer
    permission_classes = [IsStaffUser]


class AdminMediaAssetSerializer(MediaAssetSerializer):
    altText = serializers.CharField(
        source="alt_text", required=False, allow_blank=True
    )
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    url = serializers.SerializerMethodField()

    class Meta(MediaAssetSerializer.Meta):
        fields = ("id", "kind", "url", "altText", "createdAt", "src", "alt")
        read_only_fields = ("id", "kind", "url", "createdAt", "src")

    def get_url(self, obj: MediaAsset) -> str:
        return asset_absolute_url(obj, self.context.get("request")) or obj.src or ""

    def update(self, instance, validated_data):
        alt_text = validated_data.get("alt_text")
        if alt_text is not None:
            instance.alt_text = alt_text
            instance.alt = alt_text
        instance.save()
        return instance


class AdminMediaAssetViewSet(viewsets.ModelViewSet):
    queryset = MediaAsset.objects.all()
    serializer_class = AdminMediaAssetSerializer
    permission_classes = [IsStaffUser]
    http_method_names = ["get", "patch", "delete", "head", "options"]
