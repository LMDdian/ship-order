# Ship 后端 API 文档

本文档描述 Ship 项目对外提供的 HTTP API 接口。除登录与 Token 刷新外，其余接口均需在请求头中携带 JWT：`Authorization: Bearer <access>`。

**基础路径**：假设后端服务根路径为 `/`，所有 API 均以 `/api/` 为前缀（如 `/api/login/`）。

---

## 1. 认证

### 1.1 登录

- **URL**：`POST /api/login/`
- **认证**：不需要
- **说明**：使用用户名与密码登录，成功后返回 JWT（access/refresh）及当前用户简要信息。

**请求体**（JSON）：

| 字段       | 类型   | 必填 | 说明   |
|------------|--------|------|--------|
| username   | string | 是   | 用户名 |
| password   | string | 是   | 密码   |

**成功响应**（200，JSON）：

| 字段    | 类型   | 说明                    |
|---------|--------|-------------------------|
| access  | string | JWT Access Token        |
| refresh | string | JWT Refresh Token       |
| user    | object | 当前用户信息            |
| user.id | number | 用户 ID                 |
| user.username | string | 用户名           |
| user.first_name | string | 名（可空）     |
| user.last_name  | string | 姓（可空）      |

**错误响应**：

- `400`：`username` / `password` 缺失时返回 `{"detail": "username 和 password 必填"}`；校验失败时返回 `{"detail": "用户名或密码错误"}`。

---

### 1.2 刷新 Access Token

- **URL**：`POST /api/token/refresh/`
- **认证**：不需要（使用 refresh token 换取新 access）
- **说明**：使用 refresh token 换取新的 access token（SimpleJWT 标准接口）。

**请求体**（JSON）：

| 字段   | 类型   | 必填 | 说明           |
|--------|--------|------|----------------|
| refresh| string | 是   | JWT Refresh Token |

**成功响应**（200，JSON）：

| 字段   | 类型   | 说明             |
|--------|--------|------------------|
| access | string | 新的 JWT Access Token |

---

## 2. 订单样式（OrderStyle）

基础路径：`/api/order-styles/`。以下接口均需登录（`IsAuthenticated`），且仅能操作当前用户自己的订单样式。

### 2.1 列表与创建

- **URL**：`/api/order-styles/`
- **方法**：`GET`（列表）、`POST`（创建）

**GET**：返回当前用户的订单样式列表，按 `updated_at` 倒序。

**响应**（200）：JSON 数组，元素结构见下方「单条资源字段」。

**POST 请求体**（JSON）：

| 字段        | 类型   | 必填 | 说明                         |
|-------------|--------|------|------------------------------|
| name        | string | 是   | 名称，最长 128 字符          |
| description | string | 否   | 描述                         |
| style       | object | 否   | 样式 JSON，可含 `slots` 数组 |

`style` 中若包含 `slots` 数组，每条 slot 可含 `key`、`order` 等；缺失时会自动补全默认值。

**POST 响应**（201）：返回新建的单条资源（结构同下）。

**单条资源字段**（列表项 / 详情 / 创建响应）：

| 字段        | 类型   | 说明           |
|-------------|--------|----------------|
| id          | number | 主键（只读）   |
| name        | string | 名称           |
| description | string | 描述           |
| style       | object | 样式 JSON      |
| created_at  | string | 创建时间（只读）|
| updated_at  | string | 更新时间（只读）|

---

### 2.2 单条资源的查看 / 更新 / 删除

- **URL**：`/api/order-styles/<id>/`
- **方法**：`GET`（查看）、`PUT` / `PATCH`（更新）、`DELETE`（删除）
- **路径参数**：`id` 为订单样式主键（整数）。仅能操作当前用户自己的样式，否则 404。

请求体与响应结构同「2.1 列表与创建」中的单条资源；更新时 `id`、`created_at`、`updated_at` 为只读。

---

### 2.3 仅获取样式 JSON（轻量接口）

- **URL**：`/api/order-styles/<id>/style/`
- **方法**：`GET`
- **说明**：仅返回该订单样式的 `style` 字段内容（JSON 对象），便于前端或其他服务直接使用。

**响应**（200）：JSON 对象（即 `style` 字段的原始值，无包装）。

---

## 3. 处理配置（Processing）

基础路径：`/api/processing/`。以下接口均需登录。

### 3.1 ProcessingField 列表（默认）

- **URL**：`GET /api/processing/`
- **说明**：返回所有 ProcessingField，并包含关联的 Processing 信息，供前端选择处理配置。按 `id` 排序。

**响应**（200）：JSON 数组，元素结构：

