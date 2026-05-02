from __future__ import annotations

import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

from fileferry.receiver import ReceiverConfig, receive_once
from fileferry.sender import SenderConfig, send_file


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class TransferTests(unittest.TestCase):
    def test_library_transfer(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            src_file = root / "payload.bin"
            src_file.write_bytes(os.urandom(256 * 1024 + 31))
            output_dir = root / "recv"
            output_dir.mkdir()

            port = get_free_port()
            errors: list[Exception] = []
            receiver_done: dict[str, object] = {}

            def receiver_task() -> None:
                try:
                    result = receive_once(
                        ReceiverConfig(
                            host="127.0.0.1",
                            port=port,
                            output_dir=output_dir,
                            timeout=10.0,
                        )
                    )
                    receiver_done["result"] = result
                except Exception as exc:  # pragma: no cover - assertion branch
                    errors.append(exc)

            thread = threading.Thread(target=receiver_task, daemon=True)
            thread.start()
            time.sleep(0.2)

            sent = send_file(
                SenderConfig(host="127.0.0.1", port=port, file_path=src_file, timeout=10.0)
            )
            thread.join(timeout=10.0)

            self.assertFalse(thread.is_alive(), "receiver thread did not finish in time")
            if errors:
                raise errors[0]

            target = output_dir / src_file.name
            self.assertTrue(target.exists())
            self.assertEqual(sent.sent_bytes, src_file.stat().st_size)
            self.assertEqual(target.read_bytes(), src_file.read_bytes())
            self.assertEqual(receiver_done["result"].received_bytes, src_file.stat().st_size)

    def test_cli_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            src_file = root / "note.txt"
            src_file.write_text("hello from cli integration test", encoding="utf-8")
            output_dir = root / "output"
            output_dir.mkdir()
            port = get_free_port()

            recv_cmd = [
                sys.executable,
                "-m",
                "fileferry",
                "recv",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--output-dir",
                str(output_dir),
                "--timeout",
                "10",
            ]
            recv_proc = subprocess.Popen(
                recv_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            time.sleep(0.4)

            send_cmd = [
                sys.executable,
                "-m",
                "fileferry",
                "send",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--file",
                str(src_file),
                "--timeout",
                "10",
            ]
            send_res = subprocess.run(send_cmd, capture_output=True, text=True, timeout=15)
            recv_stdout, recv_stderr = recv_proc.communicate(timeout=15)

            self.assertEqual(send_res.returncode, 0, msg=send_res.stderr or send_res.stdout)
            self.assertEqual(recv_proc.returncode, 0, msg=recv_stderr or recv_stdout)

            target = output_dir / src_file.name
            self.assertTrue(target.exists())
            self.assertEqual(target.read_text(encoding="utf-8"), src_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
