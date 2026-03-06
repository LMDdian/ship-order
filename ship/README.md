# 打单发货 - 后端

独立 Django 项目，使用数据库 `dian_ship_db`（用户 `dian`）。当前已清空业务应用，便于重新设计数据结构。

## 库

- 库名：`dian_ship_db`
- 用户：`dian`（密码见主项目 `backend/scripts/mariadb-setup-new-project.sql` 或本地 `.env`）

重新设计表结构后，如与旧表冲突，可删库重建或先执行：

```bash
# 仅当需要清空库时（会删除所有表）
mysql -u dian -p dian_ship_db -e "DROP DATABASE dian_ship_db; CREATE DATABASE dian_ship_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

## 开发

```bash
cd backend/ship
cp .env.example .env
# 编辑 .env 填写 DB_PASSWORD

python3 manage.py runserver 8001
```

当前仅保留 Django 骨架（admin、REST、CORS、数据库与媒体配置），无自定义 app 与 API。
