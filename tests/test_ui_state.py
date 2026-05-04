from __future__ import annotations

import unittest

from fileferry.progress import TransferProgress
from fileferry_gui.ui_state import (
    format_bytes,
    progress_overview,
    progress_percent,
    send_button_state,
)


class UiStateTests(unittest.TestCase):
    def test_send_button_state_auto_switch(self) -> None:
        text, enabled, _ = send_button_state(connected=False, has_sources=True, busy=False)
        self.assertEqual(text, "先开启连接")
        self.assertFalse(enabled)

        text, enabled, _ = send_button_state(connected=True, has_sources=False, busy=False)
        self.assertEqual(text, "请先添加文件")
        self.assertFalse(enabled)

        text, enabled, _ = send_button_state(connected=True, has_sources=True, busy=False)
        self.assertEqual(text, "开始发送")
        self.assertTrue(enabled)

        text, enabled, _ = send_button_state(connected=True, has_sources=True, busy=True)
        self.assertEqual(text, "发送中...")
        self.assertFalse(enabled)

    def test_progress_helpers(self) -> None:
        self.assertEqual(format_bytes(0), "0 B")
        self.assertEqual(progress_percent(5, 10), 50)

        text = progress_overview(
            TransferProgress(
                direction="send",
                stage="entry_file",
                total_entries=10,
                completed_entries=3,
                session_bytes_done=1024,
                session_bytes_total=2048,
                speed_bytes_per_sec=256,
                message="文件传输中",
            )
        )
        self.assertIn("会话进度 3/10", text)
        self.assertIn("文件传输中", text)


if __name__ == "__main__":
    unittest.main()

