from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("foundation", "0008_usefullink"),
    ]

    operations = [
        migrations.AddField(
            model_name="opssettings",
            name="donate_message",
            field=models.TextField(
                blank=True,
                default="حمایت شما صرف برنامه‌های فرهنگی و عام‌المنفعهٔ بنیاد می‌شود.",
            ),
        ),
    ]
