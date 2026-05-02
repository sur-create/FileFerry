# 用户手册

## 1. 环境要求

- Python 3.8+
- Linux / macOS / Windows（同一局域网可互通）

## 2. 启动接收端

```bash
python3 -m fileferry recv --host 0.0.0.0 --port 9000 --output-dir ./downloads
```

参数说明：

- `--host`：监听 IP，默认 `0.0.0.0`
- `--port`：监听端口（必填）
- `--output-dir`：保存目录（不填时优先使用命令入口目录；若不可写则回退到当前工作目录）
- `--conflict`：冲突策略，`overwrite|skip|rename`，默认 `overwrite`
- `--continue-on-error`：条目失败后继续（默认）
- `--fail-fast`：遇到首个失败立即停止
- `--timeout`：连接读写超时（秒）
- `--chunk-size`：每次接收块大小（字节）

## 3. 启动发送端

### 3.1 多文件/目录传输（V1.2）

```bash
python3 -m fileferry send --host 192.168.1.10 --port 9000 \
  --src ./project \
  --src ./docs/readme.txt
```

### 3.2 单文件兼容模式

```bash
python3 -m fileferry send --host 192.168.1.10 --port 9000 --file ./demo.txt
```

参数说明：

- `--host`：接收端 IP（必填）
- `--port`：接收端端口（必填）
- `--src`：源路径，可重复传多个（文件或目录）
- `--file`：单文件兼容参数（与 `--src` 互斥）
- `--conflict`：冲突策略，`overwrite|skip|rename`，默认 `overwrite`
- `--continue-on-error`：条目失败后继续（默认）
- `--fail-fast`：遇到首个失败立即停止
- `--timeout`：连接超时（秒）
- `--chunk-size`：每次发送块大小（字节）

## 4. 典型流程

1. 在目标机器运行 `recv` 命令并保持进程等待。
2. 在源机器运行 `send` 命令发送目录/文件。
3. 双方命令行显示会话摘要（总数、成功、失败、字节数、耗时）。

## 5. 常见错误

- `error: file does not exist`：发送端路径不存在。
- `error: failed to send session`：网络不通、端口未监听或被防火墙拦截。
- `error: failed to receive file`：端口被占用或监听失败。
- `entry error: ...`：某条目处理失败（路径非法、权限不足、冲突不可覆盖等）。

## 6. 限制说明（V1.2）

- 不支持断点续传。
- 不支持文件内容校验（hash）。
- 不支持传输加密与鉴权。
- 不支持并发多连接会话。
