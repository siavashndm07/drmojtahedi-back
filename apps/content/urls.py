from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.content.views import (
    AdminArticleCategoryViewSet,
    AdminArticleViewSet,
    AdminLibraryViewSet,
    AdminNewsCategoryViewSet,
    AdminNewsViewSet,
    ArticleViewSet,
    LibraryViewSet,
    PublicArticleCategoryViewSet,
    PublicNewsCategoryViewSet,
    PublicNewsViewSet,
)

public = DefaultRouter()
public.register("news", PublicNewsViewSet, basename="news")
public.register("news-categories", PublicNewsCategoryViewSet, basename="news-categories")
public.register("magazine", ArticleViewSet, basename="magazine")
public.register(
    "article-categories", PublicArticleCategoryViewSet, basename="article-categories"
)

admin_router = DefaultRouter()
admin_router.register("news", AdminNewsViewSet, basename="admin-news")
admin_router.register(
    "news-categories", AdminNewsCategoryViewSet, basename="admin-news-categories"
)
admin_router.register("articles", AdminArticleViewSet, basename="admin-articles")
admin_router.register(
    "article-categories",
    AdminArticleCategoryViewSet,
    basename="admin-article-categories",
)
admin_router.register("books", AdminLibraryViewSet, basename="admin-books")

library_list = LibraryViewSet.as_view({"get": "list"})
library_detail = LibraryViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    path("", include(public.urls)),
    path("library/books/", library_list, name="library-books-list"),
    path("library/books/<slug:slug>/", library_detail, name="library-books-detail"),
    path("admin/", include(admin_router.urls)),
]
