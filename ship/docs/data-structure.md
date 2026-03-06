# 打单/发货 数据结构说明

## 1. 用户与认证

- **用户表**：使用 Django 自带 `auth.User`。
- **认证**：JWT（如 djangorestframework-simplejwt），登录返回 access/refresh token，请求头 `Authorization: Bearer <token>`。

### 1.1 UserPreference 用户喜好表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | PK | 自增 |
| user_id | OneToOne → User | 对应用户，一对一 |
| button_reverse | 布尔 | 按钮喜好状态（目前用于一个可反转按钮） |
| default_order_style_id | FK → OrderStyle，可空 | 用户默认订单样式；为空表示未设置 |

---

## 2. 核心表

### 2.1 Order 订单表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | PK | 自增 |
| user_id | FK → User | 所属用户 |
| tracking_number | 字符串 | 快递单号 |
| style | JSON | 内联样式与槽位定义（见下方 Style JSON 结构） |
| created_at / updated_at | 时间 | 可选 |

**Style JSON 约定**（每个 order 单独维护一份）：

- 维护**槽位间顺序**（如 slots 数组顺序或显式 `slot_order`）。
- 每个槽位包含：
  - 顺序（槽位间）
  - 是否必填、是否展示
  - 类型：文字槽 / 图槽
  - **文字槽**：名称、内容由 Text 表维护，通过 OrderText 关联。
  - **图槽**：名称、最多图数、**processing**（指向 ProcessingField.id，用于后续图片处理）
- 槽位内多图/多文的**槽位内展示顺序**由 OrderImage / OrderText 的 **position** 字段表示。

### 2.2 Image 图片表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | PK | 自增 |
| user_id | FK → User | 上传者，便于归属与统计 |
| bucket | 字符串 | OSS bucket |
| object_key | 字符串 | OSS 对象键，约定带 `{user_id}/` 前缀，便于按用户查与 OSS API 统计 |
| size | 整数 | 文件大小（字节），便于应用层统计 |
| created_at | 时间 | 可选 |

- 访问方式：后端用 bucket + object_key 生成预签名 URL 提供访问。

### 2.3 Text 文字表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | PK | 自增 |
| user_id | FK → User | 与 Image 对应，归属一致 |
| context | 文本 | 文字内容，无 title |
| created_at | 时间 | 可选 |

### 2.4 OrderImage（订单–图片关联）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | PK | 自增 |
| order_id | FK → Order | 订单 |
| image_id | FK → Image | 图片 |
| key | 字符串 | 槽位 key，对应 Order.style 中槽位的 key（如 slot_cover） |
| position | 整数 | 槽位内展示顺序（同一槽位多图时用） |

### 2.5 OrderText（订单–文字关联）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | PK | 自增 |
| order_id | FK → Order | 订单 |
| text_id | FK → Text | 文字 |
| key | 字符串 | 槽位 key，对应 Order.style 中槽位的 key（如 slot_title） |
| position | 整数 | 槽位内展示顺序（若同一槽位多文时用；或与 OrderImage 一致做统一约定） |

---

## 3. OrderStyle 表（独立，可复用样式模板）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | PK | 自增 |
| user_id | FK → User | 所属用户 |
| name | 字符串 | 名称 |
| description | 文本 | 描述 |
| style | JSON | 预设样式（结构可与 Order.style 中槽位定义部分一致，不含业务数据） |
| created_at / updated_at | 时间 | 可选 |

- 不与 Order/Image/Text 等表做外键关联；仅作“样式模板”供创建 Order 时参考或复制到 Order.style。

---

## 4. 分享与权限

### 4.1 Share 表（订单分享链接）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | PK | 自增 |
| order_id | FK → Order | 被分享的订单 |
| creator_id | FK → User | 创建该分享链接的用户 |
| link | 字符串 | 分享链接（或存 token，链接由前端/后端拼） |
| expires_at | 时间 | 过期时间 |
| created_at | 时间 | 创建时间 |

### 4.2 SharePermission 表（用户权限分享，未登录可查看订单）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | PK | 自增 |
| creator_id | FK → User | 创建该权限链接的用户 |
| order_id | FK → Order，可空 | 该链接允许查看的订单；**为空时表示允许访问该用户（creator）的所有订单** |
| token | 字符串 | 唯一 token，用于生成权限链接 |
| expires_at | 时间 | 过期时间 |
| created_at | 时间 | 创建时间 |

- **使用方式**：未登录用户持“权限链接”（含 token），可选带 tracking_number。若 order_id 有值：校验 token 有效、未过期，且该订单的 tracking_number 与请求一致则允许查看；若 order_id 为空：校验 token 有效、未过期后，允许查看 creator 的任意订单（可按 tracking_number 查具体订单）。

---

## 5. 图片处理（预留）

### 5.1 Processing 表（处理模型/类型）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | PK | 自增 |
| name | 字符串 | 名称（如「缩略图」「水印」） |
| 其他 | 按需 | 如 model 标识、参数等，后续扩展 |

### 5.2 ProcessingField 表（处理配置项，供 style 引用）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | PK | 自增 |
| processing_id | FK → Processing | 使用的处理模型 |
| 其他 | 按需 | 如参数、命名，后续扩展 |

- **与 style 的配合**：Order.style 的**图槽**中增加字段 **processing**，值为 ProcessingField.id；后续实现图片处理时，可根据该 id 找到 ProcessingField → Processing，执行对应处理逻辑。

---

## 6. 关系总览

```
User
  ├── Order (user_id)
  ├── Image (user_id)
  ├── Text (user_id)
  ├── OrderStyle (user_id)
  ├── Share (creator_id)
  └── SharePermission (creator_id)

Order
  ├── OrderImage (order_id) → Image
  ├── OrderText (order_id) → Text
  ├── Share (order_id)
  └── SharePermission (order_id，可空；空=该 token 可访问 creator 全部订单)

OrderStyle：独立，无 FK 到 Order/Image/Text

Processing
  └── ProcessingField (processing_id)
      └── 被 Order.style 中图槽的 processing 字段引用（仅存 id）
```

---

## 7. 顺序约定小结

- **槽位间顺序**：由 Order.style 的 JSON 维护（如 slots 数组顺序或显式字段）。
- **槽位内顺序**：由 OrderImage.position、OrderText.position 维护。
- **图槽**：在 style 中增加 processing（ProcessingField.id），用于后续图片处理扩展。

如还有字段或表要增删改，可以说具体表名和字段，我再一起更新这份说明和后续的 Django 模型设计。
