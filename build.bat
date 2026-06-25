@echo off
chcp 936 >nul
cd /d "%~dp0"

echo ============================================================
echo  打包 AC Grabber GUI
echo ============================================================
echo.

pip install -r requirements.txt -q
pip install playwright -q

echo 正在打包...
pyinstaller --noconfirm --onefile --windowed ^
  --name "ac-grabber-gui" ^
  --add-data "start-edge.bat;." ^
  app_gui.py

if exist "dist\ac-grabber-gui.exe" (
    copy /y "start-edge.bat" "dist\" >nul
    echo.
    echo 完成! 输出目录: dist\
    echo   - ac-grabber-gui.exe
    echo   - start-edge.bat
) else (
    echo 打包失败
)

pause
