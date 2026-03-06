"""
Image 应用服务层：仅提供内部调用，不对外 HTTP、不做鉴权。
调用方负责鉴权与权限校验后再调用本模块函数。

需要你实现的私有函数（均在本文件内）：
  - _upload_to_oss(file, bucket, object_key)
  - _generate_presigned_url(bucket, object_key, expires_minutes)   # 下载用 GET
  - _generate_upload_presigned_url(bucket, object_key, expires_minutes)  # 上传用 PUT
  - _get_oss_object_size(bucket, object_key)  # HEAD 取 content-length
  - _delete_from_oss(bucket, object_key)

get_user_storage_stats、confirm_upload 已实现；其余对外接口会调用上述私有函数。
调用 get_presigned_url / delete_image / confirm_upload 时若 Image 不存在会抛出 core.models.Image.DoesNotExist。
"""
import uuid
from datetime import timedelta

from django.conf import settings
from django.db.models import Sum, Count
from django.utils import timezone

from core.models import Image

import alibabacloud_oss_v2 as oss
from alibabacloud_oss_v2.types import Credentials, CredentialsProvider

ALLOWED_EXT = ("jpg", "jpeg", "png", "gif", "webp")


# ---------- OSS 凭证与客户端（封装自 settings/.env） ----------
class _DjangoEnvCredentialsProvider(CredentialsProvider):
    """从 Django settings（读取自 .env）获取 OSS 凭证，供 SDK 使用。"""

    def __init__(self) -> None:
        access_key_id = getattr(settings, "OSS_ACCESS_KEY_ID", "")
        access_key_secret = getattr(settings, "OSS_ACCESS_KEY_SECRET", "")
        session_token = getattr(settings, "OSS_SESSION_TOKEN", None)
        if not access_key_id or not access_key_secret:
            raise ValueError(
                "请在 .env 中配置 OSS_ACCESS_KEY_ID 和 OSS_ACCESS_KEY_SECRET"
            )
        self._credentials = Credentials(
            access_key_id, access_key_secret, session_token
        )

    def get_credentials(self) -> Credentials:
        return self._credentials


def _get_oss_client() -> oss.Client:
    """创建并返回 OSS Client，凭证与 region 从 settings 读取。"""
    cfg = oss.config.load_default()
    cfg.credentials_provider = _DjangoEnvCredentialsProvider()
    cfg.region = getattr(settings, "OSS_REGION", "cn-hangzhou")
    return oss.Client(cfg)


def _default_bucket():
    """默认 bucket，从配置读取。可在 settings 或 .env 中设置 OSS_BUCKET_NAME。"""
    return getattr(settings, "OSS_BUCKET_NAME", None)


# ---------- 私有函数（仅供内部调用） ----------
def _generate_presigned_url(bucket: str, object_key: str, expires_minutes: int) -> dict:
    """
    生成预签名 URL。
    使用 OSS SDK 生成 GET 预签名 URL，返回 {"url": "...", "expires_at": "ISO8601"}。
    """
    client = _get_oss_client()
    pre_result = client.presign(
        oss.GetObjectRequest(
            bucket=bucket,  # 指定存储空间名称
            key=object_key,        # 指定对象键名
        ),
        expires = timedelta(minutes=expires_minutes)  # 指定有效时长为expires_minutes分钟
    )

    return {
        "url": pre_result.url,
        "expires_at": pre_result.expiration.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    }


def _delete_from_oss(bucket: str, object_key: str) -> None:
    """
    从 OSS 删除对象。
    若对象不存在可忽略或打日志，由你定；失败时是否抛异常也由你定。
    """
    client = _get_oss_client()
    result = client.delete_object(oss.DeleteObjectRequest(
        bucket=bucket,
        key=object_key,
    ))
    if result.status_code != 204:
        raise Exception(f"删除对象失败: {result.status_code}")


def _generate_upload_presigned_url(
    bucket: str, object_key: str, expires_minutes: int
) -> dict:
    """
    生成上传用预签名 URL（PUT）。
    使用 OSS SDK 生成 PUT 预签名 URL，返回 {"upload_url": "...", "expires_at": "ISO8601"}。
    必须指定 content_type，与前端 PUT 时发送的 Content-Type 一致，否则 OSS 会返回 403。
    """
    client = _get_oss_client()
    pre_result = client.presign(
        oss.PutObjectRequest(
            bucket=bucket,
            key=object_key,
            content_type="application/octet-stream",
        ),
        expires=timedelta(minutes=expires_minutes),
    )
    return {
        "upload_url": pre_result.url,
        "expires_at": pre_result.expiration.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    }


