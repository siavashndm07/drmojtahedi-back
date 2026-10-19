from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("foundation", "0011_heroslide_and_hero_settings"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="footer_nav",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
