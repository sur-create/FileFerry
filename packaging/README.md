# Packaging Guide

FileFerry V1.1 打包采用“两层构建”模式：

1. `PyInstaller` 先构建自包含运行目录（`dist/fileferry`）。
2. 每个平台再构建原生安装包（输出到 `dist/installer`）。

## 快速命令

- 先安装依赖：

```bash
python3 -m pip install -r requirements-dev.txt
```

- 只构建二进制：

```bash
python3 scripts/build_binary.py --clean
```

- 构建当前平台安装包：

```bash
python3 scripts/build_packages.py --clean
```

## 平台脚本

- Windows: `packaging/windows/build_inno.ps1`
- macOS: `packaging/macos/build_pkg.sh`
- Linux DEB: `packaging/linux/build_deb.sh`
- Linux RPM: `packaging/linux/build_rpm.sh`

## 平台依赖

- Windows: Inno Setup 6 (`ISCC.exe`)
- macOS: `pkgbuild`、`productbuild`
- Linux: `dpkg-deb`、`rpmbuild`

## 产物目录

- `dist/fileferry/`：PyInstaller 产物
- `dist/installer/`：安装包产物
