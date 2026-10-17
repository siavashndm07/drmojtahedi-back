from django.contrib import admin
from apps.content.models import NewsItem, Article, LibraryItem
admin.site.register(NewsItem)
admin.site.register(Article)
admin.site.register(LibraryItem)
