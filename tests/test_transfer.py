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

from fileferry.receiver import ReceiverConfig, receive_once, receive_session
from fileferry.sender import SenderConfig, SessionSenderConfig, send_file, send_session


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class TransferTests(unittest.TestCase):
    def _run_receiver_session(
        self,
        port: int,
        output_dir: Path,
        conflict_policy: str = "overwrite",
    ) -> tuple[threading.Thread, list[Exception], dict[str, object]]:
        errors: list[Exception] = []
        state: dict[str, object] = {}

        def receiver_task() -> None:
            try:
                state["result"] = receive_session(
                    ReceiverConfig(
                        host="127.0.0.1",
                        port=port,
                        output_dir=output_dir,
                        timeout=10.0,
                        conflict_policy=conflict_policy,
                    )
                )
            except Exception as exc:  # pragma: no cover - assertion branch
                errors.append(exc)

        thread = threading.Thread(target=receiver_task, daemon=True)
        thread.start()
        time.sleep(0.2)
        return thread, errors, state

    def test_legacy_single_file_wrappers(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            src_file = root / "payload.bin"
            src_file.write_bytes(os.urandom(128 * 1024 + 7))
            output_dir = root / "recv"
            output_dir.mkdir()

            port = get_free_port()
            errors: list[Exception] = []
            state: dict[str, object] = {}

            def receiver_task() -> None:
                try:
                    state["result"] = receive_once(
                        ReceiverConfig(
                            host="127.0.0.1",
                            port=port,
                            output_dir=output_dir,
                            timeout=10.0,
                        )
                    )
                except Exception as exc:  # pragma: no cover - assertion branch
                    errors.append(exc)

            thread = threading.Thread(target=receiver_task, daemon=True)
            thread.start()
            time.sleep(0.2)

            sent = send_file(SenderConfig(host="127.0.0.1", port=port, file_path=src_file, timeout=10.0))
            thread.join(timeout=10.0)

            self.assertFalse(thread.is_alive(), "receiver thread did not finish in time")
            if errors:
                raise errors[0]

            target = output_dir / src_file.name
            self.assertTrue(target.exists())
            self.assertEqual(sent.sent_bytes, src_file.stat().st_size)
            self.assertEqual(target.read_bytes(), src_file.read_bytes())
            self.assertEqual(state["result"].received_bytes, src_file.stat().st_size)

    def test_library_multi_source_recursive_and_mtime(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            src_dir = root / "project"
            (src_dir / "nested").mkdir(parents=True)
            (src_dir / "empty").mkdir()

            text_file = src_dir / "nested" / "hello.txt"
            text_file.write_text("hello v1.2", encoding="utf-8")
            fixed_mtime = int(time.time()) - 3600
            os.utime(text_file, (fixed_mtime, fixed_mtime))

            extra_file = root / "notes.md"
            extra_file.write_text("notes", encoding="utf-8")

            symlink_dir = root / "linked_nested"
            try:
                symlink_dir.symlink_to(src_dir / "nested", target_is_directory=True)
            except (NotImplementedError, OSError, PermissionError):
                self.skipTest("symlink creation is not supported in current environment")

            output_dir = root / "recv"
            output_dir.mkdir()
            port = get_free_port()

            thread, errors, state = self._run_receiver_session(port, output_dir, conflict_policy="overwrite")

            sent = send_session(
                SessionSenderConfig(
                    host="127.0.0.1",
                    port=port,
                    sources=[src_dir, extra_file, symlink_dir],
                    timeout=10.0,
                    conflict_policy="overwrite",
                    continue_on_error=True,
                )
            )
            thread.join(timeout=10.0)

            self.assertFalse(thread.is_alive(), "receiver thread did not finish in time")
            if errors:
                raise errors[0]

            recv_result = state["result"]
            self.assertEqual(sent.failed_entries, 0)
            self.assertEqual(recv_result.failed_entries, 0)

            self.assertEqual((output_dir / "project" / "nested" / "hello.txt").read_text("utf-8"), "hello v1.2")
            self.assertTrue((output_dir / "project" / "empty").is_dir())
            self.assertEqual((output_dir / "notes.md").read_text("utf-8"), "notes")
            self.assertEqual((output_dir / "linked_nested" / "hello.txt").read_text("utf-8"), "hello v1.2")

            received_mtime = int((output_dir / "project" / "nested" / "hello.txt").stat().st_mtime)
            self.assertLessEqual(abs(received_mtime - fixed_mtime), 1)

    def test_conflict_rename_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            src_file = root / "dup.txt"
            src_file.write_text("new content", encoding="utf-8")

            output_dir = root / "recv"
            output_dir.mkdir()
            existing = output_dir / "dup.txt"
            existing.write_text("old content", encoding="utf-8")

            port = get_free_port()
            thread, errors, state = self._run_receiver_session(port, output_dir, conflict_policy="rename")

            sent = send_session(
                SessionSenderConfig(
                    host="127.0.0.1",
                    port=port,
                    sources=[src_file],
                    timeout=10.0,
                    conflict_policy="rename",
                    continue_on_error=True,
                )
            )
            thread.join(timeout=10.0)

            self.assertFalse(thread.is_alive(), "receiver thread did not finish in time")
            if errors:
                raise errors[0]

            recv_result = state["result"]
            self.assertEqual(sent.failed_entries, 0)
            self.assertEqual(recv_result.failed_entries, 0)
            self.assertEqual(sent.renamed_entries, 1)
            self.assertEqual(recv_result.renamed_entries, 1)

            self.assertEqual(existing.read_text("utf-8"), "old content")
            self.assertEqual((output_dir / "dup (1).txt").read_text("utf-8"), "new content")

    def test_conflict_skip_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            src_file = root / "same.txt"
            src_file.write_text("incoming", encoding="utf-8")

            output_dir = root / "recv"
            output_dir.mkdir()
            existing = output_dir / "same.txt"
            existing.write_text("existing", encoding="utf-8")

            port = get_free_port()
            thread, errors, state = self._run_receiver_session(port, output_dir, conflict_policy="skip")

            sent = send_session(
                SessionSenderConfig(
                    host="127.0.0.1",
                    port=port,
                    sources=[src_file],
                    timeout=10.0,
                    conflict_policy="skip",
                    continue_on_error=True,
                )
            )
            thread.join(timeout=10.0)

            self.assertFalse(thread.is_alive(), "receiver thread did not finish in time")
            if errors:
                raise errors[0]

            recv_result = state["result"]
            self.assertEqual(sent.failed_entries, 0)
            self.assertEqual(recv_result.failed_entries, 0)
            self.assertEqual(sent.skipped_entries, 1)
            self.assertEqual(recv_result.skipped_entries, 1)
            self.assertEqual(existing.read_text("utf-8"), "existing")

    def test_sender_policy_overrides_receiver_default(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            src_file = root / "same.txt"
            src_file.write_text("incoming", encoding="utf-8")

            output_dir = root / "recv"
            output_dir.mkdir()
            existing = output_dir / "same.txt"
            existing.write_text("existing", encoding="utf-8")

            port = get_free_port()
            # Receiver defaults to overwrite, sender asks skip through session_start.
            thread, errors, state = self._run_receiver_session(port, output_dir, conflict_policy="overwrite")

            sent = send_session(
                SessionSenderConfig(
                    host="127.0.0.1",
                    port=port,
                    sources=[src_file],
                    timeout=10.0,
                    conflict_policy="skip",
                    continue_on_error=True,
                )
            )
            thread.join(timeout=10.0)

            self.assertFalse(thread.is_alive(), "receiver thread did not finish in time")
            if errors:
                raise errors[0]

            recv_result = state["result"]
            self.assertEqual(sent.failed_entries, 0)
            self.assertEqual(recv_result.failed_entries, 0)
            self.assertEqual(sent.skipped_entries, 1)
            self.assertEqual(recv_result.skipped_entries, 1)
            self.assertEqual(existing.read_text("utf-8"), "existing")

    def test_cli_end_to_end_multi_source(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            src_dir = root / "send_dir"
            src_dir.mkdir()
            (src_dir / "a.txt").write_text("A", encoding="utf-8")
            extra = root / "b.txt"
            extra.write_text("B", encoding="utf-8")

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
                "--src",
                str(src_dir),
                "--src",
                str(extra),
                "--timeout",
                "10",
            ]
            send_res = subprocess.run(send_cmd, capture_output=True, text=True, timeout=20)
            recv_stdout, recv_stderr = recv_proc.communicate(timeout=20)

            self.assertEqual(send_res.returncode, 0, msg=send_res.stderr or send_res.stdout)
            self.assertEqual(recv_proc.returncode, 0, msg=recv_stderr or recv_stdout)

            self.assertEqual((output_dir / "send_dir" / "a.txt").read_text("utf-8"), "A")
            self.assertEqual((output_dir / "b.txt").read_text("utf-8"), "B")

    def test_send_progress_callback_emits_events(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            src_file = root / "progress.bin"
            src_file.write_bytes(os.urandom(256 * 1024))

            output_dir = root / "recv"
            output_dir.mkdir()
            port = get_free_port()

            thread, errors, _ = self._run_receiver_session(port, output_dir, conflict_policy="overwrite")

            events: list[object] = []

            sent = send_session(
                SessionSenderConfig(
                    host="127.0.0.1",
                    port=port,
                    sources=[src_file],
                    timeout=10.0,
                    conflict_policy="overwrite",
                    continue_on_error=True,
                    progress_callback=events.append,
                )
            )
            thread.join(timeout=10.0)

            self.assertFalse(thread.is_alive(), "receiver thread did not finish in time")
            if errors:
                raise errors[0]

            self.assertEqual(sent.failed_entries, 0)
            self.assertGreater(len(events), 0)
            stages = [getattr(event, "stage", "") for event in events]
            self.assertIn("session_start", stages)
            self.assertIn("entry_file", stages)
            self.assertIn("session_end", stages)


if __name__ == "__main__":
    unittest.main()
