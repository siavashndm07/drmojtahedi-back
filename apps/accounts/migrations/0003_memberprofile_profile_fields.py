from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_staffprofile"),
    ]

    operations = [
        migrations.AddField(
            model_name="memberprofile",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="memberprofile",
            name="email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="memberprofile",
            name="how_met",
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name="memberprofile",
            name="national_id",
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
