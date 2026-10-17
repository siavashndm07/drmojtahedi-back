from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.engagement.analytics_views import SiteVisitCreateView
from apps.engagement.donation_views import (
    AdminDonationGoalViewSet,
    PublicDonatePaymentOptionsView,
    PublicDonateStartView,
)
from apps.engagement.views import (
    AdminContributionViewSet,
    AdminDonationViewSet,
    AdminNewsletterViewSet,
    ContactCreateView,
    ContributionCreateView,
    NewsletterSubscribeView,
)

admin_router = DefaultRouter()
admin_router.register("newsletter", AdminNewsletterViewSet, basename="admin-newsletter")
admin_router.register("contributions", AdminContributionViewSet, basename="admin-contributions")
admin_router.register("donations", AdminDonationViewSet, basename="admin-donations")
admin_router.register(
    "donation-goals",
    AdminDonationGoalViewSet,
    basename="admin-donation-goals",
)

urlpatterns = [
    path("newsletter/", NewsletterSubscribeView.as_view()),
    path("contribute/", ContributionCreateView.as_view()),
    path("contact/", ContactCreateView.as_view()),
    path("analytics/visit/", SiteVisitCreateView.as_view(), name="analytics-visit"),
    path(
        "donate/payment-options/",
        PublicDonatePaymentOptionsView.as_view(),
        name="donate-payment-options",
    ),
    path("donate/start/", PublicDonateStartView.as_view(), name="donate-start"),
    path("admin/", include(admin_router.urls)),
]
