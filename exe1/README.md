# 网速监控悬浮窗 v2.0

一个高颜值、功能完善的电脑网速实时监控工具。

## ✨ 功能特性

### 🎨 界面设计
- **液态玻璃风格** - 半透明现代感UI
- **深色主题** - 护眼配色
- **双模式切换** - 简洁/详细模式
- **自动保存位置** - 记住窗口位置和设置

### 📊 监控功能
- **实时网速** - 上传/下载速度
- **峰值记录** - 自动记录最高网速
- **流量统计** - 累计上传/下载
- **连接数** - 当前网络连接数量
- **历史图表** - 60秒流量趋势图
- **网卡信息** - 详细网卡状态表格

### 🛡️ 程序特性
- **单实例运行** - 防止重复启动
- **自动保存配置** - 位置、模式、透明度等
- **无控制台窗口** - 纯GUI程序
- **置顶显示** - 始终在最前

## 🚀 使用方法

### 方式1：直接运行（需要Python）
```bash
pip install psutil
python network_monitor.py
```

### 方式2：打包成EXE（推荐）

**Windows:**
```bash
build.bat
```
或手动：
```bash
pip install pyinstaller
pyinstaller --name "网速监控" --onefile --windowed --noconsole network_monitor.py
```

打包完成后会在当前目录生成 `网速监控.exe`

## 📝 操作说明

| 操作 | 说明 |
|------|------|
| 拖动窗口 | 按住标题栏拖动 |
| 切换模式 | 点击 ◀/▶ 按钮 |
| 右键菜单 | 显示更多选项 |
| 置顶控制 | 点击 📌 按钮 |
| 透明度 | 点击 👁 按钮 |

## ⚙️ 配置文件

程序会自动在用户目录创建配置文件：
- Windows: `%USERPROFILE%\.netmon_config.json`
- Linux/macOS: `~/.netmon_config.json`

包含：窗口位置、显示模式、置顶状态、透明度

## 📋 系统要求

- Windows 10/11 / Linux / macOS
- Python 3.8+ (直接运行)
- psutil 库

## 📦 文件说明

```
exe1/
├── network_monitor.py  # 主程序
├── requirements.txt    # 依赖列表
├── build.bat          # Windows打包脚本
├── build.sh           # Linux/macOS打包脚本
└── README.md          # 使用说明
```
