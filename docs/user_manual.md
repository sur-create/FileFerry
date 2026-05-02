# 用户手册

## 1. 环境要求

- Python 3.8+
- Linux / macOS / Windows（同一局域网可互通）

## 2. CLI 使用

### 2.1 启动接收端

```bash
python3 -m fileferry recv --host 0.0.0.0 --port 9000 --output-dir ./downloads
```

### 2.2 启动发送端（多源）

```bash
python3 -m fileferry send --host 192.168.1.10 --port 9000 \
  --src ./project \
  --src ./docs/readme.txt
```

### 2.3 单文件兼容模式

```bash
python3 -m fileferry send --host 192.168.1.10 --port 9000 --file ./demo.txt
```

## 3. GUI 使用（V1.3）

### 3.1 安装与启动

```bash
python3 -m pip install ".[gui]"
python3 -m fileferry_gui.app
```

### 3.2 发送端操作

1. 在“发送端”页签填写目标 IP 和端口。
2. 点击“开启连接”，状态变为“已连接”。
3. 添加文件或文件夹。
4. 设置冲突策略与失败策略。
5. 点击“开始发送”。
6. 如需手动关闭，点击“断开连接”。

### 3.3 接收端操作

1. 在“接收端”页签设置监听 IP、端口、保存目录。
2. 点击“开启连接”启动监听。
3. 传输完成后可继续监听下一次会话。
4. 点击“断开连接”手动关闭监听。

## 4. 常见错误

- `error: failed to send session`：目标不可达或端口未监听。
- `entry error: ...`：单条目失败（路径非法、权限不足、冲突不可覆盖等）。
- GUI 提示“未安装 PySide6”：请先安装 GUI 依赖。

## 5. 限制说明（V1.3）

- 不支持断点续传。
- 不支持文件内容 hash 校验。
- 不支持传输加密与鉴权。
- 不支持并发多连接会话。
