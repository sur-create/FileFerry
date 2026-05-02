# 架构与技术设计文档

## 1. 总体架构

本项目采用分层式命令行应用架构：

- 表现层：`fileferry/cli.py`
- GUI 表现层：`fileferry_gui/main_window.py`
- 业务层：`fileferry/sender.py`、`fileferry/receiver.py`
- 协议层：`fileferry/protocol.py`
- 异常层：`fileferry/errors.py`

特征：

- 运行时业务代码零第三方依赖（仅 Python 标准库）。
- 单进程、单连接、会话级多条目传输模型（V1.2 支持多文件与目录递归）。
- V1.1 新增打包发布层，交付免 Python 环境安装包。

## 2. 目录结构

```text
FileFerry/
├── .github/workflows/
│   └── release.yml
├── fileferry/
│   ├── __main__.py
│   ├── cli.py
│   ├── errors.py
│   ├── protocol.py
│   ├── receiver.py
│   └── sender.py
├── fileferry_gui/
│   ├── app.py
│   ├── main_window.py
│   └── workers.py
├── packaging/
│   ├── pyinstaller/
│   ├── windows/
│   ├── macos/
│   └── linux/
├── scripts/
│   ├── build_binary.py
│   └── build_packages.py
├── tests/
│   ├── test_protocol.py
│   └── test_transfer.py
└── docs/
    ├── requirements_analysis.md
    ├── architecture_design.md
    ├── test_report.md
    ├── user_manual.md
    ├── install_windows.md
    ├── install_macos.md
    ├── install_linux.md
    └── uninstall.md
```

## 3. 协议设计

### 3.1 二进制格式

1. `header_length`：4 字节无符号整数，网络字节序（big-endian）。
2. `header_json`：UTF-8 JSON，会话帧字段示例：
   - `type: session_start|entry_dir|entry_file|entry_result|session_end|session_result`
   - `relative_path: string`（仅条目帧）
   - `payload_size: int`（文件条目为文件字节数）
3. `file_bytes`：当 `type=entry_file` 时附带原始文件字节流，长度等于 `payload_size`。

### 3.2 协议防御

- `header_length` 不能为 0，且上限 64KB。
- `relative_path` 禁止绝对路径与 `..`（防路径穿越）。
- `payload_size` 必须为非负整数。

## 4. API 接口设计

> 该项目无 HTTP API，接口形态为 CLI + Socket 协议。

### 4.1 CLI 命令接口

- 发送端：

```bash
python3 -m fileferry send --host <IP> --port <PORT> \
  (--file <FILE> | --src <PATH> [--src <PATH> ...]) \
  [--conflict overwrite|skip|rename] \
  [--continue-on-error|--fail-fast] \
  [--timeout 10] [--chunk-size 65536]
```

- 接收端：

```bash
python3 -m fileferry recv --host 0.0.0.0 --port <PORT> \
  [--output-dir DIR] \
  [--conflict overwrite|skip|rename] \
  [--continue-on-error|--fail-fast] \
  [--timeout 10] [--chunk-size 65536]
```

### 4.2 代码级接口

- `sender.send_session(SessionSenderConfig) -> SendSessionResult`
- `receiver.receive_session(ReceiverConfig) -> ReceiveSessionResult`
- 兼容接口：`sender.send_file(SenderConfig)`、`receiver.receive_once(ReceiverConfig)`
- GUI 入口：`fileferry_gui.app:main`（`fileferry-gui` 命令）

## 5. 数据建模

## 5.1 V1.0 持久化策略

- V1.0 不要求数据库；文件系统即最终存储。
- 元数据在传输期间以内存对象表示：`FileMetadata`。

## 5.2 概念模型（内存）

| 实体 | 字段 | 说明 |
|---|---|---|
| FileMetadata | filename, filesize | 协议头部元数据 |
| SendResult | filename, filesize, sent_bytes, remote_host, remote_port | 发送结果 |
| ReceiveResult | filename, filesize, received_bytes, output_path, peer_host, peer_port | 接收结果 |

## 5.3 后续可扩展数据库模型（非 V1.0 必需）

如需审计日志，可新增 `transfer_log` 表：

- `id` (PK)
- `direction` (`send`/`recv`)
- `filename`
- `filesize`
- `remote_addr`
- `status`
- `created_at`

## 6. 关键技术决策

- 使用 `socket.create_connection` 简化连接与超时处理。
- 使用 `recv_exact` 处理 TCP 分包，避免粘包导致的协议错误。
- 使用分块读写降低内存占用，适配大文件。

## 7. 错误处理策略

- `ConfigurationError`：参数非法、文件不存在。
- `NetworkError`：连接失败、监听失败、端口冲突。
- `ProtocolError`：头部非法、连接提前断开、字节不完整。

CLI 统一捕获并输出 `error: <detail>`，返回非零退出码。

## 8. 前端界面实现说明

- 依据需求文档，前端形态为命令行交互界面（CLI），不包含 Web GUI。
- CLI 输出包含监听状态、发送结果、接收结果与错误信息，满足可操作性要求。

## 9. 安装包架构（V1.1）

### 9.1 构建分层

1. PyInstaller 产出自包含运行目录（`dist/fileferry`）。
2. 平台安装器将运行目录封装为可安装包：
   - Windows：Inno Setup (`.exe`)
   - macOS：pkgbuild/productbuild (`.pkg`)
   - Linux：`dpkg-deb` (`.deb`) + `rpmbuild` (`.rpm`)

### 9.2 快捷方式与入口

- Windows：开始菜单与可选桌面快捷方式，指向命令帮助/发送/接收入口。
- macOS：`/Applications/FileFerry.app` + `/usr/local/bin/fileferry`。
- Linux：`/usr/bin/fileferry` + `.desktop` 菜单项。

### 9.3 卸载机制

- Windows：控制面板/设置中标准卸载（Inno 自动注册）。
- macOS：提供卸载脚本 `/usr/local/share/fileferry/uninstall_fileferry.sh`。
- Linux：通过包管理器标准卸载（`apt remove` / `dnf remove`）。

## 10. GUI 架构（V1.3）

- 窗口层：`MainWindow` 负责中文 UI、状态展示、按钮交互。
- 后台线程：
  - `SendSessionWorker`：异步发送会话，避免阻塞界面。
  - `ReceiverServerWorker`：持续监听，支持手动开启/断开连接。
- 连接控制：
  - 发送端：手动“开启连接/断开连接”（连接可达性检查 + 状态门控）。
  - 接收端：手动开启监听与关闭监听，监听周期内可处理多次会话。
