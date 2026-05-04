"""File sender implementation."""

from __future__ import annotations

import socket
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Sequence, Set, Tuple

from .errors import ConfigurationError, NetworkError, ProtocolError
from .protocol import (
    PROTOCOL_VERSION,
    payload_size_from_header,
    sanitize_relative_path,
    send_frame_header,
    recv_frame_header,
)
from .progress import TransferProgress

DEFAULT_CHUNK_SIZE = 64 * 1024
VALID_CONFLICT_POLICIES = {"overwrite", "skip", "rename"}


@dataclass(frozen=True)
class SenderConfig:
    host: str
    port: int
    file_path: Path
    timeout: float = 10.0
    chunk_size: int = DEFAULT_CHUNK_SIZE


@dataclass(frozen=True)
class SendResult:
    filename: str
    filesize: int
    sent_bytes: int
    remote_host: str
    remote_port: int


@dataclass(frozen=True)
class SessionSenderConfig:
    host: str
    port: int
    sources: Sequence[Path]
    timeout: float = 10.0
    chunk_size: int = DEFAULT_CHUNK_SIZE
    conflict_policy: str = "overwrite"
    continue_on_error: bool = True
    progress_callback: Optional[Callable[[TransferProgress], None]] = None


@dataclass(frozen=True)
class ManifestEntry:
    kind: str
    relative_path: str
    source_path: Optional[Path] = None
    filesize: int = 0
    mtime: int = 0


@dataclass(frozen=True)
class EntryTransferResult:
    relative_path: str
    kind: str
    status: str
    detail: str = ""
    saved_path: Optional[str] = None
    bytes_sent: int = 0


@dataclass(frozen=True)
class SendSessionResult:
    remote_host: str
    remote_port: int
    total_entries: int
    successful_entries: int
    failed_entries: int
    skipped_entries: int
    renamed_entries: int
    total_bytes_sent: int
    elapsed_seconds: float
    entry_results: Tuple[EntryTransferResult, ...]


def _validate_sender_config(config: SessionSenderConfig) -> None:
    if not config.host:
        raise ConfigurationError("target host is required")
    if config.port < 1 or config.port > 65535:
        raise ConfigurationError("port must be in range 1-65535")
    if config.timeout <= 0:
        raise ConfigurationError("timeout must be greater than 0")
    if config.chunk_size <= 0:
        raise ConfigurationError("chunk size must be greater than 0")
    if not config.sources:
        raise ConfigurationError("at least one source path is required")
    if config.conflict_policy not in VALID_CONFLICT_POLICIES:
        raise ConfigurationError(
            f"conflict policy must be one of: {', '.join(sorted(VALID_CONFLICT_POLICIES))}"
        )


def _root_label_for_source(source: Path) -> str:
    if source.name:
        label = source.name
    else:
        try:
            resolved_name = source.resolve().name
        except Exception:
            resolved_name = ""
        label = resolved_name or "source"
    return sanitize_relative_path(label)


def _append_manifest_failure(
    failures: List[EntryTransferResult],
    relative_path: str,
    kind: str,
    detail: str,
) -> None:
    failures.append(
        EntryTransferResult(
            relative_path=relative_path,
            kind=kind,
            status="error",
            detail=detail,
        )
    )


def _emit_progress(
    callback: Optional[Callable[[TransferProgress], None]],
    progress: TransferProgress,
) -> None:
    if callback is not None:
        callback(progress)


