from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_memberprofile_profile_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="memberprofile",
            name="annual_fee_rials",
            field=models.PositiveIntegerField(default=5000000),
        ),
        migrations.AddField(
            model_name="memberprofile",
            name="membership_number",
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name="memberprofile",
            name="membership_status",
            field=models.CharField(blank=True, default="pending", max_length=20),
        ),
        migrations.AddField(
            model_name="memberprofile",
            name="membership_valid_until",
            field=models.DateField(blank=True, null=True),
        ),
    ]
