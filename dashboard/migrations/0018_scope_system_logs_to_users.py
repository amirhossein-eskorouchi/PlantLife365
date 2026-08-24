import django.db.models.deletion

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "dashboard",
            "0017_secure_device_pin_and_light_precision",
        ),
        migrations.swappable_dependency(
            settings.AUTH_USER_MODEL
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="systemlog",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="plantlife365_logs",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="systemlog",
            name="device_id",
            field=models.CharField(
                blank=True,
                max_length=100,
                null=True,
            ),
        ),
    ]
