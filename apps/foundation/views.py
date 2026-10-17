from django.db.models import Max
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.accounts.permissions import IsStaffUser
from apps.foundation.models import (
    CollaborateOption,
    FoundationProject,
    HeroSlide,
    OrganMember,
    Sponsor,
    UsefulLink,
)
from apps.foundation.serializers import (
    AdminHeroSlideSerializer,
    CollaborateSerializer,
    HeroSlideSerializer,
    OrganMemberSerializer,
    ProjectSerializer,
    SponsorSerializer,
    UsefulLinkSerializer,
)


class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FoundationProject.objects.exclude(status="draft")
    serializer_class = ProjectSerializer
    lookup_field = "slug"
    permission_classes = [AllowAny]


class AdminProjectViewSet(viewsets.ModelViewSet):
    queryset = FoundationProject.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsStaffUser]


class PublicSponsorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Sponsor.objects.exclude(status="draft").select_related(
        "cover_image", "logo_image"
    )
    serializer_class = SponsorSerializer
    lookup_field = "slug"
    permission_classes = [AllowAny]


class AdminSponsorViewSet(viewsets.ModelViewSet):
    queryset = Sponsor.objects.all().select_related("cover_image", "logo_image")
    serializer_class = SponsorSerializer
    permission_classes = [IsStaffUser]


class OrganMemberViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OrganMember.objects.exclude(status="draft")
    serializer_class = OrganMemberSerializer
    permission_classes = [AllowAny]


class AdminOrganMemberViewSet(viewsets.ModelViewSet):
    queryset = OrganMember.objects.all()
    serializer_class = OrganMemberSerializer
    permission_classes = [IsStaffUser]


class CollaborateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CollaborateOption.objects.exclude(status="draft")
    serializer_class = CollaborateSerializer
    lookup_field = "slug"
    permission_classes = [AllowAny]


class PublicUsefulLinkViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UsefulLink.objects.filter(is_active=True).select_related("logo")
    serializer_class = UsefulLinkSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class AdminUsefulLinkViewSet(viewsets.ModelViewSet):
    queryset = UsefulLink.objects.all().select_related("logo")
    serializer_class = UsefulLinkSerializer
    permission_classes = [IsStaffUser]
    pagination_class = None


class HeroSlideViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = HeroSlideSerializer
    lookup_field = "slug"
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        qs = HeroSlide.objects.filter(is_active=True).select_related(
            "image_asset",
            "mobile_image_asset",
        )
        today = timezone.localtime().isoweekday()
        visible_ids = [slide.pk for slide in qs if slide.is_visible_on(today)]
        return qs.filter(pk__in=visible_ids)


class AdminHeroSlideViewSet(viewsets.ModelViewSet):
    permission_classes = [IsStaffUser]
    serializer_class = AdminHeroSlideSerializer
    lookup_field = "slug"
    pagination_class = None
    queryset = HeroSlide.objects.select_related(
        "image_asset",
        "mobile_image_asset",
    ).order_by("sort_order", "id")

    def perform_create(self, serializer):
        if serializer.validated_data.get("sort_order") is None:
            max_order = HeroSlide.objects.aggregate(m=Max("sort_order"))["m"] or 0
            serializer.save(sort_order=max_order + 1)
        else:
            serializer.save()

    def destroy(self, request, *args, **kwargs):
        slide = self.get_object()
        slide.is_active = False
        slide.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)

