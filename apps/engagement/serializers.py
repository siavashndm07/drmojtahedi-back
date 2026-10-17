from rest_framework import serializers

from apps.engagement.models import (
    ContactMessage,
    Contribution,
    DonationRecord,
    NewsletterSubscriber,
)


class NewsletterSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterSubscriber
        fields = ("id", "email", "active", "created_at")


class ContributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contribution
        fields = "__all__"


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = "__all__"


class DonationSerializer(serializers.ModelSerializer):
    donorName = serializers.CharField(source="donor_name", required=False, allow_blank=True)
    nationalId = serializers.CharField(source="national_id", required=False, allow_blank=True)
    transactionId = serializers.CharField(
        source="transaction_id", required=False, allow_blank=True
    )

    class Meta:
        model = DonationRecord
        fields = (
            "id",
            "amount",
            "donor_name",
            "donorName",
            "phone",
            "national_id",
            "nationalId",
            "goal",
            "goals",
            "method",
            "gateway",
            "authority",
            "transaction_id",
            "transactionId",
            "status",
            "created_at",
            "updated_at",
        )
