#!/bin/bash
# 网速监控工具 - 打包脚本 (Linux/macOS)

echo "==================================="
echo "  网速监控工具 - 打包脚本"
echo "==================================="
echo

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python3"
    exit 1
fi

echo "[1/4] 安装依赖..."
pip3 install psutil pyinstaller -q || {
    echo "[错误] 依赖安装失败"
    exit 1
}

echo "[2/4] 清理旧文件..."
rm -rf build dist *.spec

echo "[3/4] 打包..."
pyinstaller \
    --name "网速监控" \
    --onefile \
    --windowed \
    --noconsole \
    --clean \
    network_monitor.py

if [ $? -eq 0 ]; then
    echo
    echo "==================================="
    echo "  打包成功！"
    echo "  输出文件：dist/网速监控"
    echo "==================================="
else
    echo "[错误] 打包失败"
    exit 1
fi
