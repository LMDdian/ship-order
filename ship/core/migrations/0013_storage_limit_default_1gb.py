# 将存储容量默认值从 10GB 改为 1GB

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_userpreference_storage_limit"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userpreference",
            name="storage_limit_bytes",
            field=models.BigIntegerField(
                default=1024 * 1024 * 1024,  # 1GB
                help_text="允许该用户存储的图片总大小（字节），默认 1GB",
                verbose_name="存储容量上限（字节）",
            ),
        ),
    ]