| 字段       | 类型   | 说明                    |
|------------|--------|-------------------------|
| id         | number | ProcessingField 主键   |
| processing | object | 关联的 Processing       |
| processing.id   | number | Processing 主键  |
| processing.name | string | 处理类型名称（如缩略图、水印） |

---

### 3.2 Processing 类型列表

- **URL**：`GET /api/processing/types/`
- **说明**：仅列出所有 Processing 处理类型（如「缩略图」「水印」等），供前端下拉等使用。

**响应**（200）：JSON 数组，元素结构：

| 字段 | 类型   | 说明           |
|------|--------|----------------|
| id   | number | 主键           |
| name | string | 处理类型名称   |

---

## 4. 用户偏好（User Preference）

- **URL**：`/api/user-preference/`
- **认证**：需要登录。当前登录用户有且仅有一条偏好记录（首次访问时若不存在会自动创建）。

### 4.1 获取当前用户偏好

- **方法**：`GET /api/user-preference/`

**响应**（200，JSON）：

| 字段                  | 类型    | 说明                           |
|-----------------------|---------|--------------------------------|
| id                    | number  | 主键（只读）                   |
| button_reverse        | boolean | 按钮反转偏好（开/关）          |
| default_order_style   | object \| null | 默认订单样式（只读），结构为 `{ id, name }`；未设置时为 `null` |
| default_order_style_id | 不返回 | 仅用于写入，见下方更新接口     |

---

### 4.2 更新当前用户偏好

- **方法**：`PUT /api/user-preference/` 或 `PATCH /api/user-preference/`

**请求体**（JSON，均可选）：

| 字段                   | 类型    | 说明                                   |
|------------------------|---------|----------------------------------------|
| button_reverse         | boolean | 是否按钮反转                           |
| default_order_style_id| number \| null | 默认订单样式 ID；传 `null` 表示清除默认 |

**响应**（200）：与 GET 相同的单条偏好对象（含 `default_order_style` 嵌套对象，不含 `default_order_style_id`）。

---

## 5. 订单（Orders）

基础路径：`/api/orders/`。以下接口均需登录（`IsAuthenticated`），且仅能操作当前登录用户自己的订单。

### 5.1 列表与创建

- **URL**：`/api/orders/`
- **方法**：`GET`（列表）、`POST`（创建）

**GET**：返回当前用户的订单列表。可选查询参数（用于筛选，如主页「查」弹窗）：

| 参数 | 类型 | 说明 |
|------|------|------|
| is_completed | true / false / 1 / 0 | 按是否完成筛选；为 true 时按 completed_time、created_at 倒序 |
| tracking_number | string | 快递单号；与 search_tracking 同传时模糊匹配（icontains），否则精确匹配 |
| search_tracking | 1 / true | 与 tracking_number 同传时单号按模糊匹配 |
| search_text | string | 订单文字标签：在 OrderText 关联的 Text.context 中模糊匹配 |
| completed_date_from | YYYY-MM-DD | 完成日期起（completed_time 的日期） |
| completed_date_to | YYYY-MM-DD | 完成日期止 |
| customer_id | number | 按关联客户 ID 筛选 |
| cost_min / cost_max | number | 成本区间 |
| price_min / price_max | number | 售价区间 |
| profit_min / profit_max | number | 利润区间（利润 = 售价 - 成本，null 按 0 参与计算） |

**响应**（200）：JSON 数组（或分页对象 `{ results: [...] }`），每项结构同下方「订单字段」。

**POST 请求体**（JSON）：

| 字段            | 类型    | 必填 | 说明                                                                 |
|-----------------|---------|------|----------------------------------------------------------------------|
| tracking_number | string  | 是   | 快递单号；若当前用户已有相同单号订单，会返回错误提示已存在此单号      |
| style           | object  | 否   | 订单样式与槽位定义 JSON；若同时提供 `order_style_id`/`style_id` 会被其覆盖 |
| cost            | number  | 否   | 成本，保留两位小数                                                   |
| price           | number  | 否   | 售价，保留两位小数                                                   |
| is_completed    | boolean | 否   | 是否完成，默认 `false`                                               |
| order_style_id  | number  | 否   | 订单样式模板 ID；若为当前用户的样式，则自动复制其 `style` 到订单中     |
| customer_id     | number  | 否   | 客户 ID；若为当前用户的客户，则自动在 `CustomerOrderField` 中建立关联   |

**POST 响应**（201）：单个订单对象（见下）。

**订单字段**（列表项 / 详情 / 创建响应）：

