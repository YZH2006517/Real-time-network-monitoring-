@echo off
chcp 65001 >nul
echo ===================================
echo   网速监控工具 - 打包脚本
echo ===================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [1/4] 安装依赖...
pip install psutil pyinstaller -q
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

echo [2/4] 清理旧文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del /q "*.spec"

echo [3/4] 打包 EXE...
pyinstaller ^
    --name "网速监控" ^
    --onefile ^
    --windowed ^
    --noconsole ^
    --icon=NONE ^
    --clean ^
    --add-data "requirements.txt;." ^
    network_monitor.py

if errorlevel 1 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo [4/4] 复制文件...
if exist "dist\网速监控.exe" (
    copy "dist\网速监控.exe" "网速监控.exe" >nul
    echo.
    echo ===================================
    echo   打包成功！
    echo   输出文件：网速监控.exe
    echo ===================================
) else (
    echo [错误] 未找到输出文件
    pause
    exit /b 1
)

echo.
echo 按任意键退出...
pause >nul
