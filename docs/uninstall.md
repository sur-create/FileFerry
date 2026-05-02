# 卸载指南

## Windows

1. 打开“设置 -> 应用 -> 已安装的应用”。
2. 选择 `FileFerry`。
3. 点击“卸载”。

或在控制面板“程序和功能”中卸载。

## macOS

标准方式：

1. 删除 `/Applications/FileFerry.app`。
2. 删除 `/usr/local/bin/fileferry`。
3. 删除 `/usr/local/share/fileferry`（可选，包含卸载脚本）。

如需一次性清理：

```bash
sudo /usr/local/share/fileferry/uninstall_fileferry.sh
```

## Linux

- Debian/Ubuntu：

```bash
sudo apt remove fileferry
```

- RHEL/CentOS/Fedora：

```bash
sudo dnf remove fileferry
```
