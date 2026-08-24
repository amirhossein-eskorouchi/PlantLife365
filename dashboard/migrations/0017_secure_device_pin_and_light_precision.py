from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "dashboard",
            "0016_alter_usersubscription_tier",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="hardwaredevice",
            name="secret_pin",
            field=models.CharField(
                max_length=128,
            ),
        ),
        migrations.AlterField(
            model_name="sensorreading",
            name="light",
            field=models.FloatField(
                default=0.0,
            ),
        ),
    ]
