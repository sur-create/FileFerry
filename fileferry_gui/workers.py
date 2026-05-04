"""Background workers for GUI operations."""

from __future__ import annotations

import socket
import threading
from typing import Optional

from PySide6.QtCore import QThread, Signal

from fileferry.receiver import ReceiverConfig, receive_session_from_connection
from fileferry.sender import SessionSenderConfig, send_session


class SendSessionWorker(QThread):
    """Worker that sends one transfer session in the background."""

    progress = Signal(object)
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, config: SessionSenderConfig) -> None:
        super().__init__()
        self._config = config

    def run(self) -> None:  # noqa: D401
        try:
            config = SessionSenderConfig(
                host=self._config.host,
                port=self._config.port,
                sources=self._config.sources,
                timeout=self._config.timeout,
                chunk_size=self._config.chunk_size,
                conflict_policy=self._config.conflict_policy,
                continue_on_error=self._config.continue_on_error,
                progress_callback=self.progress.emit,
            )
            result = send_session(config)
        except Exception as exc:  # pragma: no cover - UI runtime branch
            self.failed.emit(str(exc))
            return
        self.completed.emit(result)


class ReceiverServerWorker(QThread):
    """Worker that keeps a receiver socket open until manually stopped."""

    progress = Signal(object)
    listening_started = Signal(str)
    listening_stopped = Signal(str)
    server_error = Signal(str)
    session_completed = Signal(object)
    session_failed = Signal(str)

    def __init__(self, config: ReceiverConfig) -> None:
        super().__init__()
        self._config = config
        self._stop_event = threading.Event()
        self._server: Optional[socket.socket] = None

    def stop(self) -> None:
        self._stop_event.set()
        server = self._server
        if server is not None:
            try:
                server.close()
            except OSError:
                pass

    def run(self) -> None:  # noqa: D401
        self._config.output_dir.mkdir(parents=True, exist_ok=True)

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                self._server = server
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind((self._config.host, self._config.port))
                server.listen(5)
                server.settimeout(0.5)
                self.listening_started.emit(
                    f"监听已开启：{self._config.host}:{self._config.port}"
                )

                while not self._stop_event.is_set():
                    try:
                        conn, addr = server.accept()
                    except socket.timeout:
                        continue
                    except OSError as exc:
                        if self._stop_event.is_set():
                            break
                        self.server_error.emit(f"监听异常：{exc}")
                        break

                    with conn:
                        try:
                            config = ReceiverConfig(
                                host=self._config.host,
                                port=self._config.port,
                                output_dir=self._config.output_dir,
                                timeout=self._config.timeout,
                                chunk_size=self._config.chunk_size,
                                conflict_policy=self._config.conflict_policy,
                                continue_on_error=self._config.continue_on_error,
                                progress_callback=self.progress.emit,
                            )
                            result = receive_session_from_connection(conn, addr, config)
                        except Exception as exc:  # pragma: no cover - UI runtime branch
                            self.session_failed.emit(f"会话失败（{addr[0]}:{addr[1]}）：{exc}")
                        else:
                            self.session_completed.emit(result)

        except OSError as exc:
            self.server_error.emit(f"无法启动监听：{exc}")
        finally:
            self._server = None
            self.listening_stopped.emit("监听已关闭")
