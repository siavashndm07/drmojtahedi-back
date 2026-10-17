from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.heritage.urls")),
    path("api/v1/", include("apps.content.urls")),
    path("api/v1/", include("apps.archive.urls")),
    path("api/v1/", include("apps.foundation.urls")),
    path("api/v1/", include("apps.engagement.urls")),
    path("api/v1/", include("apps.ai.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
