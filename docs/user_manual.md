# 用户手册

## 1. 环境要求

- Python 3.8+
- Linux / Windows（同一局域网可互通）

## 2. 启动接收端

```bash
python3 -m fileferry recv --host 0.0.0.0 --port 9000 --output-dir ./downloads
```

参数说明：

- `--host`：监听 IP，默认 `0.0.0.0`
- `--port`：监听端口（必填）
- `--output-dir`：保存目录（不填时优先使用命令入口目录；若不可写则回退到当前工作目录）
- `--timeout`：连接读写超时（秒）
- `--chunk-size`：每次接收块大小（字节）

## 3. 启动发送端

```bash
python3 -m fileferry send --host 192.168.1.10 --port 9000 --file ./demo.txt
```

参数说明：

- `--host`：接收端 IP（必填）
- `--port`：接收端端口（必填）
- `--file`：本地文件路径（必填）
- `--timeout`：连接超时（秒）
- `--chunk-size`：每次发送块大小（字节）

## 4. 典型流程

1. 在目标机器运行 `recv` 命令并保持进程等待。
2. 在源机器运行 `send` 命令发送文件。
3. 接收端显示 `received ...` 即表示传输完成。

## 5. 常见错误

- `error: file does not exist`：发送文件路径错误。
- `error: failed to send file`：网络不通、端口未监听或被防火墙拦截。
- `error: failed to receive file`：端口被占用或监听失败。
- `error: invalid JSON header`：对端未按协议发送。

## 6. 限制说明（V1.0）

- 仅支持单文件。
- 不支持断点续传、校验和、加密、并发传输。
