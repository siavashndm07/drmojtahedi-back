import django.db.models.deletion
from django.db import migrations, models

import apps.archive.models


class Migration(migrations.Migration):

    dependencies = [
        ("archive_app", "0002_alter_mediaasset_options_mediaasset_alt_text_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mediaasset",
            name="kind",
            field=models.CharField(
                choices=[
                    ("news", "news"),
                    ("articles", "articles"),
                    ("archive", "archive"),
                    ("people", "people"),
                    ("sponsors", "sponsors"),
                    ("hero", "hero"),
                    ("logo", "logo"),
                    ("catalog", "catalog"),
                    ("gallery", "gallery"),
                ],
                db_index=True,
                default="catalog",
                max_length=32,
            ),
        ),
        migrations.CreateModel(
            name="Gallery",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=200)),
                ("slug", models.SlugField(allow_unicode=True, blank=True, max_length=180, unique=True)),
                ("description", models.TextField(blank=True)),
                ("kind", models.CharField(choices=[("images", "تصاویر"), ("videos", "ویدئو")], default="images", max_length=16)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("cover", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="gallery_covers", to="archive_app.mediaasset")),
            ],
            options={
                "verbose_name": "گالری",
                "verbose_name_plural": "گالری‌ها",
                "ordering": ["sort_order", "-id"],
            },
        ),
        migrations.CreateModel(
            name="GalleryItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("caption", models.CharField(blank=True, max_length=255)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("video", models.FileField(blank=True, upload_to=apps.archive.models.gallery_video_upload_to)),
                ("gallery", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="archive_app.gallery")),
                ("image", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="gallery_items", to="archive_app.mediaasset")),
            ],
            options={
                "verbose_name": "رسانه گالری",
                "verbose_name_plural": "رسانه‌های گالری",
                "ordering": ["sort_order", "id"],
            },
        ),
    ]
