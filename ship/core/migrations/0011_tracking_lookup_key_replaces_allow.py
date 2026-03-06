# Replace allow_tracking_lookup (bool) with tracking_lookup_key (secret key string)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_userpreference_allow_tracking_lookup"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="userpreference",
            name="allow_tracking_lookup",
        ),
        migrations.AddField(
            model_name="userpreference",
            name="tracking_lookup_key",
            field=models.CharField(
                blank=True,
                default="",
                help_text="用户将此密钥分享给他人后，他人可通过 密钥+完整快递单号 查看该用户对应订单的只读页面；为空表示未启用",
                max_length=64,
                verbose_name="快递单号查询密钥",
            ),
        ),
    ]
