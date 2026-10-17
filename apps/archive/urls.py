from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.archive.gallery_views import (
    AdminGalleryItemDeleteView,
    AdminGalleryItemUploadView,
    AdminGalleryViewSet,
    PublicGalleryViewSet,
)
from apps.archive.media_views import MediaUploadView
from apps.archive.views import (
    AdminArchiveViewSet,
    AdminMediaAssetViewSet,
    AdminOralHistoryViewSet,
    OralHistoryViewSet,
    PublicArchiveViewSet,
)

public = DefaultRouter()
public.register("archive", PublicArchiveViewSet, basename="archive")
public.register("galleries", PublicGalleryViewSet, basename="galleries")
public.register("oral-history", OralHistoryViewSet, basename="oral-history")

admin_router = DefaultRouter()
admin_router.register("archive", AdminArchiveViewSet, basename="admin-archive")
admin_router.register(
    "oral-history", AdminOralHistoryViewSet, basename="admin-oral-history"
)
admin_router.register("media", AdminMediaAssetViewSet, basename="admin-media")
admin_router.register("galleries", AdminGalleryViewSet, basename="admin-galleries")

urlpatterns = [
    path("media/upload/", MediaUploadView.as_view(), name="media-upload"),
    path(
        "admin/galleries/<int:gallery_id>/items/",
        AdminGalleryItemUploadView.as_view(),
        name="admin-gallery-item-upload",
    ),
    path(
        "admin/galleries/<int:gallery_id>/items/<int:item_id>/",
        AdminGalleryItemDeleteView.as_view(),
        name="admin-gallery-item-delete",
    ),
    path("", include(public.urls)),
    path("admin/", include(admin_router.urls)),
]
