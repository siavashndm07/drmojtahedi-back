from django.db import migrations, models


DEFAULT_GOALS = [
    (1, "schools", "مدارس بنیاد", "ساخت و بهره‌برداری از مدارس"),
    (2, "entrepreneurship", "مراکز کارآفرینی", "ساخت، تجهیز و بهره‌برداری"),
    (3, "training", "آموزش نیروی انسانی", "امور آموزش و تربیت"),
    (4, "students", "دانش‌آموزان نیازمند", "کمک به خانواده‌های نیازمند"),
    (5, "jobs", "اشتغال مناطق محروم", "ایجاد اشتغال و کارآفرینی"),
    (6, "general", "کمک عام", "هزینه به تشخیص بنیاد"),
]


def seed_goals(apps, schema_editor):
    DonationGoal = apps.get_model("engagement", "DonationGoal")
    for order, slug, title, description in DEFAULT_GOALS:
        DonationGoal.objects.get_or_create(
            slug=slug,
            defaults={
                "title": title,
                "description": description,
                "sort_order": order,
                "is_active": True,
            },
        )


def unseed_goals(apps, schema_editor):
    DonationGoal = apps.get_model("engagement", "DonationGoal")
    DonationGoal.objects.filter(slug__in=[g[1] for g in DEFAULT_GOALS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("engagement", "0003_donationrecord_payment_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="DonationGoal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=120)),
                ("description", models.CharField(blank=True, max_length=255)),
                ("slug", models.SlugField(blank=True, max_length=80, unique=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "هدف کمک",
                "verbose_name_plural": "اهداف کمک",
                "ordering": ["sort_order", "id"],
            },
        ),
        migrations.RunPython(seed_goals, unseed_goals),
    ]
