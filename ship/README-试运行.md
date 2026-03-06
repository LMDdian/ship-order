# 试运行：Vue 打包 + Django 一体运行

## 1. 打包前端

在项目根目录下执行（前端目录 `frontend/ship-app`）：

```bash
cd frontend/ship-app
npm run build
```

会在 `frontend/ship-app/dist` 下生成 `index.html` 和 `assets/`。

## 2. 启动 Django

回到后端目录，按平时方式启动即可：

```bash
cd backend/ship
python manage.py runserver 0.0.0.0:8001
```

（端口按你本地习惯改，如 8000）

## 3. 访问

浏览器打开：**http://127.0.0.1:8001/**（或你配置的端口）

- 页面由 Django 直接提供 Vue 打包后的 `index.html` 和静态资源，不再单独起 Vite。
- 接口仍是 `/api/...`，同源请求，无需再配 CORS 或代理。

## 4. 说明

- `ship/settings.py` 里配置了 `FRONTEND_DIST`，指向 `frontend/ship-app/dist`（相对项目根）。
- `ship/urls.py` 在存在该目录时：
  - `/assets/*` 由 Django 从 dist 里提供；
  - 其余路径（除 `/admin/`、`/api/` 等）统一返回 `index.html`，交给前端路由。
- 若暂时不用一体运行，可删除或重命名 `dist`，Django 就不会挂载上述 SPA 路由，不影响原有 API 与 admin。
