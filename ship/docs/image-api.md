# Image 应用接口设计（内部服务层）

Image 应用**不对外提供 HTTP 接口**，不做用户验证。仅提供**内部服务**（Python 调用），供其他应用在完成鉴权、路由后调用。  
鉴权、权限校验、对外 REST 接口均由**调用方应用**负责。

**约定**：
- `object_key` 由本应用生成，格式：`{user_id}/{date}/{uuid}.{ext}`（date 为 YYYY-MM-DD）。
- 默认使用配置中的单一 bucket；可选参数覆盖。

---

## 1. 服务层职责

| 能力 | 说明 |
|------|------|
| 上传 | 接收文件 + user_id → 写 OSS，写 `core.Image`，返回 Image 实例 |
| 预签名上传 | 生成上传用 PUT 预签名 URL，先落库 Image(size=0)，客户端直传 OSS 后调用确认以更新 size |
| 预签名 URL（下载） | 根据 Image 或 (bucket, object_key) 生成 GET 预签名 URL |
| 删除 | 根据 Image 或 image_id → 删 OSS 对象，删 `core.Image` 记录 |
| 统计 | 根据 user_id → 返回该用户总大小、数量 |

---

## 2. 内部接口（供其他应用调用）

以下为**函数级**接口，无 HTTP、无 request、无 JWT。调用方传入已校验的 `user_id` / `image_id` 等。

### 2.1 上传

```text
upload(file, user_id, bucket=None) -> core.Image
```

- **file**：上传文件对象（如 `request.FILES['file']` 或已打开的 file-like）。
- **user_id**：所属用户 ID（调用方保证已鉴权）。
- **bucket**：可选，不传则用配置默认 bucket。
- **返回**：创建好的 `core.Image` 实例（含 id, user_id, bucket, object_key, size, created_at）。
- **异常**：OSS 失败、DB 失败时抛出，由调用方捕获并转为 HTTP 响应。

### 2.2 预签名 URL

```text
get_presigned_url(image_id, expires_seconds=3600) -> dict
```

- **image_id**：`core.Image` 主键；或改为提供 `(bucket, object_key)` 的重载，由调用方先查 Image 再调。
- **expires_seconds**：有效秒数，默认 3600，最大建议 604800（7 天）。
- **返回**：`{"url": "...", "expires_at": "ISO8601"}`。
- **异常**：Image 不存在、OSS 异常时抛出。**不校验**当前用户是否拥有该图片，由调用方在查 Image 时做权限校验。

- 已提供重载：`get_presigned_url_by_object(bucket, object_key, expires_seconds=3600)`。

### 2.3 预签名上传（客户端直传 OSS）

```text
get_upload_presigned_url(user_id, filename_or_ext="", bucket=None, expires_seconds=3600) -> dict
```

- **user_id**：所属用户 ID（调用方保证已鉴权）。
- **filename_or_ext**：可选，文件名或扩展名（如 `"photo.jpg"` 或 `".png"`），用于生成 object_key 的扩展名，否则默认 jpg。
- **返回**：`{"upload_url": "...", "object_key": "...", "image_id": int, "expires_at": "ISO8601"}`。先创建 `core.Image`（size=0），再生成 OSS PUT 预签名 URL。
- **流程**：调用方把 `upload_url`、`image_id` 返回给客户端 → 客户端用 PUT 直传文件到 `upload_url` → 客户端上传完成后请求调用方 → 调用方调用 `confirm_upload(image_id)` 更新 size。

```text
confirm_upload(image_id) -> core.Image
```

- **image_id**：`get_upload_presigned_url` 返回的 image_id。
- **行为**：对 OSS 对象做 HEAD 取 content-length，更新该 `core.Image.size`。
- **返回**：更新后的 `core.Image`。
- **异常**：Image 不存在、OSS 对象不存在或 HEAD 失败时抛出。

### 2.4 删除

```text
delete_image(image_id) -> None
```

- **image_id**：`core.Image` 主键。
- **行为**：先删 OSS 对象，再删 `core.Image` 记录。若 OSS 不存在或已删，仍删 DB（或先查 Image 再删 OSS 再删 DB）。
- **异常**：Image 不存在可抛；OSS 失败策略（抛 / 仅日志）实现时定。**不校验**归属，由调用方保证只有有权限的用户才调用。

### 2.5 统计

```text
get_user_storage_stats(user_id) -> dict
```

- **user_id**：用户 ID（调用方保证已鉴权）。
- **返回**：`{"total_size": int, "count": int}`（字节数、图片张数），基于 `core.Image` 该用户的 `size` 聚合。

---

## 3. 调用方职责（其他应用）

- **对外 HTTP**：由其他应用提供 REST（如 `POST /api/images/`、`GET /api/images/{id}/url/` 等）。
- **鉴权**：解析 JWT、得到 `request.user`，仅对“当前用户”允许操作。
- **权限**：在调用 image 服务前，自行校验「当前用户是否可操作该 image」（如 image.user_id == request.user.id 或业务规则）。
- **入参**：将 `request.user.id`、选中的 `image_id` 等传入 image 服务，不再在 image 应用内做任何用户校验。

---

## 4. 小结

- **image 应用**：仅实现 OSS 读写 + `core.Image` 增删查、预签名、按 user 统计；对外**无** URL、**无** 用户验证。
- **其他应用**：负责路由、JWT、权限，然后调用 image 提供的函数，并把结果封装成 HTTP 响应。

这样 image 保持独立、可复用，用户与权限边界清晰在调用方。