def _walk_source(
    source_path: Path,
    relative_path: str,
    entries: List[ManifestEntry],
    failures: List[EntryTransferResult],
    active_real_dirs: Set[str],
) -> None:
    try:
        stat_info = source_path.stat()
    except OSError as exc:
        _append_manifest_failure(failures, relative_path, "source", f"unable to stat source: {exc}")
        return

    if source_path.is_dir():
        try:
            real_dir = str(source_path.resolve())
        except (OSError, RuntimeError) as exc:
            _append_manifest_failure(failures, relative_path, "dir", f"unable to resolve directory: {exc}")
            return

        if real_dir in active_real_dirs:
            _append_manifest_failure(
                failures,
                relative_path,
                "dir",
                "symlink loop detected while following directory links",
            )
            return

        entries.append(ManifestEntry(kind="dir", relative_path=relative_path))
        next_active = set(active_real_dirs)
        next_active.add(real_dir)

        try:
            children = sorted(source_path.iterdir(), key=lambda item: item.name)
        except OSError as exc:
            _append_manifest_failure(failures, relative_path, "dir", f"unable to list directory: {exc}")
            return

        for child in children:
            try:
                child_rel = sanitize_relative_path(f"{relative_path}/{child.name}")
            except ProtocolError as exc:
                _append_manifest_failure(
                    failures,
                    relative_path,
                    "dir",
                    f"invalid child path '{child.name}': {exc}",
                )
                continue
            _walk_source(child, child_rel, entries, failures, next_active)
        return

    if source_path.is_file():
        entries.append(
            ManifestEntry(
                kind="file",
                relative_path=relative_path,
                source_path=source_path,
                filesize=stat_info.st_size,
                mtime=int(stat_info.st_mtime),
            )
        )
        return

    _append_manifest_failure(
        failures,
        relative_path,
        "source",
        "unsupported source type (only regular files and directories are supported)",
    )


def build_manifest(sources: Sequence[Path]) -> Tuple[List[ManifestEntry], List[EntryTransferResult]]:
    entries: List[ManifestEntry] = []
    failures: List[EntryTransferResult] = []

    for raw_source in sources:
        source = raw_source.expanduser()
        try:
            source = source.absolute()
        except Exception:
            source = source

        try:
            root_rel = _root_label_for_source(source)
        except ProtocolError as exc:
            _append_manifest_failure(
                failures,
                "source",
                "source",
                f"invalid source root name '{source.name}': {exc}",
            )
            continue
        _walk_source(source, root_rel, entries, failures, set())
    return entries, failures


def _recv_entry_result_from_socket(sock: socket.socket) -> EntryTransferResult:
    header = recv_frame_header(sock)
    message_type = header.get("type")
    if message_type != "entry_result":
        raise ProtocolError(f"expected 'entry_result' frame, got '{message_type}'")

    payload_size = payload_size_from_header(header)
    if payload_size != 0:
        raise ProtocolError("entry_result payload_size must be zero")

    relative_path = header.get("relative_path", "")
    kind = header.get("kind", "")
    status = header.get("status", "")
    detail = header.get("detail", "")
    saved_path = header.get("saved_path")

    if not isinstance(relative_path, str):
        raise ProtocolError("entry_result.relative_path must be a string")
    if not isinstance(kind, str):
        raise ProtocolError("entry_result.kind must be a string")
    if not isinstance(status, str):
        raise ProtocolError("entry_result.status must be a string")
    if not isinstance(detail, str):
        raise ProtocolError("entry_result.detail must be a string")
    if saved_path is not None and not isinstance(saved_path, str):
        raise ProtocolError("entry_result.saved_path must be a string")

    if relative_path:
        sanitize_relative_path(relative_path)
    if saved_path:
        sanitize_relative_path(saved_path)

    return EntryTransferResult(
        relative_path=relative_path,
        kind=kind,
        status=status,
        detail=detail,
        saved_path=saved_path,
    )


