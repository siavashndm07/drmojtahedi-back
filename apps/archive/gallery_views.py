from __future__ import annotations

from pathlib import Path

from django.http import Http404
from rest_framework import serializers, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsStaffUser
from apps.archive.media_utils import asset_absolute_url, to_webp_upload
from apps.archive.models import Gallery, GalleryItem, MediaAsset

MAX_VIDEO_BYTES = 250 * 1024 * 1024
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov"}
VIDEO_CONTENT_TYPES = {
    "video/mp4",
    "video/webm",
    "video/quicktime",
    "application/octet-stream",
}


def serialize_item(item: GalleryItem, request) -> dict:
    url = ""
    if item.image_id:
        url = asset_absolute_url(item.image, request)
    elif item.video:
        from apps.archive.media_utils import absolute_media_url

        url = absolute_media_url(item.video.url, request)
    return {
        "id": item.id,
        "caption": item.caption or "",
        "sortOrder": item.sort_order,
        "url": url,
    }


def serialize_gallery(gallery: Gallery, request, *, include_items: bool) -> dict:
    items = list(gallery.items.select_related("image").all())
    cover = asset_absolute_url(gallery.cover, request) if gallery.cover_id else ""
    if not cover:
        for item in items:
            if item.image_id:
                cover = asset_absolute_url(item.image, request)
                if cover:
                    break
    data = {
        "id": gallery.id,
        "title": gallery.title,
        "slug": gallery.slug,
        "description": gallery.description or "",
        "kind": gallery.kind,
        "sortOrder": gallery.sort_order,
        "isActive": gallery.is_active,
        "coverId": str(gallery.cover_id) if gallery.cover_id else None,
        "coverUrl": cover,
        "itemCount": len(items),
    }
    if include_items:
        data["items"] = [serialize_item(item, request) for item in items]
    return data


class GalleryWriteSerializer(serializers.ModelSerializer):
    sortOrder = serializers.IntegerField(source="sort_order", required=False)
    isActive = serializers.BooleanField(source="is_active", required=False)
    coverId = serializers.UUIDField(source="cover_id", required=False, allow_null=True)

    class Meta:
        model = Gallery
        fields = (
            "title",
            "description",
            "kind",
            "slug",
            "sortOrder",
            "isActive",
            "coverId",
        )
        extra_kwargs = {
            "slug": {"required": False, "allow_blank": True},
            "description": {"required": False, "allow_blank": True},
        }

    def validate_cover_id(self, value):
        if value is None:
            return None
        if not MediaAsset.objects.filter(pk=value).exists():
            raise serializers.ValidationError("تصویر جلد پیدا نشد.")
        return value

    def validate_kind(self, value):
        if value not in {Gallery.Kind.IMAGES, Gallery.Kind.VIDEOS}:
            raise serializers.ValidationError("نوع گالری نامعتبر است.")
        return value


class PublicGalleryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Gallery.objects.filter(is_active=True).prefetch_related("items__image")
    permission_classes = [AllowAny]
    lookup_field = "slug"
    pagination_class = None

    def get_object(self):
        key = str(self.kwargs.get(self.lookup_field) or "")
        queryset = self.filter_queryset(self.get_queryset())
        if key.isdigit():
            gallery = queryset.filter(pk=int(key)).first()
        else:
            gallery = queryset.filter(slug=key).first()
        if gallery is None:
            raise Http404
        return gallery

    def list(self, request, *args, **kwargs):
        rows = self.get_queryset()
        return Response(
            [serialize_gallery(row, request, include_items=False) for row in rows]
        )

    def retrieve(self, request, *args, **kwargs):
        gallery = self.get_object()
        return Response(serialize_gallery(gallery, request, include_items=True))


class AdminGalleryViewSet(viewsets.ModelViewSet):
    queryset = Gallery.objects.all().prefetch_related("items__image", "cover")
    serializer_class = GalleryWriteSerializer
    permission_classes = [IsStaffUser]
    pagination_class = None
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def list(self, request, *args, **kwargs):
        return Response(
            [
                serialize_gallery(row, request, include_items=True)
                for row in self.get_queryset()
            ]
        )

    def retrieve(self, request, *args, **kwargs):
        return Response(
            serialize_gallery(self.get_object(), request, include_items=True)
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        gallery = serializer.save()
        return Response(
            serialize_gallery(gallery, request, include_items=True),
            status=201,
        )

    def partial_update(self, request, *args, **kwargs):
        gallery = self.get_object()
        serializer = self.get_serializer(gallery, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if (
            "kind" in serializer.validated_data
            and serializer.validated_data["kind"] != gallery.kind
            and gallery.items.exists()
        ):
            return Response(
                {"detail": "تا وقتی رسانه‌ای در گالری هست، نوع آن را عوض نکنید."},
                status=400,
            )
        gallery = serializer.save()
        return Response(serialize_gallery(gallery, request, include_items=True))

    def destroy(self, request, *args, **kwargs):
        gallery = self.get_object()
        for item in gallery.items.all():
            item.delete()
        gallery.delete()
        return Response(status=204)


class AdminGalleryItemUploadView(APIView):
    permission_classes = [IsStaffUser]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, gallery_id: int):
        gallery = Gallery.objects.filter(pk=gallery_id).first()
        if not gallery:
            return Response({"detail": "گالری پیدا نشد."}, status=404)
        uploaded = request.FILES.get("file")
        if not uploaded:
            return Response({"detail": "فایل الزامی است."}, status=400)
        caption = str(request.data.get("caption") or "").strip()[:255]
        next_order = gallery.items.count()

        if gallery.kind == Gallery.Kind.IMAGES:
            try:
                webp = to_webp_upload(uploaded, kind="gallery")
            except ValueError as exc:
                return Response({"detail": str(exc)}, status=400)
            asset = MediaAsset(kind="gallery", alt_text=caption, alt=caption)
            asset.file.save(webp.name, webp, save=True)
            item = GalleryItem.objects.create(
                gallery=gallery,
                caption=caption,
                sort_order=next_order,
                image=asset,
            )
            if not gallery.cover_id:
                gallery.cover = asset
                gallery.save(update_fields=["cover", "updated_at"])
        else:
            name = Path(uploaded.name or "").name
            ext = Path(name).suffix.lower()
            content_type = (uploaded.content_type or "").lower()
            if ext not in VIDEO_EXTENSIONS and content_type not in VIDEO_CONTENT_TYPES:
                return Response(
                    {"detail": "فقط ویدئوی mp4، webm یا mov پذیرفته می‌شود."},
                    status=400,
                )
            if uploaded.size and uploaded.size > MAX_VIDEO_BYTES:
                return Response(
                    {"detail": "حجم ویدئو بیشتر از ۲۵۰ مگابایت است."},
                    status=400,
                )
            item = GalleryItem(
                gallery=gallery,
                caption=caption,
                sort_order=next_order,
            )
            item.video.save(name, uploaded, save=True)

        gallery.refresh_from_db()
        return Response(
            serialize_gallery(gallery, request, include_items=True),
            status=201,
        )


class AdminGalleryItemDeleteView(APIView):
    permission_classes = [IsStaffUser]

    def delete(self, request, gallery_id: int, item_id: int):
        item = (
            GalleryItem.objects.select_related("gallery")
            .filter(pk=item_id, gallery_id=gallery_id)
            .first()
        )
        if not item:
            return Response({"detail": "رسانه پیدا نشد."}, status=404)
        gallery = item.gallery
        item.delete()
        return Response(serialize_gallery(gallery, request, include_items=True))
