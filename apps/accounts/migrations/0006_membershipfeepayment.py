from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_membershiptier_and_member_link"),
    ]

    operations = [
        migrations.CreateModel(
            name="MembershipFeePayment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("tier_title", models.CharField(blank=True, max_length=255)),
                ("amount", models.PositiveIntegerField(default=0)),
                (
                    "method",
                    models.CharField(
                        choices=[("online", "پرداخت آنلاین"), ("card_to_card", "کارت‌به‌کارت")],
                        default="online",
                        max_length=20,
                    ),
                ),
                ("gateway", models.CharField(blank=True, max_length=16)),
                ("authority", models.CharField(blank=True, max_length=120)),
                ("transaction_id", models.CharField(blank=True, max_length=120)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "در انتظار"),
                            ("redirected", "هدایت به درگاه"),
                            ("awaiting_transfer", "در انتظار واریز"),
                            ("paid", "پرداخت‌شده"),
                            ("cancelled", "لغوشده"),
                            ("failed", "ناموفق"),
                        ],
                        default="pending",
                        max_length=40,
                    ),
                ),
                ("period_year", models.PositiveIntegerField(blank=True, null=True)),
                ("note", models.CharField(blank=True, max_length=255)),
                (
                    "member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="fee_payments",
                        to="accounts.memberprofile",
                    ),
                ),
                (
                    "tier",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="fee_payments",
                        to="accounts.membershiptier",
                    ),
                ),
            ],
            options={
                "verbose_name": "پرداخت حق عضویت",
                "verbose_name_plural": "پرداخت‌های حق عضویت",
                "ordering": ["-created_at"],
            },
        ),
    ]
