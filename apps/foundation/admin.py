from django.contrib import admin
from apps.foundation.models import (
    CharterChapter,
    FoundationProject,
    OrganMember,
    SiteSettings,
    Sponsor,
    UsefulLink,
)

for m in (
    FoundationProject,
    Sponsor,
    OrganMember,
    UsefulLink,
    CharterChapter,
    SiteSettings,
):
    admin.site.register(m)
