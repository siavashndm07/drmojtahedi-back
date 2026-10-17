from datetime import timedelta
import random

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.db.models import Count
from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.jwt_utils import decode_token, issue_access, issue_refresh
from apps.accounts.models import (
    MemberProfile,
    MembershipFeePayment,
    MembershipTier,
    OtpChallenge,
    StaffProfile,
)
from apps.accounts.permissions import IsStaffUser
from apps.accounts.staff_permissions import (
    STAFF_PERMISSION_KEYS,
    permissions_for_django_user,
)
from apps.engagement.analytics_views import client_ip
from apps.archive.models import ArchiveItem, Gallery, OralHistoryInterview
from apps.content.models import Article, LibraryItem, NewsItem
from apps.engagement.models import (
    Contribution,
    DonationRecord,
    NewsletterSubscriber,
    SiteVisitDaily,
    SiteVisitHit,
)
from apps.foundation.models import Sponsor
from apps.heritage.models import Person

User = get_user_model()


def _record_staff_login(user, request) -> None:
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])
    profile, created = StaffProfile.objects.get_or_create(user=user)
    if created:
        profile.permissions = list(STAFF_PERMISSION_KEYS)
    profile.last_login_ip = client_ip(request) or ""
    profile.save(update_fields=["permissions", "last_login_ip", "updated_at"])


def _record_member_login(profile: MemberProfile, request) -> None:
    profile.last_login = timezone.now()
    profile.last_login_ip = client_ip(request) or ""
    profile.save(update_fields=["last_login", "last_login_ip", "updated_at"])


def _member_payload(profile: MemberProfile) -> dict:
    valid_until = profile.membership_valid_until
    tier = profile.membership_tier
    return {
        "phone": profile.phone,
        "firstName": profile.first_name,
        "lastName": profile.last_name,
        "email": profile.email,
        "nationalId": profile.national_id,
        "education": profile.education,
        "city": profile.city,
        "description": profile.description,
        "howMet": profile.how_met,
        "membershipTierId": tier.id if tier else None,
        "membershipType": (tier.title if tier else profile.membership_type) or "",
        "membershipNumber": profile.membership_number
        or (f"DM-{profile.phone[-4:]}" if profile.phone else ""),
        "membershipStatus": profile.membership_status or "pending",
        "membershipValidUntil": valid_until.isoformat() if valid_until else "",
        "annualFeeRials": profile.resolve_annual_fee(),
    }