def _get_oss_object_info(bucket: str, object_key: str) -> int:
    """
    通过 HEAD 请求获取 OSS 对象信息。
    对象不存在或失败时抛出异常。
    """
    client = _get_oss_client()
    if not client.is_object_exist(bucket=bucket, key=object_key):
        raise Exception(f"对象不存在: {object_key}")
    result = client.head_object(oss.HeadObjectRequest(
        bucket=bucket,
        key=object_key,
    ))
    if result.status_code != 200:
        raise Exception(f"查询对象大小失败: {result.status_code}")
    return result.content_length


def _get_oss_list_objects(bucket: str, prefix: str):
    """
    通过 LIST 请求获取指定前缀下的 OSS 对象列表。
    :return: [{"name": str, "size": int, "last_modified": datetime}, ...]
    """
    items = []
    client = _get_oss_client()
    paginator = client.list_objects_v2_paginator()
    for page in paginator.iter_page(
        oss.ListObjectsV2Request(
            bucket=bucket,
            # 只列出以 prefix 开头的对象
            prefix=prefix,
        )
    ):
        for o in page.contents:
            items.append(
                {
                    "name": o.key,
                    "size": o.size,
                    "last_modified": o.last_modified,
                }
            )
    return items
# ---------- 

def _normalize_ext(filename_or_ext: str) -> str:
    """从文件名或扩展名字符串解析出允许的扩展名，否则返回 jpg。"""
    s = (filename_or_ext or "").strip().lower()
    if not s:
        return "jpg"
    if s.startswith("."):
        s = s[1:]
    return s if s in ALLOWED_EXT else "jpg"


def _object_key(user_id: int, file) -> str:
    """生成 object_key：{user_id}/{date}/{uuid}.{ext}，date 为 YYYY-MM-DD"""
    date_str = timezone.now().strftime("%Y-%m-%d")
    ext = "jpg"
    if getattr(file, "name", None):
        ext = _normalize_ext(file.name.rsplit(".", 1)[-1] if "." in file.name else "")
    return f"{user_id}/{date_str}/{uuid.uuid4().hex}.{ext}"


def _object_key_for_upload(user_id: int, filename_or_ext: str = "") -> str:
    """预签名上传时生成通用 object_key，无 file 对象，仅根据 filename_or_ext 定扩展名。"""
    date_str = timezone.now().strftime("%Y-%m-%d")
    ext = _normalize_ext(filename_or_ext)
    return f"{user_id}/{date_str}/{uuid.uuid4().hex}.{ext}"


def _object_key_for_order_slot(
    user_id: int,
    order_id: int,
    slot_index: int,
    position: int,
    filename_or_ext: str = "",
) -> str:
    """
    针对“订单内容槽位”生成 object_key。

    约定结构：
      {user_id}/orders/{order_id}/slot-{slot_index}/pos-{position}-{uuid}.{ext}

    这样后续只根据 object_key 即可反推出：
      - 属于哪个订单(order_id)
      - 槽位索引(slot_index)
      - 槽位内的顺序(position)
    """
    ext = _normalize_ext(filename_or_ext)
    return f"{user_id}/orders/{order_id}/slot-{slot_index}/pos-{position}-{uuid.uuid4().hex}.{ext}"
# ---------- 对外服务接口（供其他应用调用） ----------

def get_presigned_url(image_id: int, expires_minutes: int = 30) -> dict:
    """
    根据 Image 主键生成预签名 URL。不校验归属，由调用方保证权限。
    :return: {"url": "...", "expires_at": "ISO8601"}
    """
    image = Image.objects.get(pk=image_id)
    return get_presigned_url_by_object(
        image.bucket, image.object_key, expires_minutes=expires_minutes
    )


def get_presigned_url_by_object(
    bucket: str, object_key: str, expires_minutes: int = 30
) -> dict:
    """
    根据 bucket + object_key 生成预签名 URL。
    :return: {"url": "...", "expires_at": "ISO8601"}
    """
    result = _generate_presigned_url(bucket, object_key, expires_minutes)
    return result


def delete_image(image_id: int) -> None:
    """
    删除图片：先删 OSS 对象，再删 core.Image。不校验归属，由调用方保证权限。
    """
    image = Image.objects.get(pk=image_id)
    try:
        _delete_from_oss(image.bucket, image.object_key)
    except Exception:
        # 可选：仅打日志不抛，或重新抛出，由你实现 _delete_from_oss 时统一
        raise
    image.delete()


