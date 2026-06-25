@echo off
chcp 936 >nul
cd /d "%~dp0"

echo ============================================================
echo  打包 AI Copywriter 抢稿助手
echo ============================================================
echo.

pip install -r requirements.txt -q
pip install playwright -q

echo 正在打包...
pyinstaller --noconfirm --onefile --windowed ^
  --name "AC抢稿助手" ^
  --add-data "start_edge_debug.bat;." ^
  app_gui.py

if exist "dist\AC抢稿助手.exe" (
    copy /y "start_edge_debug.bat" "dist\" >nul
    echo.
    echo 完成! 输出目录: dist\
    echo   - AC抢稿助手.exe
    echo   - start_edge_debug.bat
) else (
    echo 打包失败
)

pause
