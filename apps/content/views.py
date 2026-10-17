from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from apps.accounts.permissions import IsStaffUser
from apps.content.models import (
    Article,
    ArticleCategory,
    LibraryItem,
    NewsCategory,
    NewsItem,
)
from apps.content.serializers import (
    ArticleCategorySerializer,
    ArticleSerializer,
    LibraryItemSerializer,
    NewsCategorySerializer,
    NewsItemSerializer,
)


class PublicNewsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NewsItem.objects.exclude(status="draft").select_related("cover_image")
    serializer_class = NewsItemSerializer
    lookup_field = "slug"
    permission_classes = [AllowAny]


class AdminNewsViewSet(viewsets.ModelViewSet):
    queryset = NewsItem.objects.all().select_related("cover_image")
    serializer_class = NewsItemSerializer
    permission_classes = [IsStaffUser]


class AdminNewsCategoryViewSet(viewsets.ModelViewSet):
    queryset = NewsCategory.objects.all()
    serializer_class = NewsCategorySerializer
    permission_classes = [IsStaffUser]


class PublicNewsCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NewsCategory.objects.filter(is_active=True)
    serializer_class = NewsCategorySerializer
    lookup_field = "slug"
    permission_classes = [AllowAny]


class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Article.objects.exclude(status="draft").select_related("cover_image")
    serializer_class = ArticleSerializer
    lookup_field = "slug"
    permission_classes = [AllowAny]


class AdminArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all().select_related("cover_image")
    serializer_class = ArticleSerializer
    permission_classes = [IsStaffUser]


class AdminArticleCategoryViewSet(viewsets.ModelViewSet):
    queryset = ArticleCategory.objects.all()
    serializer_class = ArticleCategorySerializer
    permission_classes = [IsStaffUser]


class PublicArticleCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ArticleCategory.objects.filter(is_active=True)
    serializer_class = ArticleCategorySerializer
    lookup_field = "slug"
    permission_classes = [AllowAny]


class LibraryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LibraryItem.objects.exclude(status="draft").select_related("cover_image")
    serializer_class = LibraryItemSerializer
    lookup_field = "slug"
    permission_classes = [AllowAny]


class AdminLibraryViewSet(viewsets.ModelViewSet):
    queryset = LibraryItem.objects.all().select_related("cover_image")
    serializer_class = LibraryItemSerializer
    permission_classes = [IsStaffUser]
