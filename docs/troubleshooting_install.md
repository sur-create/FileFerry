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
