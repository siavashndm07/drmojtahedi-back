from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from apps.accounts.permissions import IsStaffUser
from apps.heritage.models import Person, Place, TimelineEvent
from apps.heritage.serializers import (
    PersonSerializer,
    PlaceSerializer,
    TimelineEventSerializer,
)


class PublicPersonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Person.objects.exclude(status="draft")
    serializer_class = PersonSerializer
    lookup_field = "slug"
    permission_classes = [AllowAny]


class AdminPersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    permission_classes = [IsStaffUser]


class PublicPlaceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Place.objects.exclude(status="draft")
    serializer_class = PlaceSerializer
    lookup_field = "slug"
    permission_classes = [AllowAny]


class AdminPlaceViewSet(viewsets.ModelViewSet):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer
    permission_classes = [IsStaffUser]


class TimelineViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TimelineEvent.objects.exclude(status="draft").order_by("id")
    serializer_class = TimelineEventSerializer
    permission_classes = [AllowAny]


class AdminTimelineViewSet(viewsets.ModelViewSet):
    queryset = TimelineEvent.objects.all().order_by("id")
    serializer_class = TimelineEventSerializer
    permission_classes = [IsStaffUser]
