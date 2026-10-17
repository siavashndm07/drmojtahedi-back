from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsStaffUser
from apps.foundation.ai_chat_services import (
    AiChatError,
    chat_completion,
    public_ai_config,
    test_ai_connection,
)
from apps.foundation.models import OpsSettings


def _client_key(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR") or ""
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    return (request.META.get("REMOTE_ADDR") or "anon")[:64]


class PublicAiChatConfigView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response(public_ai_config())


class PublicAiChatView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        try:
            result = chat_completion(
                messages=request.data.get("messages"),
                client_key=_client_key(request),
            )
        except AiChatError as exc:
            return Response({"detail": exc.detail}, status=exc.status)
        except Exception:
            return Response(
                {"detail": "پاسخ‌گویی ناموفق بود."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(result)


class AdminOpsAiTestView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]

    def post(self, request):
        ops = OpsSettings.objects.filter(key="default").first()
        if not ops:
            return Response(
                {"detail": "تنظیمات یافت نشد."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        temp_key = str(request.data.get("apiKey") or "").strip()
        if temp_key:
            ops.ai_api_key = temp_key
        provider = str(request.data.get("provider") or "").strip()
        if provider in {c.value for c in OpsSettings.AiProvider}:
            ops.ai_provider = provider
        model = str(request.data.get("model") or "").strip()
        if model:
            ops.ai_model = model
        base_url = str(request.data.get("baseUrl") or "").strip()
        if base_url:
            ops.ai_base_url = base_url
        if not ops.ai_enabled and not temp_key and not (ops.ai_api_key or "").strip():
            return Response(
                {"detail": "دستیار را فعال کنید و کلید API را ذخیره کنید."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ops.ai_enabled = True
        try:
            detail = test_ai_connection(ops)
        except AiChatError as exc:
            return Response({"detail": exc.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response(
                {"detail": str(exc) or "تست ناموفق بود."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"ok": True, "detail": detail})
