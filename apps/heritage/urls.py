from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.heritage.views import (
    AdminPersonViewSet,
    AdminPlaceViewSet,
    AdminTimelineViewSet,
    PublicPersonViewSet,
    PublicPlaceViewSet,
    TimelineViewSet,
)

public = DefaultRouter()
public.register("people", PublicPersonViewSet, basename="people")
public.register("places", PublicPlaceViewSet, basename="places")
public.register("timeline", TimelineViewSet, basename="timeline")

admin_router = DefaultRouter()
admin_router.register("people", AdminPersonViewSet, basename="admin-people")
admin_router.register("places", AdminPlaceViewSet, basename="admin-places")
admin_router.register("timeline", AdminTimelineViewSet, basename="admin-timeline")

urlpatterns = [
    path("", include(public.urls)),
    path("admin/", include(admin_router.urls)),
]
