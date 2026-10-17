from __future__ import annotations

from datetime import date

from django.utils import timezone
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import MembershipFeePayment, MemberProfile
from apps.accounts.permissions import IsStaffUser
from apps.engagement.donation_payment import initiate_donation_payment
from apps.engagement.donation_views import get_ops, public_payment_options
from apps.foundation.gateway_services import GATEWAY_LABELS


def _member_from_request(request) -> MemberProfile | None:
    return getattr(request, "member_profile", None)


def activate_membership(member: MemberProfile, *, period_year: int | None = None) -> None:
    year = period_year or timezone.localdate().year
    member.membership_status = "active"
    member.membership_valid_until = date(year + 1, 12, 29)
    member.sync_tier_fields()
    member.save(
        update_fields=[
            "membership_status",
            "membership_valid_until",
            "membership_type",
            "annual_fee_rials",
            "updated_at",
        ]
    )


class MembershipFeePaymentSerializer(serializers.ModelSerializer):
    memberPhone = serializers.CharField(source="member.phone", read_only=True)
    memberName = serializers.SerializerMethodField()
    tierTitle = serializers.CharField(source="tier_title", required=False, allow_blank=True)
    tierId = serializers.IntegerField(source="tier_id", read_only=True)
    transactionId = serializers.CharField(
        source="transaction_id", required=False, allow_blank=True
    )
    periodYear = serializers.IntegerField(source="period_year", required=False, allow_null=True)
    gatewayLabel = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = MembershipFeePayment
        fields = (
            "id",
            "member",
            "memberPhone",
            "memberName",
            "tier",
            "tierId",
            "tier_title",
            "tierTitle",
            "amount",
            "method",
            "gateway",
            "gatewayLabel",
            "authority",
            "transaction_id",
            "transactionId",
            "status",
            "period_year",
            "periodYear",
            "note",
            "created_at",
            "createdAt",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "member",
            "tier",
            "tier_title",
            "amount",
            "method",
            "gateway",
            "authority",
            "transaction_id",
            "period_year",
            "created_at",
            "updated_at",
        )

    def get_memberName(self, obj: MembershipFeePayment) -> str:
        name = f"{obj.member.first_name} {obj.member.last_name}".strip()
        return name or obj.member.phone

    def get_gatewayLabel(self, obj: MembershipFeePayment) -> str:
        if obj.method == MembershipFeePayment.Method.CARD_TO_CARD:
            return "کارت‌به‌کارت"
        return GATEWAY_LABELS.get(obj.gateway, obj.gateway or "—")


class MemberMembershipFeeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        member = _member_from_request(request)
        if not member:
            return Response({"detail": "پروفایل عضو یافت نشد"}, status=404)
        rows = (
            MembershipFeePayment.objects.filter(member=member)
            .select_related("tier", "member")
            .order_by("-created_at")
        )
        return Response(MembershipFeePaymentSerializer(rows, many=True).data)


class MemberMembershipFeeStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        member = _member_from_request(request)
        if not member:
            return Response({"detail": "پروفایل عضو یافت نشد"}, status=404)

        if member.membership_tier_id:
            member = (
                MemberProfile.objects.select_related("membership_tier")
                .filter(pk=member.pk)
                .first()
                or member
            )

        amount = member.resolve_annual_fee()
        if amount <= 0:
            return Response(
                {"detail": "برای ارکان شما حق عضویت سالانه تعریف نشده است."},
                status=400,
            )

        ops = get_ops()
        options = public_payment_options(ops)
        method = str(request.data.get("method") or "").strip()
        gateway = str(request.data.get("gateway") or "").strip() or None
        method_ids = {m["id"] for m in options["methods"]}
        if method not in method_ids:
            return Response({"detail": "روش پرداخت در دسترس نیست."}, status=400)

        year = timezone.localdate().year
        tier = member.membership_tier
        payment = MembershipFeePayment.objects.create(
            member=member,
            tier=tier,
            tier_title=(tier.title if tier else member.membership_type) or "",
            amount=amount,
            method=method,
            gateway=gateway or "",
            status=MembershipFeePayment.Status.PENDING,
            period_year=year,
        )

        if method == MembershipFeePayment.Method.CARD_TO_CARD:
            card = options["cardToCard"]
            payment.status = MembershipFeePayment.Status.AWAITING_TRANSFER
            payment.transaction_id = f"MFEE-CTC-{payment.id}"
            payment.save(update_fields=["status", "transaction_id", "updated_at"])
            return Response(
                {
                    "paymentId": payment.id,
                    "method": method,
                    "status": payment.status,
                    "transactionId": payment.transaction_id,
                    "amount": payment.amount,
                    "cardToCard": card,
                    "redirectUrl": None,
                },
                status=201,
            )

        try:
            resolved, authority, redirect_url = initiate_donation_payment(
                ops,
                amount=amount,
                description=f"حق عضویت #{payment.id} — {payment.tier_title}",
                donation_id=payment.id,
                gateway=gateway,
                callback_path="/account/membership-fee",
                callback_query_key="payment",
            )
        except ValueError as exc:
            payment.status = MembershipFeePayment.Status.FAILED
            payment.save(update_fields=["status", "updated_at"])
            return Response({"detail": str(exc)}, status=400)

        payment.gateway = resolved
        payment.authority = authority
        payment.status = MembershipFeePayment.Status.REDIRECTED
        payment.transaction_id = authority
        payment.save(
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
                "paymentId": payment.id,
                "method": method,
                "status": payment.status,
                "gateway": resolved,
                "transactionId": authority,
                "amount": payment.amount,
                "redirectUrl": redirect_url,
            },
            status=201,
        )


class AdminMembershipFeePaymentViewSet(viewsets.ModelViewSet):
    queryset = MembershipFeePayment.objects.select_related(
        "member", "tier"
    ).all()
    serializer_class = MembershipFeePaymentSerializer
    permission_classes = [IsStaffUser]
    http_method_names = ["get", "patch", "delete", "head", "options"]
    pagination_class = None

    def partial_update(self, request, *args, **kwargs):
        payment = self.get_object()
        new_status = str(request.data.get("status") or "").strip()
        note = request.data.get("note")
        if note is not None:
            payment.note = str(note)[:255]

        if new_status and new_status != payment.status:
            payment.status = new_status
            if new_status == MembershipFeePayment.Status.PAID:
                activate_membership(payment.member, period_year=payment.period_year)
                if not payment.transaction_id:
                    payment.transaction_id = f"MFEE-{payment.id}"
            payment.save()
        elif note is not None:
            payment.save(update_fields=["note", "updated_at"])

        return Response(MembershipFeePaymentSerializer(payment).data)
