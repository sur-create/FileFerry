# Linux 安装指南

支持 `deb` 与 `rpm` 两种安装包。

## 1. Debian/Ubuntu

下载 `fileferry_<version>_<arch>.deb` 后执行：

```bash
sudo apt install ./fileferry_<version>_<arch>.deb
```

## 2. RHEL/CentOS/Fedora

下载 `fileferry-<version>-1.<arch>.rpm` 后执行：

```bash
sudo dnf install ./fileferry-<version>-1.<arch>.rpm
```

## 3. 安装后路径

- CLI 程序目录：`/opt/fileferry`
- GUI 程序目录：`/opt/fileferry-gui`
- 命令入口：`/usr/bin/fileferry`
- GUI 启动命令：`/usr/bin/fileferry-gui`
- 菜单项：`/usr/share/applications/fileferry.desktop`

## 4. 验证安装

```bash
fileferry --help
fileferry-gui
```

## 5. 常见安装错误

- 依赖冲突：先执行系统更新后重试（如 `sudo apt update` 或 `sudo dnf update`）。
- 权限不足：确保使用 `sudo`。
- 架构不匹配：确认包后缀架构与系统架构一致（如 `amd64`、`x86_64`、`arm64`）。
