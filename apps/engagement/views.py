from rest_framework import generics, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.accounts.permissions import IsStaffUser
from apps.engagement.models import (
    ContactMessage,
    Contribution,
    DonationRecord,
    NewsletterSubscriber,
)
from apps.engagement.serializers import (
    ContactSerializer,
    ContributionSerializer,
    DonationSerializer,
    NewsletterSerializer,
)

class NewsletterSubscribeView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = str(request.data.get("email") or "").strip().lower()
        if "@" not in email:
            return Response({"detail": "ایمیل نامعتبر"}, status=400)
        obj, created = NewsletterSubscriber.objects.get_or_create(email=email)
        return Response({"success": True, "created": created, "email": obj.email})

class ContributionCreateView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        ser = ContributionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data, status=201)

class ContactCreateView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        ser = ContactSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data, status=201)

class AdminNewsletterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NewsletterSubscriber.objects.all().order_by("-created_at")
    serializer_class = NewsletterSerializer
    permission_classes = [IsStaffUser]

class AdminContributionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Contribution.objects.all().order_by("-created_at")
    serializer_class = ContributionSerializer
    permission_classes = [IsStaffUser]


class AdminDonationViewSet(viewsets.ModelViewSet):
    queryset = DonationRecord.objects.all().order_by("-created_at")
    serializer_class = DonationSerializer
    permission_classes = [IsStaffUser]
    http_method_names = ["get", "patch", "delete", "head", "options"]