def get_user_storage_stats(user_id: int) -> dict:
    """
    统计指定用户的存储：总大小（字节）、图片数量。
    """
    reconcile_pending_upload_images()
    agg = Image.objects.filter(user_id=user_id).aggregate(
        total_size=Sum("size"),
        count=Count("id"),
    )
    return {
        "total_size": agg["total_size"] or 0,
        "count": agg["count"] or 0,
    }


def get_upload_presigned_url(
    user_id: int,
    filename_or_ext: str = "",
    bucket: str = None,
    expires_minutes: int = 30,
) -> dict:
    """
    获取上传用预签名 URL：先创建 core.Image（size=0），再生成 OSS PUT 预签名 URL。
    客户端直传至 upload_url 后，需调用 confirm_upload(image_id) 以更新 size。
    :param filename_or_ext: 文件名或扩展名（如 "photo.jpg" 或 ".png"），用于生成 object_key 扩展名
    :return: {"upload_url": "...", "object_key": "...", "image_id": int, "expires_at": "ISO8601"}
    """
    bucket = bucket or _default_bucket()
    if not bucket:
        raise ValueError("未配置 OSS_BUCKET_NAME 且未传入 bucket")

    object_key = _object_key_for_upload(user_id, filename_or_ext)
    image = Image.objects.create(
        user_id=user_id,
        bucket=bucket,
        object_key=object_key,
        size=0,
    )

    result = _generate_upload_presigned_url(bucket, object_key, expires_minutes)
    result["object_key"] = object_key
    result["image_id"] = image.id
    return result


def get_order_slots_upload_presigned_urls(
    user_id: int,
    order_id: int,
    slots: list[dict],
    bucket: str = None,
    expires_minutes: int = 30,
) -> list[dict]:
    """
    针对“订单内容槽位”批量生成上传用预签名 URL。

    参数：
      - slots: 前端/调用方传入的槽位定义列表，元素需至少包含：
          {
            "type": "text" | "image",
            "max_images": int (仅 image 类型需要，可选，默认 1),
          }

    返回：
      [
        {
          "slot_index": int,
          "type": "image",
          "max_images": int,
          "items": [
            {
              "position": int,          # 槽位内顺序，从 0 开始
              "upload_url": str,
              "expires_at": str,
              "object_key": str,
              "image_id": int,
            },
            ...
          ],
        },
        ...  # 仅包含 image 类型槽位
      ]

    说明：
      - object_key 按 _object_key_for_order_slot 约定编码，后续可据此反查订单/槽位/顺序。
      - 目前未为 text 槽位生成任何 URL。
    """
    bucket = bucket or _default_bucket()
    if not bucket:
        raise ValueError("未配置 OSS_BUCKET_NAME 且未传入 bucket")

    results: list[dict] = []

    for idx, raw in enumerate(slots):
        slot_type = (raw or {}).get("type")
        if slot_type != "image":
            continue

        try:
            max_images = int((raw or {}).get("max_images") or 1)
        except (TypeError, ValueError):
            max_images = 1
        if max_images <= 0:
            max_images = 1

        slot_result = {
            "slot_index": idx,
            "type": "image",
            "max_images": max_images,
            "items": [],
        }

        for pos in range(max_images):
            object_key = _object_key_for_order_slot(
                user_id=user_id,
                order_id=order_id,
                slot_index=idx,
                position=pos,
                filename_or_ext="jpg",
            )
            image = Image.objects.create(
                user_id=user_id,
                bucket=bucket,
                object_key=object_key,
                size=0,
            )
            pre = _generate_upload_presigned_url(
                bucket=bucket,
                object_key=object_key,
                expires_minutes=expires_minutes,
            )
            slot_result["items"].append(
                {
                    "position": pos,
                    "upload_url": pre["upload_url"],
                    "expires_at": pre["expires_at"],
                    "object_key": object_key,
                    "image_id": image.id,
                }
            )

        results.append(slot_result)

    return results


