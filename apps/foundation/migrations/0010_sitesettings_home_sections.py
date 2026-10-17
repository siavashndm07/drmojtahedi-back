from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("foundation", "0009_opssettings_donate_message"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="home_sections",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="home_section_order",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
