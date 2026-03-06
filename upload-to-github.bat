@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".git" (
    git init
    echo Git 仓库已初始化。
)

git remote remove origin 2>nul
git remote add origin https://github.com/LMDdian/ship-order.git

git add .
git status

echo.
echo 请确认上面列出的文件无误后，按任意键执行提交并推送到 GitHub...
pause >nul

git commit -m "Initial commit: ship-order project"
git branch -M main
git push -u origin main

echo.
echo 若推送时要求登录，请使用 GitHub 用户名和 Personal Access Token（不是密码）。
pause
