from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts import views
from apps.accounts.membership_fee_views import (
    AdminMembershipFeePaymentViewSet,
    MemberMembershipFeeListView,
    MemberMembershipFeeStartView,
)

admin_router = DefaultRouter()
admin_router.register("members", views.AdminMemberViewSet, basename="admin-members")
admin_router.register(
    "membership-tiers",
    views.AdminMembershipTierViewSet,
    basename="admin-membership-tiers",
)
admin_router.register(
    "membership-fees",
    AdminMembershipFeePaymentViewSet,
    basename="admin-membership-fees",
)

urlpatterns = [
    path("auth/otp/send/", views.OtpSendView.as_view()),
    path("auth/otp/verify/", views.OtpVerifyView.as_view()),
    path("auth/admin/login/", views.AdminLoginView.as_view()),
    path("auth/admin/refresh/", views.AdminRefreshView.as_view()),
    path("auth/admin/me/", views.AdminMeView.as_view()),
    path("auth/me/", views.MeView.as_view()),
    path(
        "membership-fee/payments/",
        MemberMembershipFeeListView.as_view(),
        name="membership-fee-payments",
    ),
    path(
        "membership-fee/start/",
        MemberMembershipFeeStartView.as_view(),
        name="membership-fee-start",
    ),
    path(
        "membership-tiers/",
        views.PublicMembershipTierListView.as_view(),
        name="membership-tiers",
    ),
    path("admin/dashboard/", views.AdminDashboardView.as_view()),
    path("admin/", include(admin_router.urls)),
]