| 字段            | 类型    | 说明                                   |
|-----------------|---------|----------------------------------------|
| id              | number  | 主键（只读）                           |
| tracking_number | string  | 快递单号                               |
| style           | object  | 样式与槽位定义 JSON                    |
| create_style_id | number  | 创建订单时使用的订单样式模板 ID（可空） |
| cost            | number  | 成本（可空）                           |
| price           | number  | 售价（可空）                           |
| is_completed    | boolean | 是否完成                               |
| completed_time  | string \| null | 完成时间（ISO8601），仅已完成订单有值；只读 |
| customer_id     | number  | 关联客户 ID（若存在客户关联，否则为 null） |
| customer_name   | string  | 关联客户名称（若存在客户关联）         |
| card_image_url  | string \| null | 卡片首图预签名 URL（只读，便于列表/瀑布流展示） |
| card_line1      | string \| null | 卡片第一行文字（只读，来自首条 OrderText） |
| card_line2      | string \| null | 卡片第二行文字（只读，来自第二条 OrderText） |
| created_at      | string  | 创建时间（只读）                       |
| updated_at      | string  | 更新时间（只读）                       |

---

### 5.2 单条订单的查看 / 更新 / 删除

- **URL**：`/api/orders/<id>/`
- **方法**：`GET`（查看）、`PUT` / `PATCH`（更新）、`DELETE`（删除）
- **路径参数**：`id` 为订单主键，仅能操作当前用户的订单，否则返回 404。

请求体与响应结构同上「订单字段」；更新时 `id`、`created_at`、`updated_at` 为只读。  
`PUT` 更新时需提供非空的 `tracking_number`，且在当前用户下保持唯一；`PATCH` 更新时若修改 `tracking_number` 同样需满足非空与唯一约束。  
`order_style_id` / `style_id` 与 `customer_id` 在更新时的行为与 `POST /api/orders/` 相同：前者会覆盖订单的 `style`，后者会更新订单与客户的绑定关系。

---

### 5.3 为指定图片槽位获取上传 URL

用于「订单内容槽位」中**单个图片槽位**的预签名上传 URL 获取，前端通常在用户真正进入某个槽位（如展开/点击拍照）时调用。

- **URL**：`POST /api/orders/<id>/slots/<slot_index>/upload-urls/`
- **认证**：需要登录，仅能操作当前登录用户的订单，否则返回 404。
- **路径参数**：
  - `id`：订单主键（整数）
  - `slot_index`：槽位在 `Order.style.slots` 数组中的下标（从 0 开始）

**请求体**（JSON，可选）：

| 字段       | 类型   | 必填 | 说明 |
|------------|--------|------|------|
| max_images | number | 否   | 该槽位最多允许上传的图片数量；若不传，则尝试从 `Order.style.slots[slot_index].max_images` 推断，最终至少为 1 |

**成功响应**（200，JSON）：

```json
{
  "slot_index": 1,
  "max_images": 3,
  "items": [
    {
      "position": 0,
      "upload_url": "https://...签名URL...",
      "expires_at": "2026-03-04T12:00:00.000Z",
      "object_key": "1/orders/123/slot-1/pos-0-xxxx.jpg",
      "image_id": 101
    }
  ]
}
```

- `position`：该图片在槽位内的顺序（0 开始）。
- `upload_url`：前端通过 `PUT` 直传图片到 OSS 时使用的预签名 URL。
- `object_key`：OSS 对象键，按 `{user_id}/orders/{order_id}/slot-{slot_index}/pos-{position}-{uuid}.ext` 结构生成，后端可据此解析订单、槽位、顺序。
- `image_id`：对应的 `Image` 表主键，便于后续统计或查询。

---

### 5.4 订单发货确认（写入文字与图片内容）

用于在用户完成文字填写与图片上传后，确认“发货”并将内容写入对应数据表，同时将订单标记为已完成。

- **URL**：`POST /api/orders/<id>/complete/`
- **认证**：需要登录，仅能操作当前登录用户的订单，否则返回 404。
- **路径参数**：
  - `id`：订单主键（整数）

**请求体**（JSON）：

```json
{
  "order": {
    "cost": 10.5,
    "price": 20,
    "customer_id": 1
  },
  "texts": [
    {
      "slot_index": 0,
      "position": 0,
      "content": "标题文字"
    },
    {
      "slot_index": 2,
      "position": 0,
      "content": "描述文字"
    }
  ]
}
```

- **order**：可选，若提供则用于更新订单基础字段：
  - `cost`、`price`：数值类型，可空；若提供则覆盖原值。
  - `customer_id`：数值类型，可选；若为当前用户的客户，则更新 `CustomerOrderField` 中的订单–客户绑定。
  - 该接口会自动将 `is_completed` 置为 `true`，无需前端显式传入。
- **texts**：可选，文字内容列表；若提供则会写入 `Text` / `OrderText`：
  - `slot_index`：必填，对应 `Order.style.slots` 中的槽位下标（从 0 开始）。
  - `position`：可选，槽位内顺序，默认 0；同一槽位多文时按此字段排序。
  - `content`：必填，具体文字内容；空字符串会被忽略。

