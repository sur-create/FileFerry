from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fileferry.cli import default_output_dir


class CliTests(unittest.TestCase):
    def test_default_output_dir_prefers_executable_dir_when_writable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake_exe = Path(tmp) / "fileferry"
            fake_exe.write_text("x", encoding="utf-8")
            with mock.patch.object(sys, "argv", [str(fake_exe)]):
                with mock.patch("fileferry.cli.os.access", return_value=True):
                    self.assertEqual(default_output_dir(), Path(tmp))

    def test_default_output_dir_falls_back_to_cwd_when_not_writable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake_exe = Path(tmp) / "fileferry"
            fake_exe.write_text("x", encoding="utf-8")
            with mock.patch.object(sys, "argv", [str(fake_exe)]):
                with mock.patch("fileferry.cli.os.access", return_value=False):
                    self.assertEqual(default_output_dir(), Path.cwd())


if __name__ == "__main__":
    unittest.main()
