# ship-order 打单发货

订单与发货管理：前端 `ship-app`（Vue3 + Vite + Vant），后端 `ship`（Django）。

## 项目结构

- **ship-app/** — 移动端前端（订单、个人、统计；录单/发货）
- **ship/** — Django 后端 API（端口 8001）

## 快速开始

1. 后端：`ship/README.md` 中查看数据库与运行方式
2. 前端：`ship-app/README.md` 中查看 `npm install` 与 `npm run dev`（默认端口 5174，代理到 8001）

## 上传到 GitHub

首次上传可双击运行项目根目录下的 **`upload-to-github.bat`**，或在项目根目录打开终端执行：

```bash
git init
git remote add origin https://github.com/LMDdian/ship-order.git
git add .
git commit -m "Initial commit: ship-order project"
git branch -M main
git push -u origin main
```

推送时如要求登录，请使用 GitHub 用户名和 **Personal Access Token**（在 GitHub → Settings → Developer settings → Personal access tokens 创建）。
