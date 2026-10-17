from __future__ import annotations

import re

from django.core.exceptions import ValidationError
from django.core.validators import validate_ipv46_address
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from apps.engagement.models import SiteVisitDaily, SiteVisitHit, SiteVisitVisitor

VISITOR_RE = re.compile(r"^[a-zA-Z0-9_-]{8,64}$")
BOT_UA = re.compile(
    r"(bot|crawl|spider|slurp|facebookexternalhit|preview|wget|curl|python-requests)",
    re.I,
)


class VisitBurstThrottle(AnonRateThrottle):
    rate = "120/minute"


def client_ip(request) -> str | None:
    forwarded = str(request.META.get("HTTP_X_FORWARDED_FOR") or "").strip()
    if forwarded:
        candidate = forwarded.split(",")[0].strip()
    else:
        candidate = str(request.META.get("REMOTE_ADDR") or "").strip()
    candidate = candidate[:45]
    if not candidate:
        return None
    try:
        validate_ipv46_address(candidate)
    except ValidationError:
        return None
    return candidate


def parse_client(ua: str) -> tuple[str, str]:
    text = (ua or "").lower()
    if "ipad" in text or ("android" in text and "mobile" not in text):
        device = "tablet"
    elif "mobi" in text or "iphone" in text or "android" in text:
        device = "mobile"
    else:
        device = "desktop"

    if "edg/" in text or "edgios" in text:
        browser = "Edge"
    elif "opr/" in text or "opera" in text:
        browser = "Opera"
    elif "samsung" in text:
        browser = "Samsung"
    elif "firefox" in text or "fxios" in text:
        browser = "Firefox"
    elif "chrome" in text or "crios" in text:
        browser = "Chrome"
    elif "safari" in text:
        browser = "Safari"
    else:
        browser = "Other"
    return browser, device


class SiteVisitCreateView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [VisitBurstThrottle]

    def post(self, request):
        ua = str(request.META.get("HTTP_USER_AGENT") or "")
        if BOT_UA.search(ua):
            return Response({"success": True, "ignored": True})

        visitor_key = str(request.data.get("visitorKey") or "").strip()
        if not VISITOR_RE.match(visitor_key):
            return Response(
                {"success": False, "message": "visitorKey نامعتبر است."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        path = str(request.data.get("path") or "").strip()[:200]
        browser, device = parse_client(ua)
        today = timezone.localdate()

        with transaction.atomic():
            daily, _ = SiteVisitDaily.objects.select_for_update().get_or_create(
                day=today,
                defaults={"pageviews": 0, "uniques": 0},
            )
            daily.pageviews += 1
            _, created = SiteVisitVisitor.objects.get_or_create(
                day=today,
                visitor_key=visitor_key,
            )
            if created:
                daily.uniques += 1
            daily.save(update_fields=["pageviews", "uniques"])
            SiteVisitHit.objects.create(
                visitor_key=visitor_key,
                path=path,
                ip=client_ip(request),
                browser=browser,
                device=device,
            )

        return Response(
            {
                "success": True,
                "pageviews": daily.pageviews,
                "uniques": daily.uniques,
            },
            status=status.HTTP_201_CREATED,
        )
