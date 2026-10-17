from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_membershipfeepayment"),
    ]

    operations = [
        migrations.AddField(
            model_name="memberprofile",
            name="last_login",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="memberprofile",
            name="last_login_ip",
            field=models.CharField(blank=True, max_length=45),
        ),
        migrations.AddField(
            model_name="staffprofile",
            name="last_login_ip",
            field=models.CharField(blank=True, max_length=45),
        ),
    ]