def send_session(config: SessionSenderConfig) -> SendSessionResult:
    _validate_sender_config(config)

    manifest_entries, preflight_failures = build_manifest(config.sources)

    results: List[EntryTransferResult] = list(preflight_failures)
    if preflight_failures and not config.continue_on_error:
        failed_entries = len(preflight_failures)
        return SendSessionResult(
            remote_host=config.host,
            remote_port=config.port,
            total_entries=failed_entries,
            successful_entries=0,
            failed_entries=failed_entries,
            skipped_entries=0,
            renamed_entries=0,
            total_bytes_sent=0,
            elapsed_seconds=0.0,
            entry_results=tuple(results),
        )

    total_bytes_sent = 0
    start = time.perf_counter()
    aborted = False
    progress_callback = config.progress_callback
    session_bytes_total = sum(entry.filesize for entry in manifest_entries if entry.kind == "file")
    completed_entries = 0

    try:
        with socket.create_connection((config.host, config.port), timeout=config.timeout) as sock:
            send_frame_header(
                sock,
                {
                    "type": "session_start",
                    "payload_size": 0,
                    "protocol_version": PROTOCOL_VERSION,
                    "conflict_policy": config.conflict_policy,
                    "continue_on_error": config.continue_on_error,
                    "entry_count": len(manifest_entries),
                    "total_file_bytes": session_bytes_total,
                },
            )
            _emit_progress(
                progress_callback,
                TransferProgress(
                    direction="send",
                    stage="session_start",
                    total_entries=len(manifest_entries),
                    completed_entries=0,
                    session_bytes_done=0,
                    session_bytes_total=session_bytes_total,
                    message="会话已开始",
                ),
            )

            for index, entry in enumerate(manifest_entries, start=1):
                if entry.kind == "dir":
                    send_frame_header(
                        sock,
                        {
                            "type": "entry_dir",
                            "payload_size": 0,
                            "relative_path": entry.relative_path,
                        },
                    )
                    _emit_progress(
                        progress_callback,
                        TransferProgress(
                            direction="send",
                            stage="entry_dir",
                            total_entries=len(manifest_entries),
                            completed_entries=completed_entries,
                            current_index=index,
                            relative_path=entry.relative_path,
                            kind="dir",
                            session_bytes_done=total_bytes_sent,
                            session_bytes_total=session_bytes_total,
                            message="目录已发送",
                        ),
                    )
                else:
                    assert entry.source_path is not None
                    send_frame_header(
                        sock,
                        {
                            "type": "entry_file",
                            "payload_size": entry.filesize,
                            "relative_path": entry.relative_path,
                            "mtime": entry.mtime,
                        },
                    )
                    sent = 0
                    last_emit = time.perf_counter()
                    with entry.source_path.open("rb") as fp:
                        while True:
                            chunk = fp.read(config.chunk_size)
                            if not chunk:
                                break
                            sock.sendall(chunk)
                            sent += len(chunk)
                            total_bytes_sent += len(chunk)
                            now = time.perf_counter()
                            if now - last_emit >= 0.1 or sent == entry.filesize:
                                elapsed = max(now - start, 1e-9)
                                speed = total_bytes_sent / elapsed
                                remaining = max(session_bytes_total - total_bytes_sent, 0)
                                eta = remaining / speed if speed > 0 else None
                                _emit_progress(
                                    progress_callback,
                                    TransferProgress(
                                        direction="send",
                                        stage="entry_file",
                                        total_entries=len(manifest_entries),
                                        completed_entries=completed_entries,
                                        current_index=index,
                                        relative_path=entry.relative_path,
                                        kind="file",
                                        entry_bytes_done=sent,
                                        entry_bytes_total=entry.filesize,
                                        session_bytes_done=total_bytes_sent,
                                        session_bytes_total=session_bytes_total,
                                        speed_bytes_per_sec=speed,
                                        eta_seconds=eta,
                                        message="文件传输中",
                                    ),
                                )
                                last_emit = now
                    _emit_progress(
                        progress_callback,
                        TransferProgress(
                            direction="send",
                            stage="entry_file_done",
                            total_entries=len(manifest_entries),
                            completed_entries=completed_entries,
                            current_index=index,
                            relative_path=entry.relative_path,
                            kind="file",
                            entry_bytes_done=entry.filesize,
                            entry_bytes_total=entry.filesize,
                            session_bytes_done=total_bytes_sent,
                            session_bytes_total=session_bytes_total,
                            message="文件已发送",
                        ),
                    )

                entry_result = _recv_entry_result_from_socket(sock)
                if entry.kind == "file" and entry_result.bytes_sent == 0:
                    entry_result = EntryTransferResult(
                        relative_path=entry_result.relative_path,
                        kind=entry_result.kind,
                        status=entry_result.status,
                        detail=entry_result.detail,
                        saved_path=entry_result.saved_path,
                        bytes_sent=entry.filesize,
                    )
                results.append(entry_result)
                completed_entries += 1
                _emit_progress(
                    progress_callback,
                    TransferProgress(
                        direction="send",
                        stage="entry_result",
                        total_entries=len(manifest_entries),
                        completed_entries=completed_entries,
                        current_index=index,
                        relative_path=entry_result.relative_path,
                        kind=entry_result.kind,
                        session_bytes_done=total_bytes_sent,
                        session_bytes_total=session_bytes_total,
                        message=f"条目结果：{entry_result.status}",
                        detail=entry_result.detail,
                    ),
                )

                if entry_result.status == "error" and not config.continue_on_error:
                    aborted = True
                    break

            send_frame_header(
                sock,
                {
                    "type": "session_end",
                    "payload_size": 0,
                    "aborted": aborted,
                },
            )

            final_header = recv_frame_header(sock)
            if final_header.get("type") != "session_result":
                raise ProtocolError("receiver did not return session_result")
            _emit_progress(
                progress_callback,
                TransferProgress(
                    direction="send",
                    stage="session_end",
                    total_entries=len(manifest_entries),
                    completed_entries=completed_entries,
                    session_bytes_done=total_bytes_sent,
                    session_bytes_total=session_bytes_total,
                    message="会话已结束",
                ),
            )
    except OSError as exc:
        raise NetworkError(f"failed to send session: {exc}") from exc

    elapsed = time.perf_counter() - start

    successful_entries = sum(1 for result in results if result.status in {"success", "renamed"})
    skipped_entries = sum(1 for result in results if result.status == "skipped")
    failed_entries = sum(1 for result in results if result.status == "error")
    renamed_entries = sum(1 for result in results if result.status == "renamed")

    return SendSessionResult(
        remote_host=config.host,
        remote_port=config.port,
        total_entries=len(results),
        successful_entries=successful_entries,
        failed_entries=failed_entries,
        skipped_entries=skipped_entries,
        renamed_entries=renamed_entries,
        total_bytes_sent=total_bytes_sent,
        elapsed_seconds=elapsed,
        entry_results=tuple(results),
    )