**文字写入规则**：

- 后端会根据 `Order.style.slots[slot_index]` 推断槽位 key：
  - 若 slot 中存在 `key` 字段，则使用该值；
  - 否则尝试使用 slot 的 `name`；
  - 若仍未取到，则回退为 `"slot_<slot_index>"`。
- 对每个槽位，采用**覆盖写入**策略：
  - 先删除该订单在该槽位 key 下已有的 `OrderText` 记录；
  - 再按 `position` 排序，依次创建新的 `Text` 与 `OrderText` 记录。

**图片处理规则（服务端自动完成，前端无需传 image_id）**：

- 后端会读取 `Order.style.slots`，对其中 `type === "image"` 的槽位，逐一执行：
  - 使用约定的 OSS 前缀 `{user_id}/orders/{order_id}/slot-{slot_index}/` 调用内部服务扫描该槽位下的所有已上传对象；
  - 按 object_key 中的 `pos-{position}-...` 片段解析槽位内顺序，并按顺序排序；
  - 先删除该订单在该槽位 key 下已有的 `OrderImage` 记录；
  - 再为扫描到的每个对象创建/更新对应的 `Image` 记录（如无则新建，并补充 size），并按顺序创建新的 `OrderImage` 记录（包含 `order_id`、`image_id`、key、position）。
- 因此，前端在调用该接口前，只需确保：
  - 使用 `POST /api/orders/<id>/slots/<slot_index>/upload-urls/` 获取到的预签名 URL 成功上传了图片；
  - 不需要在发货时回传 `image_id` 或 `object_key`。

**成功响应**（200，JSON）：

- 返回更新后的单个订单对象，结构同「5.1 列表与创建」中的“订单字段”。

---

## 6. 客户（Customers）

基础路径：`/api/customers/`。当前登录用户维护自己的客户列表；订单与客户的关联通过 `CustomerOrderField` 表（id、客户 id、order id）维护。

### 6.1 列表与创建

- **URL**：`/api/customers/`
- **方法**：`GET`（列表）、`POST`（新建）
- **认证**：需要登录

**GET**：返回当前用户的客户列表，按名称排序。

**响应**（200）：JSON 数组（或分页对象 `{ results: [...] }`），每项：

| 字段                 | 类型   | 说明                         |
|----------------------|--------|------------------------------|
| id                   | number | 主键                         |
| name                 | string | 客户名称                     |
| tracking_lookup_key   | string | 订单查询密钥（可空）；用于公开接口按「客户密钥+快递单号」查该客户订单 |

**POST 请求体**（JSON）：

| 字段 | 类型   | 必填 | 说明     |
|------|--------|------|----------|
| name | string | 是   | 客户名称 |

**POST 响应**（201）：新建的客户对象（同上）。客户可在编辑时生成/更新 `tracking_lookup_key`，用于下方公开查询接口。

### 6.2 公开：按密钥 + 快递单号查订单（只读）

- **URL**：`GET /api/public/order-by-tracking/`
- **认证**：不需要（公开接口）
- **说明**：通过 **密钥（key）+ 完整快递单号（tracking_number）** 查询订单只读信息。支持两种密钥：
  1. **用户密钥**：对应用户的 `UserPreference.tracking_lookup_key`，匹配该用户下快递单号一致的订单。
  2. **客户密钥**：某客户的 `Customer.tracking_lookup_key`，匹配已关联该客户且快递单号一致的订单（未命中用户密钥时再按客户密钥查）。

**Query 参数**：

| 参数             | 类型   | 必填 | 说明           |
|------------------|--------|------|----------------|
| key              | string | 是   | 用户或客户的查询密钥 |
| tracking_number  | string | 是   | 完整快递单号   |

**成功响应**（200）：返回单个订单对象（结构同订单列表/详情）。

**错误响应**：`400` 缺少 key 或 tracking_number；`404` 未找到对应订单或密钥/单号有误。

---

## 7. 错误与通用说明

- **Order 模型**：订单表已包含 `cost`（成本）、`price`（售价）、`is_completed`（是否完成）字段，可选；客户与订单的关联见 `customer.CustomerOrderField`（id、customer_id、order_id）。
- **认证失败**：未带 Token 或 Token 无效时，通常返回 `401 Unauthorized`。
- **权限不足**：访问非本人资源（如他人订单样式）时返回 `404 Not Found`。
- **业务错误**：多数接口在 body 中通过 `detail` 字段返回错误信息，例如：`{"detail": "错误描述"}`。
- **Content-Type**：请求体请使用 `Content-Type: application/json`；响应为 JSON 时同样为 `application/json`。