def get_order_slot_upload_presigned_urls(
    user_id: int,
    order_id: int,
    slot_index: int,
    max_images: int,
    bucket: str = None,
    expires_minutes: int = 30,
) -> dict:
    """
    针对“单个图片槽位”生成上传用预签名 URL。

    场景：前端在用户真正进入某个图片槽位（如展开/点击拍照）时，再按需向后端要这一槽位的 URL，
    避免一次性为整单所有槽位生成大量可能用不到的 URL。

    返回：
      {
        "slot_index": int,
        "max_images": int,
        "items": [
          {
            "position": int,          # 槽位内顺序，从 0 开始
            "upload_url": str,
            "expires_at": str,
            "object_key": str,
            "image_id": int,
          },
          ...
        ],
      }
    """
    bucket = bucket or _default_bucket()
    if not bucket:
        raise ValueError("未配置 OSS_BUCKET_NAME 且未传入 bucket")

    try:
        max_images_int = int(max_images)
    except (TypeError, ValueError):
        max_images_int = 1
    if max_images_int <= 0:
        max_images_int = 1

    result: dict = {
        "slot_index": slot_index,
        "max_images": max_images_int,
        "items": [],
    }

    for pos in range(max_images_int):
        object_key = _object_key_for_order_slot(
            user_id=user_id,
            order_id=order_id,
            slot_index=slot_index,
            position=pos,
            filename_or_ext="jpg",
        )
        image = Image.objects.create(
            user_id=user_id,
            bucket=bucket,
            object_key=object_key,
            size=0,
        )
        pre = _generate_upload_presigned_url(
            bucket=bucket,
            object_key=object_key,
            expires_minutes=expires_minutes,
        )
        result["items"].append(
            {
                "position": pos,
                "upload_url": pre["upload_url"],
                "expires_at": pre["expires_at"],
                "object_key": object_key,
                "image_id": image.id,
            }
        )

    return result


def confirm_upload(image_id: int):
    """
    确认预签名上传完成：HEAD OSS 取 content-length，更新 core.Image.size。
    :return: 更新后的 core.Image
    """
    image = Image.objects.get(pk=image_id)
    size = _get_oss_object_info(image.bucket, image.object_key)
    image.size = size
    image.save(update_fields=["size"])
    return image


def reconcile_pending_upload_images() -> dict:
    """
    对 size=0 的 Image 做一次“对账”：
    - 若 OSS 上已不存在对应对象，则删除这条 Image 记录
    - 若 OSS 上存在，则补充 size 字段

    注意：目前只按最简单策略实现，后续若有需要可接入定时任务、批量处理等。
    """
    bucket = _default_bucket()
    if not bucket:
        return {"updated": 0, "deleted": 0}

    client = _get_oss_client()
    pending = Image.objects.filter(size=0, bucket=bucket)
    updated = 0
    deleted = 0

    for image in pending:
        try:
            if not client.is_object_exist(bucket=image.bucket, key=image.object_key):
                image.delete()
                deleted += 1
                continue

            result = client.head_object(
                oss.HeadObjectRequest(bucket=image.bucket, key=image.object_key)
            )
            if result.status_code != 200:
                continue

            image.size = result.content_length
            image.save(update_fields=["size"])
            updated += 1
        except Exception:
            # 网络/OSS 异常时跳过本条，下次任务再试
            continue

    return {"updated": updated, "deleted": deleted}


def list_order_slot_objects(
    user_id: int,
    order_id: int,
    slot_index: int,
    bucket: str = None,
) -> list[dict]:
    """
    列出某个订单中，指定图片槽位下在 OSS 上已存在的所有对象。

    仅依赖 object_key 约定：
      {user_id}/orders/{order_id}/slot-{slot_index}/pos-{position}-{uuid}.{ext}

    返回：
      [
        {
          "object_key": str,
          "size": int,
          "last_modified": datetime,
          "position": Optional[int],  # 若解析失败则为 None
        },
        ...
      ]

    后续上层可以：
      - 按 position 排序，得到槽位内最终顺序
      - 将这些 object_key 与 Image / 订单图片表做统一对账，而不必逐条单独 confirm。
    """
    bucket = bucket or _default_bucket()
    if not bucket:
        raise ValueError("未配置 OSS_BUCKET_NAME 且未传入 bucket")

    prefix = f"{user_id}/orders/{order_id}/slot-{slot_index}/"
    objects = _get_oss_list_objects(bucket=bucket, prefix=prefix)

    results: list[dict] = []
    for obj in objects:
        name = obj["name"]
        # 解析 pos-{position}- 前缀片段
        position = None
        try:
            # name 形如: {user}/orders/{order}/slot-{idx}/pos-{position}-{uuid}.{ext}
            tail = name.split(f"slot-{slot_index}/", 1)[1]
            # tail: 'pos-{position}-{uuid}.{ext}'
            if tail.startswith("pos-"):
                rest = tail[len("pos-") :]  # '{position}-{uuid}.{ext}'
                position_str = rest.split("-", 1)[0]
                position = int(position_str)
        except Exception:
            position = None

        results.append(
            {
                "object_key": name,
                "size": obj["size"],
                "last_modified": obj["last_modified"],
                "position": position,
            }
        )

    # 按 position 排序（None 保持在末尾）
    results.sort(key=lambda x: (x["position"] is None, x["position"] or 0))
    return results
