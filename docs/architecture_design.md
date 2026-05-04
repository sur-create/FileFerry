# 架构与技术设计文档

## 1. 总体架构

本项目采用分层式应用架构：

- CLI 表现层：`fileferry/cli.py`
- GUI 表现层：`fileferry_gui/main_window.py`
- 业务层：`fileferry/sender.py`、`fileferry/receiver.py`
- 协议层：`fileferry/protocol.py`
- 进度模型层：`fileferry/progress.py`
- UI 状态层：`fileferry_gui/ui_state.py`
- 异常层：`fileferry/errors.py`

特征：

- 核心传输逻辑保持标准库实现。
- GUI 基于 PySide6，发送与接收均在后台线程执行。
- 会话级多条目传输（V1.2）与手动连接控制（V1.3）持续兼容。
- V1.4 在不破坏传输语义的前提下增加进度事件链路。

## 2. 目录结构

```text
FileFerry/
├── fileferry/
│   ├── cli.py
│   ├── errors.py
│   ├── progress.py
│   ├── protocol.py
│   ├── receiver.py
│   └── sender.py
├── fileferry_gui/
│   ├── app.py
│   ├── main_window.py
│   ├── ui_state.py
│   └── workers.py
├── packaging/
├── scripts/
├── tests/
└── docs/
```

## 3. 协议设计

### 3.1 帧格式

```text
[4-byte header_len][JSON header][binary payload(optional)]
```

消息类型：

- `session_start`
- `entry_dir`
- `entry_file`
- `entry_result`
- `session_end`
- `session_result`

### 3.2 安全约束

- `header_len` 不能为 0，且不超过 64KB。
- `relative_path` 禁止绝对路径和 `..`，防止路径穿越。
- `payload_size` 必须是非负整数。

## 4. 传输进度模型（V1.4）

### 4.1 数据结构

`TransferProgress` 字段覆盖：

- 会话维度：`total_entries`、`completed_entries`、`session_bytes_done`、`session_bytes_total`
- 条目维度：`relative_path`、`entry_bytes_done`、`entry_bytes_total`
- 运行维度：`speed_bytes_per_sec`、`eta_seconds`、`stage`、`message`

### 4.2 发送端进度链路

- `send_session` 内部按分块发送文件。
- 每个块完成后触发 `progress_callback(TransferProgress)`。
- 关键阶段：`session_start`、`entry_file`、`entry_result`、`session_end`。

### 4.3 接收端进度链路

- `receive_session_from_connection` 内部按分块接收文件。
- 每个块写入后触发进度事件。
- 关键阶段：`session_start`、`entry_file`、`entry_result`、`session_end`。

### 4.4 GUI 消费方式

- `SendSessionWorker` 与 `ReceiverServerWorker` 通过 Qt `Signal` 透传进度对象。
- `MainWindow` 更新会话进度条、条目进度条、速度/ETA 文本。

## 5. GUI 状态机（V1.4）

发送按钮由 `send_button_state` 控制：

- 未连接：`先开启连接`（禁用）
- 已连接无源：`请先添加文件`（禁用）
- 已连接且有源：`开始发送`（启用）
- 发送中：`发送中...`（禁用）

禁用态采用更高对比度样式，确保可辨识性。

## 6. 断点续传方案边界

当前版本输出调研结论，不启用正式断点续传。

建议实施路线：

1. 阶段 A：文件级断点续传（`resume_id + offset + journal`）。
2. 阶段 B：块级断点续传（引入块索引和更细粒度一致性校验）。

## 7. 错误处理策略

- `ConfigurationError`：参数非法。
- `NetworkError`：连接、监听、网络中断。
- `ProtocolError`：头部非法、字段不合法、字节流不完整。

CLI 统一输出 `error: ...` 并返回非 0。

## 8. 打包与交付

- CLI 与 GUI 双入口并存。
- 继续使用 PyInstaller + 平台安装器两层构建。
- 保持 Windows/macOS/Linux 主流安装流程兼容。
