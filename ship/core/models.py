"""
核心模型：与 docs/data-structure.md 一致。
用户使用 Django 自带 auth.User，JWT 认证。
"""
from django.conf import settings
from django.db import models


# ---------- 图片处理（预留，被 Order.style 图槽的 processing 字段引用） ----------


class Processing(models.Model):
    """处理模型/类型（如缩略图、水印等）"""
    name = models.CharField("名称", max_length=64)

    class Meta:
        db_table = "ship_processing"
        verbose_name = "处理模型"

    def __str__(self):
        return self.name


class ProcessingField(models.Model):
    """处理配置项，供 Order.style 图槽的 processing 字段引用（存 id）"""
    processing = models.ForeignKey(
        Processing, on_delete=models.CASCADE, related_name="fields", verbose_name="处理模型"
    )

    class Meta:
        db_table = "ship_processing_field"
        verbose_name = "处理配置项"

    def __str__(self):
        return f"ProcessingField({self.processing.name})"


# ---------- 图片与文字 ----------


class Image(models.Model):
    """图片：OSS 存储，object_key 约定带 {user_id}/ 前缀"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="core_images",
        verbose_name="上传者",
    )
    bucket = models.CharField("bucket", max_length=128)
    object_key = models.CharField("object_key", max_length=512)
    size = models.PositiveIntegerField("大小(字节)", default=0)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "ship_image"
        verbose_name = "图片"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.bucket}/{self.object_key}"


class Text(models.Model):
    """文字内容"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="core_texts",
        verbose_name="所属用户",
    )
    context = models.TextField("内容", blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "ship_text"
        verbose_name = "文字"
        ordering = ["-created_at"]

    def __str__(self):
        return (self.context[:50] + "…") if len(self.context) > 50 else self.context or "(空)"


# ---------- 订单与槽位关联 ----------


class Order(models.Model):
    """
    订单。style 为 JSON，内联槽位定义：
    - 槽位间顺序、是否必填、是否展示
    - 文字槽：名称，内容在 Text 表，通过 OrderText 关联
    - 图槽：名称、最多图数、processing(ProcessingField.id)
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="core_orders",
        verbose_name="所属用户",
    )
    tracking_number = models.CharField("快递单号", max_length=64, blank=True)
    style = models.JSONField("样式与槽位定义", default=dict, blank=True)
    create_style_id = models.IntegerField(
        "创建样式 ID",
        null=True,
        blank=True,
        help_text="记录创建订单时使用的 OrderStyle.id",
    )
    cost = models.DecimalField(
        "成本",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="订单成本",
    )
    price = models.DecimalField(
        "售价",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="订单售价",
    )
    is_completed = models.BooleanField(
        "是否完成",
        default=False,
        help_text="订单是否已经完成",
    )
    completed_time = models.DateTimeField(
        "完成时间",
        null=True,
        blank=True,
        help_text="订单标记为已完成的时间",
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "ship_order"
        verbose_name = "订单"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order#{self.id} ({self.tracking_number or '-'})"


class OrderImage(models.Model):
    """订单–图片关联，key 指定槽位（对应 Order.style 中槽位 key），position 表示槽位内展示顺序"""
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_images", verbose_name="订单"
    )
    image = models.ForeignKey(
        Image, on_delete=models.CASCADE, related_name="order_images", verbose_name="图片"
    )
    key = models.CharField("槽位 key", max_length=64, blank=True, default="")
    position = models.PositiveIntegerField("槽位内顺序", default=0)

    class Meta:
        db_table = "ship_order_image"
        verbose_name = "订单图片"
        ordering = ["order", "key", "position", "id"]

    def __str__(self):
        return f"Order#{self.order_id} ↔ Image#{self.image_id}"


class OrderText(models.Model):
    """订单–文字关联，key 指定槽位（对应 Order.style 中槽位 key），position 表示槽位内展示顺序"""
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_texts", verbose_name="订单"
    )
    text = models.ForeignKey(
        Text, on_delete=models.CASCADE, related_name="order_texts", verbose_name="文字"
    )
    key = models.CharField("槽位 key", max_length=64, blank=True, default="")
    position = models.PositiveIntegerField("槽位内顺序", default=0)

    class Meta:
        db_table = "ship_order_text"
        verbose_name = "订单文字"
        ordering = ["order", "key", "position", "id"]

    def __str__(self):
        return f"Order#{self.order_id} ↔ Text#{self.text_id}"


# ---------- 样式模板（独立） ----------


class OrderStyle(models.Model):
    """预设样式模板，不与 Order 等表外键关联"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="core_order_styles",
        verbose_name="所属用户",
    )
    name = models.CharField("名称", max_length=128)
    description = models.TextField("描述", blank=True)
    style = models.JSONField("样式", default=dict, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "ship_order_style"
        verbose_name = "订单样式模板"
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name


# ---------- 分享与权限 ----------


class Share(models.Model):
    """订单分享链接"""
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="shares", verbose_name="订单"
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="core_share_links",
        verbose_name="创建者",
    )
    link = models.CharField("分享链接或 token", max_length=512)
    expires_at = models.DateTimeField("过期时间")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "ship_share"
        verbose_name = "分享链接"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Share Order#{self.order_id}"


class SharePermission(models.Model):
    """权限分享：未登录用户凭 token + tracking_number 查看订单。order 为空时表示允许访问创建者的所有订单。"""
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="core_share_permissions",
        verbose_name="创建者",
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="share_permissions",
        verbose_name="订单",
        null=True,
        blank=True,
        help_text="为空时表示该 token 允许访问创建者的所有订单",
    )
    token = models.CharField("token", max_length=64, unique=True)
    expires_at = models.DateTimeField("过期时间")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "ship_share_permission"
        verbose_name = "分享权限"
        ordering = ["-created_at"]

    def __str__(self):
        if self.order_id is None:
            return f"Permission 全部订单 (creator_id={self.creator_id})"
        return f"Permission Order#{self.order_id}"


# ---------- 用户喜好 ----------


class UserPreference(models.Model):
    """用户喜好"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="core_user_preference",
        verbose_name="用户",
    )
    button_reverse = models.BooleanField(
        "按钮反转",
        default=False,
        help_text="用于记录某个按钮的喜好状态（开/关）",
    )
    default_order_style = models.ForeignKey(
        OrderStyle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="preferred_by_users",
        verbose_name="默认订单样式",
        help_text="用户新建订单时默认选用的 OrderStyle；为空表示未设置默认样式",
    )
    tracking_lookup_key = models.CharField(
        "快递单号查询密钥",
        max_length=64,
        blank=True,
        default="",
        help_text="用户将此密钥分享给他人后，他人可通过 密钥+完整快递单号 查看该用户对应订单的只读页面；为空表示未启用",
    )
    storage_limit_bytes = models.BigIntegerField(
        "存储容量上限（字节）",
        default=1024 * 1024 * 1024,  # 1GB
        help_text="允许该用户存储的图片总大小（字节），默认 1GB",
    )

    class Meta:
        db_table = "ship_user_preference"
        verbose_name = "用户喜好"

    def __str__(self):
        return (
            f"Preference(user_id={self.user_id}, "
            f"button_reverse={self.button_reverse}, "
            f"default_order_style_id={self.default_order_style_id})"
        )
