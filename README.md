# FileFerry

基于 TCP 的局域网文件传输工具（Linux ↔ Windows ↔ macOS），支持单文件、多文件与目录递归传输，并提供中文桌面 GUI。

## 快速开始

1. 启动接收端（示例端口 `9000`）：

```bash
python3 -m fileferry recv --host 0.0.0.0 --port 9000 --output-dir ./downloads
```

2. 启动发送端（示例发送目录 + 文件）：

```bash
python3 -m fileferry send --host <接收端IP> --port 9000 \
  --src ./project \
  --src ./notes.txt
```

兼容旧命令（单文件）：

```bash
python3 -m fileferry send --host <接收端IP> --port 9000 --file ./demo.txt
```

## 桌面 GUI（V1.3）

安装 GUI 依赖：

```bash
python3 -m pip install ".[gui]"
```

启动中文图形界面：

```bash
python3 -m fileferry_gui.app
```

## 运行测试

```bash
python3 -m unittest discover -s tests -v
```

## 打包构建（V1.1）

安装开发依赖：

```bash
python3 -m pip install -r requirements-dev.txt
```

构建当前平台安装包：

```bash
python3 scripts/build_packages.py --clean
```

产物目录：

- `dist/fileferry/`：自包含可执行目录（PyInstaller）
- `dist/installer/`：平台安装包

## 文档

- 需求分析：[docs/requirements_analysis.md](docs/requirements_analysis.md)
- V1.2 需求：[docs/requirements_v1.2.md](docs/requirements_v1.2.md)
- V1.3 需求：[docs/requirements_v1.3.md](docs/requirements_v1.3.md)
- 架构设计：[docs/architecture_design.md](docs/architecture_design.md)
- 测试报告：[docs/test_report.md](docs/test_report.md)
- 用户手册：[docs/user_manual.md](docs/user_manual.md)
- Windows 安装：[docs/install_windows.md](docs/install_windows.md)
- macOS 安装：[docs/install_macos.md](docs/install_macos.md)
- Linux 安装：[docs/install_linux.md](docs/install_linux.md)
- 卸载指南：[docs/uninstall.md](docs/uninstall.md)
- 安装排障：[docs/troubleshooting_install.md](docs/troubleshooting_install.md)
- 打包测试报告：[docs/packaging_test_report.md](docs/packaging_test_report.md)
- 打包说明：[packaging/README.md](packaging/README.md)
