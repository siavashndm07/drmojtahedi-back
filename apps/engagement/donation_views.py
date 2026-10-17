from __future__ import annotations

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework import serializers, viewsets

from apps.accounts.permissions import IsStaffUser
from apps.engagement.donation_payment import initiate_donation_payment
from apps.engagement.models import DonationGoal, DonationRecord
from apps.foundation.gateway_services import (
    checkout_gateway_options,
    default_gateway,
)
from apps.foundation.models import OpsSettings
from apps.foundation.simple_html import sanitize_simple_html

MIN_DONATION_RIALS = 10_000
DEFAULT_DONATE_MESSAGE = (
    "حمایت شما صرف برنامه‌های فرهنگی و عام‌المنفعهٔ بنیاد می‌شود."
)


def get_ops() -> OpsSettings:
    page, _ = OpsSettings.objects.get_or_create(key="default")
    return page


def _digits(value: str) -> str:
    persian = "۰۱۲۳۴۵۶۷۸۹"
    arabic = "٠١٢٣٤٥٦٧٨٩"
    out = []
    for ch in str(value or ""):
        if ch in persian:
            out.append(str(persian.index(ch)))
        elif ch in arabic:
            out.append(str(arabic.index(ch)))
        else:
            out.append(ch)
    return "".join(out)


def serialize_donation_goals() -> list[dict]:
    rows = DonationGoal.objects.filter(is_active=True).order_by("sort_order", "id")
    return [
        {
            "id": row.slug or str(row.id),
            "title": row.title,
            "description": row.description or "",
        }
        for row in rows
    ]


def public_payment_options(ops: OpsSettings) -> dict:
    gateways = checkout_gateway_options(ops)
    card_enabled = bool(ops.card_to_card)
    card_number = _digits(ops.card_number or "").replace(" ", "")
    methods: list[dict] = []
    if gateways:
        methods.append(
            {
                "id": "online",
                "label": "پرداخت آنلاین",
                "description": "هدایت امن به درگاه بانکی انتخاب‌شده",
            }
        )
    if card_enabled and card_number:
        methods.append(
            {
                "id": "card_to_card",
                "label": "کارت‌به‌کارت",
                "description": "واریز مستقیم به کارت بنیاد",
            }
        )
    resolved_default = default_gateway(ops)
    raw_message = (ops.donate_message or "").strip()
    message = sanitize_simple_html(raw_message) or DEFAULT_DONATE_MESSAGE
    return {
        "methods": methods,
        "gateways": gateways,
        "defaultGateway": (
            resolved_default
            if resolved_default != OpsSettings.Gateway.NONE
            else (gateways[0]["id"] if gateways else None)
        ),
        "cardToCard": {
            "enabled": card_enabled and bool(card_number),
            "cardHolder": (ops.card_holder or "").strip(),
            "cardNumber": card_number,
        },
        "minAmountRials": MIN_DONATION_RIALS,
        "message": message,
        "goals": serialize_donation_goals(),
    }


class DonationGoalSerializer(serializers.ModelSerializer):
    sortOrder = serializers.IntegerField(source="sort_order", required=False)
    isActive = serializers.BooleanField(source="is_active", required=False)

    class Meta:
        model = DonationGoal
        fields = (
            "id",
            "title",
            "description",
            "slug",
            "sort_order",
            "sortOrder",
            "is_active",
            "isActive",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at")


class AdminDonationGoalViewSet(viewsets.ModelViewSet):
    queryset = DonationGoal.objects.all()
    serializer_class = DonationGoalSerializer
    permission_classes = [IsStaffUser]
    pagination_class = None


class PublicDonatePaymentOptionsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(public_payment_options(get_ops()))


class PublicDonateStartView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ops = get_ops()
        options = public_payment_options(ops)

        try:
            amount = int(request.data.get("amount") or 0)
        except (TypeError, ValueError):
            amount = 0
        if amount < MIN_DONATION_RIALS:
            return Response(
                {"detail": f"حداقل مبلغ کمک {MIN_DONATION_RIALS:,} ریال است."},
                status=400,
            )

        method = str(request.data.get("method") or "").strip()
        gateway = str(request.data.get("gateway") or "").strip() or None
        first_name = str(request.data.get("firstName") or "").strip()
        last_name = str(request.data.get("lastName") or "").strip()
        phone = _digits(str(request.data.get("phone") or "")).strip()
        national_id = _digits(str(request.data.get("nationalId") or "")).strip()
        goals_raw = request.data.get("goals") or request.data.get("targets") or []
        if isinstance(goals_raw, str):
            goals = [g.strip() for g in goals_raw.split(",") if g.strip()]
        elif isinstance(goals_raw, list):
            goals = [str(g).strip() for g in goals_raw if str(g).strip()]
        else:
            goals = []

        donor_name = " ".join(part for part in (first_name, last_name) if part).strip()
        if not donor_name:
            return Response({"detail": "نام اهداکننده الزامی است."}, status=400)
        if not phone:
            return Response({"detail": "شماره همراه الزامی است."}, status=400)

        method_ids = {m["id"] for m in options["methods"]}
        if method not in method_ids:
            return Response({"detail": "روش پرداخت در دسترس نیست."}, status=400)

        goal_label = " · ".join(goals)[:80] if goals else "کمک عام"

        donation = DonationRecord.objects.create(
            amount=amount,
            donor_name=donor_name,
            phone=phone,
            national_id=national_id,
            goal=goal_label,
            goals=goals,
            method=method,
            gateway=gateway or "",
            status=DonationRecord.Status.PENDING,
        )

        if method == DonationRecord.Method.CARD_TO_CARD:
            card = options["cardToCard"]
            donation.status = DonationRecord.Status.AWAITING_TRANSFER
            donation.transaction_id = f"CTC-{donation.id}"
            donation.save(
                update_fields=["status", "transaction_id", "updated_at"]
            )
            return Response(
                {
                    "donationId": donation.id,
                    "method": method,
                    "status": donation.status,
                    "transactionId": donation.transaction_id,
                    "cardToCard": card,
                    "redirectUrl": None,
                },
                status=201,
            )

        # Online → bank redirect
        try:
            resolved, authority, redirect_url = initiate_donation_payment(
                ops,
                amount=amount,
                description=f"کمک بلاعوض #{donation.id} — {goal_label}",
                donation_id=donation.id,
                gateway=gateway,
            )
        except ValueError as exc:
            donation.status = DonationRecord.Status.FAILED
            donation.save(update_fields=["status", "updated_at"])
            return Response({"detail": str(exc)}, status=400)

        donation.gateway = resolved
        donation.authority = authority
        donation.status = DonationRecord.Status.REDIRECTED
        donation.transaction_id = authority
        donation.save(
            update_fields=[
                "gateway",
                "authority",
                "status",
                "transaction_id",
                "updated_at",
            ]
        )
        return Response(
            {
                "donationId": donation.id,
                "method": method,
                "status": donation.status,
                "gateway": resolved,
                "transactionId": authority,
                "redirectUrl": redirect_url,
            },
            status=201,
        )