def _validate_config(config: SenderConfig) -> None:
    if not config.host:
        raise ConfigurationError("target host is required")
    if config.port < 1 or config.port > 65535:
        raise ConfigurationError("port must be in range 1-65535")
    if config.timeout <= 0:
        raise ConfigurationError("timeout must be greater than 0")
    if config.chunk_size <= 0:
        raise ConfigurationError("chunk size must be greater than 0")
    if not config.file_path.exists():
        raise ConfigurationError(f"file does not exist: {config.file_path}")
    if not config.file_path.is_file():
        raise ConfigurationError(f"path is not a regular file: {config.file_path}")


def send_file(config: SenderConfig) -> SendResult:
    _validate_config(config)

    session_result = send_session(
        SessionSenderConfig(
            host=config.host,
            port=config.port,
            sources=[config.file_path],
            timeout=config.timeout,
            chunk_size=config.chunk_size,
            conflict_policy="overwrite",
            continue_on_error=False,
        )
    )

    file_size = config.file_path.stat().st_size
    if session_result.failed_entries > 0:
        first_failure = next(
            (
                result
                for result in session_result.entry_results
                if result.status == "error"
            ),
            None,
        )
        detail = first_failure.detail if first_failure else "unknown receiver error"
        raise NetworkError(f"failed to send file: {detail}")

    return SendResult(
        filename=config.file_path.name,
        filesize=file_size,
        sent_bytes=session_result.total_bytes_sent,
        remote_host=config.host,
        remote_port=config.port,
    )
