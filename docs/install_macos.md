# macOS 安装指南

## 1. 获取安装包

下载 `FileFerry-<version>-macos.pkg`。

## 2. 安装步骤

1. 双击 `.pkg`。
2. 按安装向导完成安装。
3. 安装后会写入：
   - `/Applications/FileFerry.app`
   - `/usr/local/bin/fileferry`

## 3. 验证安装

终端执行：

```bash
fileferry --help
```

也可在 `Applications` 中打开 `FileFerry.app` 启动图形界面。

## 4. 常见安装错误

- `installer requires admin privileges`：请使用管理员账号安装。
- `cannot be opened because the developer cannot be verified`：在“系统设置 -> 隐私与安全性”中放行后重试。
- 命令不可用：确认 `/usr/local/bin` 在 `PATH` 中。