class OtpSendView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone = str(request.data.get("phone") or "").strip()
        if len(phone) < 10:
            return Response({"detail": "شماره نامعتبر است"}, status=400)
        code = settings.OTP_DEMO_CODE if settings.OTP_DEMO else f"{random.randint(0, 999999):06d}"
        OtpChallenge.objects.create(
            phone=phone,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        payload = {"success": True, "message": "کد ارسال شد"}
        if settings.OTP_DEMO:
            payload["demo_code"] = code
        return Response(payload)


class OtpVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone = str(request.data.get("phone") or "").strip()
        code = str(request.data.get("code") or "").strip()
        challenge = (
            OtpChallenge.objects.filter(phone=phone, consumed=False)
            .order_by("-created_at")
            .first()
        )
        ok = False
        if settings.OTP_DEMO and code == settings.OTP_DEMO_CODE:
            ok = True
        elif challenge and not challenge.consumed and challenge.expires_at >= timezone.now():
            ok = challenge.code == code
        if not ok:
            return Response({"success": False, "message": "کد نادرست است"}, status=400)
        if challenge:
            challenge.consumed = True
            challenge.save(update_fields=["consumed"])
        profile, _ = MemberProfile.objects.get_or_create(phone=phone)
        _record_member_login(profile, request)
        access = issue_access(phone, "member")
        refresh = issue_refresh(phone, "member")
        return Response(
            {
                "success": True,
                "access": access,
                "refresh": refresh,
                "user": _member_payload(profile),
            }
        )


class AdminLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = str(request.data.get("username") or "").strip()
        password = str(request.data.get("password") or "")
        user = authenticate(username=username, password=password)
        if not user or not user.is_staff:
            return Response({"detail": "نام کاربری یا رمز نادرست است"}, status=400)
        _record_staff_login(user, request)
        access = issue_access(user.username, "staff", uid=user.id)
        refresh = issue_refresh(user.username, "staff")
        return Response(
            {
                "access": access,
                "refresh": refresh,
                "user": {
                    "username": user.username,
                    "firstName": user.first_name,
                    "lastName": user.last_name,
                    "displayName": user.get_full_name() or user.username,
                    "isSuperuser": user.is_superuser,
                    "permissions": permissions_for_django_user(user),
                },
            }
        )


class AdminRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh = str(request.data.get("refresh") or "")
        try:
            payload = decode_token(refresh)
        except Exception:
            return Response({"detail": "رفرش نامعتبر"}, status=401)
        if payload.get("typ") != "refresh" or payload.get("kind") != "staff":
            return Response({"detail": "رفرش نامعتبر"}, status=401)
        access = issue_access(payload["sub"], "staff")
        return Response({"access": access})


class AdminMeView(APIView):
    permission_classes = [IsStaffUser]

    def get(self, request):
        user = request.user
        return Response(
            {
                "username": user.username,
                "firstName": user.first_name,
                "lastName": user.last_name,
                "displayName": user.get_full_name() or user.username,
                "isSuperuser": user.is_superuser,
                "permissions": permissions_for_django_user(user),
            }
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = getattr(request, "member_profile", None)
        if not profile:
            return Response({"detail": "پروفایل عضو یافت نشد"}, status=404)
        if profile.membership_tier_id:
            profile = (
                MemberProfile.objects.select_related("membership_tier")
                .filter(pk=profile.pk)
                .first()
                or profile
            )
        return Response(_member_payload(profile))

    def patch(self, request):
        profile = getattr(request, "member_profile", None)
        if not profile:
            return Response({"detail": "پروفایل عضو یافت نشد"}, status=404)
        # Membership status / validity are payment-driven — not client-writable here.
        mapping = {
            "firstName": "first_name",
            "lastName": "last_name",
            "email": "email",
            "nationalId": "national_id",
            "education": "education",
            "city": "city",
            "description": "description",
            "howMet": "how_met",
            "membershipType": "membership_type",
        }
        for src, dst in mapping.items():
            if src in request.data:
                setattr(profile, dst, str(request.data.get(src) or ""))
        profile.save()
        return self.get(request)


class MembershipTierSerializer(serializers.ModelSerializer):
    annualFeeRials = serializers.IntegerField(source="annual_fee_rials", required=False)
    sortOrder = serializers.IntegerField(source="sort_order", required=False)
    isActive = serializers.BooleanField(source="is_active", required=False)

    class Meta:
        model = MembershipTier
        fields = (
            "id",
            "title",
            "slug",
            "annual_fee_rials",
            "annualFeeRials",
            "description",
            "sort_order",
            "sortOrder",
            "is_active",
            "isActive",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at")


class MemberProfileSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source="first_name", required=False, allow_blank=True)
    lastName = serializers.CharField(source="last_name", required=False, allow_blank=True)
    membershipType = serializers.CharField(
        source="membership_type", required=False, allow_blank=True
    )
    membershipTierId = serializers.PrimaryKeyRelatedField(
        source="membership_tier",
        queryset=MembershipTier.objects.all(),
        allow_null=True,
        required=False,
    )
    membershipNumber = serializers.CharField(
        source="membership_number", required=False, allow_blank=True
    )
    membershipStatus = serializers.CharField(
        source="membership_status", required=False, allow_blank=True
    )
    membershipValidUntil = serializers.DateField(
        source="membership_valid_until", required=False, allow_null=True
    )
    annualFeeRials = serializers.SerializerMethodField()
    nationalId = serializers.CharField(source="national_id", required=False, allow_blank=True)
    howMet = serializers.CharField(source="how_met", required=False, allow_blank=True)
    lastLogin = serializers.DateTimeField(source="last_login", read_only=True)
    lastLoginIp = serializers.CharField(source="last_login_ip", read_only=True)

    class Meta:
        model = MemberProfile
        fields = (
            "id",
            "phone",
            "first_name",
            "firstName",
            "last_name",
            "lastName",
            "email",
            "national_id",
            "nationalId",
            "education",
            "city",
            "description",
            "how_met",
            "howMet",
            "membership_tier",
            "membershipTierId",
            "membership_type",
            "membershipType",
            "membership_number",
            "membershipNumber",
            "membership_status",
            "membershipStatus",
            "membership_valid_until",
            "membershipValidUntil",
            "annual_fee_rials",
            "annualFeeRials",
            "lastLogin",
            "lastLoginIp",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "phone",
            "membership_type",
            "membershipType",
            "annual_fee_rials",
            "created_at",
            "updated_at",
        )

    def get_annualFeeRials(self, obj: MemberProfile) -> int:
        return obj.resolve_annual_fee()

    def update(self, instance, validated_data):
        tier = validated_data.pop("membership_tier", serializers.empty)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if tier is not serializers.empty:
            instance.membership_tier = tier
        instance.sync_tier_fields()
        instance.save()
        return instance


class AdminMembershipTierViewSet(viewsets.ModelViewSet):
    queryset = MembershipTier.objects.all()
    serializer_class = MembershipTierSerializer
    permission_classes = [IsStaffUser]
    pagination_class = None


class PublicMembershipTierListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        rows = MembershipTier.objects.filter(is_active=True)
        return Response(MembershipTierSerializer(rows, many=True).data)


class AdminMemberViewSet(viewsets.ModelViewSet):
    queryset = MemberProfile.objects.select_related("membership_tier").all().order_by(
        "-created_at"
    )
    serializer_class = MemberProfileSerializer
    permission_classes = [IsStaffUser]
    http_method_names = ["get", "patch", "delete", "head", "options"]


class AdminDashboardView(APIView):
    permission_classes = [IsStaffUser]

    def get(self, request):
        now = timezone.localtime()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        try:
            visit_days = int(request.query_params.get("visitDays") or 7)
        except (TypeError, ValueError):
            visit_days = 7
        visit_days = min(max(visit_days, 1), 30)

        visit_rows = {
            row.day.isoformat(): row
            for row in SiteVisitDaily.objects.filter(
                day__gte=(start_of_day - timedelta(days=visit_days - 1)).date(),
                day__lte=start_of_day.date(),
            )
        }
        visits_series = []
        for offset in range(visit_days - 1, -1, -1):
            day = (start_of_day - timedelta(days=offset)).date()
            key = day.isoformat()
            row = visit_rows.get(key)
            visits_series.append(
                {
                    "date": key,
                    "pageviews": row.pageviews if row else 0,
                    "uniques": row.uniques if row else 0,
                }
            )
        today_visit = visit_rows.get(start_of_day.date().isoformat())
        hit_since = start_of_day - timedelta(days=6)
        visit_browsers = [
            {"label": row["browser"] or "Other", "value": row["c"]}
            for row in (
                SiteVisitHit.objects.filter(created_at__gte=hit_since)
                .values("browser")
                .annotate(c=Count("id"))
                .order_by("-c")
            )
        ]
        visit_devices = [
            {"label": row["device"] or "desktop", "value": row["c"]}
            for row in (
                SiteVisitHit.objects.filter(created_at__gte=hit_since)
                .values("device")
                .annotate(c=Count("id"))
                .order_by("-c")
            )
        ]
        recent_visits = [
            {
                "at": hit.created_at.isoformat(),
                "path": hit.path or "/",
                "ip": hit.ip or "",
                "browser": hit.browser or "Other",
                "device": hit.device or "desktop",
            }
            for hit in SiteVisitHit.objects.only(
                "created_at", "path", "ip", "browser", "device"
            ).order_by("-created_at")[:40]
        ]

        open_payment = ("pending", "awaiting_transfer", "redirected")
        drafts = (
            NewsItem.objects.filter(status="draft").count()
            + Article.objects.filter(status="draft").count()
            + LibraryItem.objects.filter(status="draft").count()
        )
        recent_news = [
            {
                "id": item.pk,
                "title": item.title,
                "status": item.status,
                "updatedAt": item.updated_at.isoformat(),
            }
            for item in NewsItem.objects.order_by("-updated_at")[:5]
        ]
        recent_contributions = [
            {
                "id": item.pk,
                "title": item.title,
                "name": item.name,
                "status": item.status,
                "createdAt": item.created_at.isoformat(),
            }
            for item in Contribution.objects.order_by("-created_at")[:5]
        ]
        recent_donations = [
            {
                "id": item.pk,
                "name": item.donor_name or "بدون نام",
                "amount": item.amount,
                "status": item.status,
                "createdAt": item.created_at.isoformat(),
            }
            for item in DonationRecord.objects.order_by("-created_at")[:5]
        ]

        return Response(
            {
                "news": NewsItem.objects.count(),
                "articles": Article.objects.count(),
                "books": LibraryItem.objects.count(),
                "people": Person.objects.count(),
                "archive": ArchiveItem.objects.count(),
                "galleries": Gallery.objects.count(),
                "oralHistory": OralHistoryInterview.objects.count(),
                "sponsors": Sponsor.objects.count(),
                "members": MemberProfile.objects.count(),
                "membersPending": MemberProfile.objects.filter(
                    membership_status="pending"
                ).count(),
                "newsletter": NewsletterSubscriber.objects.filter(active=True).count(),
                "contributions": Contribution.objects.count(),
                "contributionsNew": Contribution.objects.filter(status="new").count(),
                "donationsOpen": DonationRecord.objects.filter(
                    status__in=open_payment
                ).count(),
                "donationsPaid": DonationRecord.objects.filter(status="paid").count(),
                "feesOpen": MembershipFeePayment.objects.filter(
                    status__in=open_payment
                ).count(),
                "drafts": drafts,
                "recentNews": recent_news,
                "recentContributions": recent_contributions,
                "recentDonations": recent_donations,
                "todayVisits": today_visit.pageviews if today_visit else 0,
                "todayUniques": today_visit.uniques if today_visit else 0,
                "visitsLast7Days": visits_series[-7:],
                "visitsSeries": visits_series,
                "visitBrowsers": visit_browsers,
                "visitDevices": visit_devices,
                "recentVisits": recent_visits,
            }
        )
