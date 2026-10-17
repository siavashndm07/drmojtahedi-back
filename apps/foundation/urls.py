from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.foundation.ai_views import (
    AdminOpsAiTestView,
    PublicAiChatConfigView,
    PublicAiChatView,
)
from apps.foundation.settings_views import (
    AdminOpsSettingsView,
    AdminSiteSettingsView,
    AdminStaffPermissionMetaView,
    AdminStaffViewSet,
    PublicSiteSettingsView,
)
from apps.foundation.views import (
    AdminHeroSlideViewSet,
    AdminOrganMemberViewSet,
    AdminProjectViewSet,
    AdminSponsorViewSet,
    AdminUsefulLinkViewSet,
    CollaborateViewSet,
    HeroSlideViewSet,
    OrganMemberViewSet,
    ProjectViewSet,
    PublicSponsorViewSet,
    PublicUsefulLinkViewSet,
)

public = DefaultRouter()
public.register("projects", ProjectViewSet, basename="projects")
public.register("sponsors", PublicSponsorViewSet, basename="sponsors")
public.register("collaborate", CollaborateViewSet, basename="collaborate")
public.register("useful-links", PublicUsefulLinkViewSet, basename="useful-links")
public.register("hero-slides", HeroSlideViewSet, basename="hero-slides")

admin_router = DefaultRouter()
admin_router.register("sponsors", AdminSponsorViewSet, basename="admin-sponsors")
admin_router.register("projects", AdminProjectViewSet, basename="admin-projects")
admin_router.register("organs", AdminOrganMemberViewSet, basename="admin-organs")
admin_router.register("useful-links", AdminUsefulLinkViewSet, basename="admin-useful-links")
admin_router.register("staff", AdminStaffViewSet, basename="admin-staff")
admin_router.register("hero-slides", AdminHeroSlideViewSet, basename="admin-hero-slides")

organs_list = OrganMemberViewSet.as_view({"get": "list"})
organs_detail = OrganMemberViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    path("", include(public.urls)),
    path("foundation/organs/", organs_list, name="organs-list"),
    path("foundation/organs/<int:pk>/", organs_detail, name="organs-detail"),
    path("site/", PublicSiteSettingsView.as_view(), name="public-site-settings"),
    path("ai/chat/config/", PublicAiChatConfigView.as_view(), name="ai-chat-config"),
    path("ai/chat/", PublicAiChatView.as_view(), name="ai-chat"),
    path("admin/settings/site/", AdminSiteSettingsView.as_view(), name="admin-site-settings"),
    path("admin/settings/ops/", AdminOpsSettingsView.as_view(), name="admin-ops-settings"),
    path(
        "admin/settings/ops/test-ai/",
        AdminOpsAiTestView.as_view(),
        name="admin-ops-test-ai",
    ),
    path(
        "admin/staff/permission-meta/",
        AdminStaffPermissionMetaView.as_view(),
        name="admin-staff-permission-meta",
    ),
    path("admin/", include(admin_router.urls)),
]
