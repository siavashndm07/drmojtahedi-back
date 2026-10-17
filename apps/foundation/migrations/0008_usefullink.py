from django.db import migrations, models
import django.db.models.deletion


DEFAULT_LINKS = [
    (1, "آروین، مجری مرکز توسعه مهارت و سرمایه اجتماعی", "http://arwinco.com"),
    (2, "انجمن فارغ التحصیلان دانشگاه صنعتی شریف", "https://alumsharif.org"),
    (3, "انجمن مدیریت منابع انسانی ایران", "http://hrmsociety.ir/"),
    (4, "جامعه فارغ التحصیلان دبیرستان ماندگار البرز", "http://www.alborzalumni.ir"),
]


def seed_links(apps, schema_editor):
    UsefulLink = apps.get_model("foundation", "UsefulLink")
    for order, title, url in DEFAULT_LINKS:
        UsefulLink.objects.get_or_create(
            title=title,
            defaults={"url": url, "sort_order": order, "is_active": True},
        )


def unseed_links(apps, schema_editor):
    UsefulLink = apps.get_model("foundation", "UsefulLink")
    titles = [t[1] for t in DEFAULT_LINKS]
    UsefulLink.objects.filter(title__in=titles).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("archive_app", "0001_initial"),
        ("foundation", "0007_sponsor_images"),
    ]

    operations = [
        migrations.CreateModel(
            name="UsefulLink",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=255)),
                ("url", models.URLField(max_length=500)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "logo",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="useful_link_logos",
                        to="archive_app.mediaasset",
                    ),
                ),
            ],
            options={
                "verbose_name": "پیوند مفید",
                "verbose_name_plural": "پیوندهای مفید",
                "ordering": ["sort_order", "id"],
            },
        ),
        migrations.RunPython(seed_links, unseed_links),
    ]
