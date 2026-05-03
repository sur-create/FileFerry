# 安装与运行排障

## 1. 安装完成但命令不可用

- 重新打开终端会话。
- 检查路径：
  - macOS/Linux: `which fileferry`
  - Windows: `where fileferry`

## 2. 启动时报找不到运行时

症状：提示 `runtime not found`。

处理：

- 确认安装目录未被手动删改。
- 执行卸载后重新安装。

## 2.1 GUI 无法启动（缺少 PySide6）

症状：`未安装 PySide6，无法启动图形界面`。

处理：

```bash
python3 -m pip install ".[gui]"
```

## 2.2 Linux 安装后点击图标无反应

症状：

- 菜单中点击 FileFerry 没有窗口。
- 终端执行 `fileferry-gui` 提示 `command not found` 或 `runtime not found`。

处理：

1. 确认安装包是否包含 GUI 运行时：

```bash
dpkg -L fileferry 2>/dev/null | grep -E 'fileferry-gui|/opt/fileferry-gui'
```

2. 如果没有任何输出，说明当前安装的是旧版 CLI-only 包，请卸载并安装 V1.3+ Linux 安装包。
3. 如果命令存在但仍无法启动，查看 GUI 启动日志：

```bash
cat ~/.local/state/fileferry/gui-launch.log
```

## 2.3 Linux 报错：Qt platform plugin "xcb" 无法加载

常见日志（你当前就是这个）：

- `x... xcb-cursor0 or libxcb-cursor0 is needed`
- `Could not load the Qt platform plugin "xcb"`

处理：

- Debian/Ubuntu:

```bash
sudo apt update
sudo apt install -y \
  libxcb-cursor0 \
  libxkbcommon-x11-0 \
  libxcb-icccm4 \
  libxcb-image0 \
  libxcb-keysyms1 \
  libxcb-render-util0 \
  libxcb-xinerama0
```

- Fedora/RHEL/CentOS:

```bash
sudo dnf install -y xcb-util-cursor
```

安装后重新执行 `fileferry-gui`。
若仍失败，请把 `~/.local/state/fileferry/gui-launch.log` 的最新 30 行贴出来。

## 3. 端口监听失败

症状：`failed to receive file`。

处理：

- 更换端口（如 `9000 -> 19000`）。
- 检查防火墙与端口占用。

## 4. 发送端连接失败

症状：`failed to send file`。

处理：

- 确认接收端已先启动并监听正确地址。
- 使用 `ping` 或 `telnet <ip> <port>` 验证网络可达。
- 确认双方在同一局域网且无 ACL 阻断。

## 5. 安装器构建失败（开发侧）

- 缺少工具：按平台安装 `PyInstaller`、`Inno Setup`、`rpmbuild`、`pkgbuild`。
- 先执行：

```bash
python3 scripts/build_binary.py --clean
```

再执行平台安装脚本。
