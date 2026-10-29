@echo off
chcp 65001 >nul
title 草屯生活處方服務點資料 同步至 iPad
echo ========================================================
echo   正在將 PC 端更新補充之服務點說明與圖片同步至 iPad...
echo ========================================================
python "C:\Users\tsai_\OneDrive\桌面\20261015_南投草屯\南投縣草屯鎮生活處方完整版\sync_and_publish.py"
echo.
echo 完成！請在 iPad 上重新整理網頁，或點選頂部「🔄 同步最新資料」。
pause
