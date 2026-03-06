from django.conf import settings
from django.db import models


class Customer(models.Model):
    """客户：按用户维护，每个用户有自己的客户列表"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_customers",
        verbose_name="所属用户",
    )
    name = models.CharField("客户名称", max_length=128)
    tracking_lookup_key = models.CharField(
        "订单查询密钥",
        max_length=64,
        blank=True,
        null=True,
        unique=True,
        help_text="用于通过 密钥+快递单号 查询该客户订单的只读权限",
    )

    class Meta:
        db_table = "ship_customer"
        verbose_name = "客户"
        ordering = ["name"]

    def __str__(self):
        return self.name


class CustomerOrderField(models.Model):
    """
    客户与订单关联表（对应「filed」表）：
    id、客户 id、order id，用于记录订单对应的客户。
    """
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="order_fields",
        verbose_name="客户",
    )
    order = models.OneToOneField(
        "core.Order",
        on_delete=models.CASCADE,
        related_name="customer_order_field",
        verbose_name="订单",
    )

    class Meta:
        db_table = "ship_customer_order_field"
        verbose_name = "订单客户关联"

    def __str__(self):
        return f"Customer#{self.customer_id} ↔ Order#{self.order_id}"
