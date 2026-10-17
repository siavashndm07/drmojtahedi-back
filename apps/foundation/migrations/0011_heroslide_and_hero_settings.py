import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("archive_app", "0003_gallery"),
        ("foundation", "0010_sitesettings_home_sections"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="hero_autoplay_delay",
            field=models.PositiveIntegerField(default=5600),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="hero_template",
            field=models.CharField(blank=True, default="fullBleed", max_length=32),
        ),
        migrations.CreateModel(
            name="HeroSlide",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("slug", models.SlugField(allow_unicode=True, max_length=120, unique=True)),
                ("image", models.CharField(blank=True, max_length=500)),
                ("mobile_image", models.CharField(blank=True, max_length=500)),
                ("eyebrow", models.CharField(blank=True, max_length=120)),
                ("title", models.CharField(max_length=200)),
                ("subtitle", models.CharField(blank=True, max_length=255)),
                ("description", models.TextField(blank=True)),
                ("cta_label", models.CharField(blank=True, max_length=120)),
                ("cta_href", models.CharField(blank=True, max_length=255)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "weekdays",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="روزهای نمایش بر اساس ISO (۱=دوشنبه … ۷=یکشنبه). خالی یعنی همه روزها.",
                    ),
                ),
                (
                    "image_asset",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="hero_slides",
                        to="archive_app.mediaasset",
                    ),
                ),
                (
                    "mobile_image_asset",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="hero_slides_mobile",
                        to="archive_app.mediaasset",
                    ),
                ),
            ],
            options={
                "verbose_name": "اسلاید هیرو",
                "verbose_name_plural": "اسلایدهای هیرو",
                "ordering": ["sort_order", "id"],
            },
        ),
    ]
