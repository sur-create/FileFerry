# Windows 安装指南

## 1. 获取安装包

下载 `FileFerry-<version>-windows-x64-setup.exe`。

## 2. 安装步骤

1. 双击安装包。
2. 按向导点击 `Next` 完成安装。
3. 可选勾选桌面快捷方式。
4. 安装完成后在开始菜单可见：
   - `FileFerry`（桌面图形界面）
   - `FileFerry Help (CLI)`
   - `FileFerry Send (CLI)`
   - `FileFerry Receive (CLI)`

## 3. 验证安装

1. 在开始菜单点击 `FileFerry`，应弹出图形界面窗口。  
2. 如需验证命令行，在命令提示符执行（默认安装路径）：

```bat
"%ProgramFiles%\\FileFerry\\cli\\fileferry.exe" --help
```

若显示帮助信息即安装成功。

## 4. 常见安装错误

- `Permission denied`：请右键“以管理员身份运行”安装程序。
- `Windows Defender SmartScreen` 提示：选择“更多信息 -> 仍要运行”（内网环境使用）。
- 安装后命令不可用：重新打开终端，或确认安装目录中存在 `cli\\fileferry.exe`。
