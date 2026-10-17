from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("engagement", "0002_sitevisitdaily_sitevisithit_sitevisitvisitor"),
    ]

    operations = [
        migrations.AddField(
            model_name="donationrecord",
            name="authority",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="donationrecord",
            name="gateway",
            field=models.CharField(blank=True, max_length=16),
        ),
        migrations.AddField(
            model_name="donationrecord",
            name="goals",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="donationrecord",
            name="method",
            field=models.CharField(
                choices=[("online", "پرداخت آنلاین"), ("card_to_card", "کارت‌به‌کارت")],
                default="online",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="donationrecord",
            name="national_id",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="donationrecord",
            name="transaction_id",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AlterField(
            model_name="donationrecord",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "در انتظار"),
                    ("redirected", "هدایت به درگاه"),
                    ("awaiting_transfer", "در انتظار واریز"),
                    ("paid", "پرداخت‌شده"),
                    ("failed", "ناموفق"),
                ],
                default="pending",
                max_length=40,
            ),
        ),
    ]
