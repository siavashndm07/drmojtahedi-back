from django.contrib import admin
from apps.engagement.models import (
    ContactMessage,
    Contribution,
    DonationGoal,
    DonationRecord,
    NewsletterSubscriber,
)

for m in (
    NewsletterSubscriber,
    Contribution,
    ContactMessage,
    DonationGoal,
    DonationRecord,
):
    admin.site.register(m)
