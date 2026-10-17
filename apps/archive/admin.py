from django.contrib import admin
from apps.archive.models import (
    ArchiveItem,
    Gallery,
    GalleryItem,
    MediaAsset,
    OralHistoryInterview,
)

admin.site.register(ArchiveItem)
admin.site.register(OralHistoryInterview)
admin.site.register(MediaAsset)
admin.site.register(Gallery)
admin.site.register(GalleryItem)
