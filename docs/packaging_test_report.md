# V1.3 打包测试报告

## 1. 测试目标

验证打包体系是否具备以下能力：

- 生成自包含 CLI 与 GUI 二进制（PyInstaller）
- 生成平台安装包（Windows/macOS/Linux）
- 提供清晰错误提示与失败退出

## 2. 本地已执行检查（2026-05-02）

- `python3 -m compileall scripts fileferry fileferry_gui`：通过
- `bash -n packaging/linux/build_deb.sh packaging/linux/build_rpm.sh packaging/macos/build_pkg.sh`：通过
- `python3 scripts/build_binary.py --help`：通过
- `python3 scripts/build_packages.py --help`：通过
- `python3 -m fileferry_gui.app`：按预期提示缺少 PySide6（当前环境未安装 GUI 依赖）
- `python3 scripts/build_binary.py`：按预期报错（缺少 PyInstaller）
- `python3 scripts/build_packages.py`：按预期报错（上游 PyInstaller 缺失）

## 3. 功能回归测试

- `python3 -m unittest discover -s tests -v`：12/12 通过（在允许 socket 权限下）。

## 4. 待在 CI/目标平台验证

- Windows：`build_inno.ps1` + `fileferry.iss` 生成 GUI + CLI 安装包
- macOS：`build_pkg.sh` 生成包含 `.app`（GUI）与 `fileferry` CLI 的 `.pkg`
- Linux：`build_deb.sh` / `build_rpm.sh` 生成含 `fileferry`（CLI）+ `fileferry-gui`（GUI）安装包

## 5. 结论

V1.3 打包流程已支持 GUI/CLI 双产物封装，脚本语法与错误处理机制通过本地校验。最终安装包产物需在具备对应打包工具链的 CI 或目标系统上执行构建验证。
