@echo off
chcp 936 >nul
cd /d "%~dp0"

echo ============================================================
echo  AC Grabber - 以调试模式启动 Edge
echo ============================================================
echo.
echo 说明:
echo   - 使用你平时的 Edge 账号、Cookie、书签
echo   - 若 Edge 正在运行, 请先关闭所有 Edge 窗口再运行本脚本
echo   - 启动后可开其他标签页, 抢稿脚本只操作稿池页
echo.
pause

set EDGE_EXE=
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    set "EDGE_EXE=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
)
if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" (
    set "EDGE_EXE=C:\Program Files\Microsoft\Edge\Application\msedge.exe"
)

if "%EDGE_EXE%"=="" (
    echo 未找到 Edge, 请手动安装 Microsoft Edge
    pause
    exit /b 1
)

set "USER_DATA=%LOCALAPPDATA%\Microsoft\Edge\User Data"

echo 关闭旧 Edge...
taskkill /IM msedge.exe /F >nul 2>&1
timeout /t 2 /nobreak >nul

echo 启动 Edge (调试端口 9222)...
start "" "%EDGE_EXE%" --remote-debugging-port=9222 --user-data-dir="%USER_DATA%" "https://ai-copywriter.risevideo.ai/distribute"

echo.
echo Edge 已启动。确认稿池页已登录后, 运行 run-cli.bat
echo.
pause
