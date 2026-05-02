"""GUI entrypoint for FileFerry."""

from __future__ import annotations

import sys


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except Exception as exc:  # pragma: no cover - runtime only
        print("错误：未安装 PySide6，无法启动图形界面。")
        print("请先执行：python3 -m pip install PySide6")
        print(f"详细信息：{exc}")
        return 1

    from .main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("FileFerry")
    app.setOrganizationName("FileFerry")

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
