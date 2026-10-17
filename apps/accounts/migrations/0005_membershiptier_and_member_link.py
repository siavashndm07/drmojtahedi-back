from django.db import migrations, models
import django.db.models.deletion


DEFAULT_TIERS = [
    ("هیئت موسس", 10_000_000),
    ("هیئت رئیسه", 10_000_000),
    ("هیئت امناء", 0),
    ("رییس کمیته", 5_000_000),
    ("عضو پیوسته", 2_000_000),
    ("عضو افتخاری", 0),
    ("بازرس قانونی", 10_000_000),
    ("عضو وابسته", 0),
    ("عضو حقوقی", 20_000_000),
    ("نماینده بنیاد در چابهار", 0),
    ("نماینده بنیاد در استان همدان", 0),
    ("نماینده بنیاد در ایرانشهر", 0),
    ("شورای برنامه ریزی مجتمع فرهنگی گردشگری دکتر مجتهدی", 10_000_000),
    ("مدیر حسابداری", 0),
    ("همکار بنیاد", 0),
]


def seed_tiers(apps, schema_editor):
    MembershipTier = apps.get_model("accounts", "MembershipTier")
    for index, (title, fee) in enumerate(DEFAULT_TIERS, start=1):
        MembershipTier.objects.get_or_create(
            title=title,
            defaults={
                "slug": f"tier-{index}",
                "annual_fee_rials": fee,
                "sort_order": index,
                "is_active": True,
            },
        )


def unseed_tiers(apps, schema_editor):
    MembershipTier = apps.get_model("accounts", "MembershipTier")
    titles = [t[0] for t in DEFAULT_TIERS]
    MembershipTier.objects.filter(title__in=titles).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_memberprofile_membership_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="MembershipTier",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=255)),
                ("slug", models.SlugField(blank=True, max_length=255, unique=True)),
                ("annual_fee_rials", models.PositiveIntegerField(default=0)),
                ("description", models.TextField(blank=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "نوع عضویت",
                "verbose_name_plural": "انواع عضویت",
                "ordering": ["sort_order", "id"],
            },
        ),
        migrations.AddField(
            model_name="memberprofile",
            name="membership_tier",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="members",
                to="accounts.membershiptier",
            ),
        ),
        migrations.AlterField(
            model_name="memberprofile",
            name="annual_fee_rials",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="memberprofile",
            name="membership_type",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.RunPython(seed_tiers, unseed_tiers),
    ]
