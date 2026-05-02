"""File receiver implementation."""

from __future__ import annotations

import os
import socket
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from .errors import ConfigurationError, NetworkError, ProtocolError
from .protocol import (
    PROTOCOL_VERSION,
    payload_size_from_header,
    recv_frame_header,
    recv_payload_discard,
    recv_payload_to_file,
    resolve_relative_output_path,
    sanitize_relative_path,
    send_frame_header,
)

DEFAULT_CHUNK_SIZE = 64 * 1024
VALID_CONFLICT_POLICIES = {"overwrite", "skip", "rename"}


@dataclass(frozen=True)
class ReceiverConfig:
    host: str
    port: int
    output_dir: Path
    timeout: Optional[float] = None
    chunk_size: int = DEFAULT_CHUNK_SIZE
    conflict_policy: str = "overwrite"
    continue_on_error: bool = True


@dataclass(frozen=True)
class ReceiveResult:
    filename: str
    filesize: int
    received_bytes: int
    output_path: Path
    peer_host: str
    peer_port: int


@dataclass(frozen=True)
class EntryReceiveResult:
    relative_path: str
    kind: str
    status: str
    detail: str = ""
    saved_path: Optional[str] = None
    received_bytes: int = 0


@dataclass(frozen=True)
class ReceiveSessionResult:
    peer_host: str
    peer_port: int
    total_entries: int
    successful_entries: int
    failed_entries: int
    skipped_entries: int
    renamed_entries: int
    total_bytes_received: int
    elapsed_seconds: float
    entry_results: Tuple[EntryReceiveResult, ...]


def _validate_config(config: ReceiverConfig) -> None:
    if not config.host:
        raise ConfigurationError("listen host is required")
    if config.port < 1 or config.port > 65535:
        raise ConfigurationError("port must be in range 1-65535")
    if config.timeout is not None and config.timeout <= 0:
        raise ConfigurationError("timeout must be greater than 0")
    if config.chunk_size <= 0:
        raise ConfigurationError("chunk size must be greater than 0")
    if config.conflict_policy not in VALID_CONFLICT_POLICIES:
        raise ConfigurationError(
            f"conflict policy must be one of: {', '.join(sorted(VALID_CONFLICT_POLICIES))}"
        )


def _to_saved_relative(output_dir: Path, target_path: Path) -> str:
    rel = target_path.resolve().relative_to(output_dir.resolve())
    return sanitize_relative_path(rel.as_posix())


def _resolve_renamed_file_path(target_path: Path) -> Path:
    base_name = target_path.stem
    suffix = target_path.suffix
    parent = target_path.parent

    for index in range(1, 100000):
        candidate = parent / f"{base_name} ({index}){suffix}"
        if not candidate.exists():
            return candidate
    raise ProtocolError("unable to allocate renamed file path")


def _resolve_renamed_dir_path(target_path: Path) -> Path:
    base_name = target_path.name
    parent = target_path.parent

    for index in range(1, 100000):
        candidate = parent / f"{base_name} ({index})"
        if not candidate.exists():
            return candidate
    raise ProtocolError("unable to allocate renamed directory path")


def _process_dir_entry(config: ReceiverConfig, relative_path: str) -> EntryReceiveResult:
    target = resolve_relative_output_path(config.output_dir, relative_path)

    if target.exists():
        if target.is_dir():
            return EntryReceiveResult(relative_path=relative_path, kind="dir", status="success")

        if config.conflict_policy == "skip":
            return EntryReceiveResult(
                relative_path=relative_path,
                kind="dir",
                status="skipped",
                detail="target exists as file",
            )

        if config.conflict_policy == "rename":
            renamed_target = _resolve_renamed_dir_path(target)
            renamed_target.mkdir(parents=True, exist_ok=False)
            return EntryReceiveResult(
                relative_path=relative_path,
                kind="dir",
                status="renamed",
                saved_path=_to_saved_relative(config.output_dir, renamed_target),
            )

        return EntryReceiveResult(
            relative_path=relative_path,
            kind="dir",
            status="error",
            detail="cannot overwrite existing file with directory",
        )

    target.mkdir(parents=True, exist_ok=False)
    return EntryReceiveResult(relative_path=relative_path, kind="dir", status="success")


def _apply_file_conflict_policy(
    config: ReceiverConfig,
    target: Path,
) -> Tuple[str, Optional[Path], Optional[str], str]:
    if not target.exists():
        return "success", target, None, ""

    if config.conflict_policy == "skip":
        return "skipped", None, None, "target exists"

    if config.conflict_policy == "rename":
        renamed = _resolve_renamed_file_path(target)
        return "renamed", renamed, _to_saved_relative(config.output_dir, renamed), ""

    if target.is_dir():
        return "error", None, None, "cannot overwrite existing directory with file"

    return "success", target, None, ""


def _process_file_entry(
    conn: socket.socket,
    config: ReceiverConfig,
    relative_path: str,
    payload_size: int,
    mtime: Optional[int],
) -> EntryReceiveResult:
    target = resolve_relative_output_path(config.output_dir, relative_path)
    status, write_target, saved_path, detail = _apply_file_conflict_policy(config, target)

    if status == "error":
        recv_payload_discard(conn, payload_size, config.chunk_size)
        return EntryReceiveResult(
            relative_path=relative_path,
            kind="file",
            status="error",
            detail=detail,
            received_bytes=payload_size,
        )

    if status == "skipped":
        recv_payload_discard(conn, payload_size, config.chunk_size)
        return EntryReceiveResult(
            relative_path=relative_path,
            kind="file",
            status="skipped",
            detail=detail,
            received_bytes=payload_size,
        )

    assert write_target is not None
    write_target.parent.mkdir(parents=True, exist_ok=True)

    with write_target.open("wb") as fp:
        received = recv_payload_to_file(conn, payload_size, fp, config.chunk_size)

    if mtime is not None:
        os.utime(write_target, (mtime, mtime))

    return EntryReceiveResult(
        relative_path=relative_path,
        kind="file",
        status=status,
        saved_path=saved_path,
        received_bytes=received,
    )


def _send_entry_result(conn: socket.socket, result: EntryReceiveResult) -> None:
    send_frame_header(
        conn,
        {
            "type": "entry_result",
            "payload_size": 0,
            "relative_path": result.relative_path,
            "kind": result.kind,
            "status": result.status,
            "detail": result.detail,
            "saved_path": result.saved_path,
        },
    )


def receive_session(config: ReceiverConfig) -> ReceiveSessionResult:
    _validate_config(config)
    config.output_dir.mkdir(parents=True, exist_ok=True)

    start = time.perf_counter()

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((config.host, config.port))
            server.listen(1)
            conn, addr = server.accept()
            with conn:
                if config.timeout is not None:
                    conn.settimeout(config.timeout)

                start_frame = recv_frame_header(conn)
                if start_frame.get("type") != "session_start":
                    raise ProtocolError("first frame must be session_start")
                if payload_size_from_header(start_frame) != 0:
                    raise ProtocolError("session_start payload_size must be zero")

                protocol_version = start_frame.get("protocol_version")
                if protocol_version not in {"1.1", PROTOCOL_VERSION, "1.2"}:
                    raise ProtocolError(f"unsupported protocol_version: {protocol_version}")

                results: List[EntryReceiveResult] = []
                total_bytes = 0

                while True:
                    header = recv_frame_header(conn)
                    frame_type = header.get("type")

                    if frame_type == "session_end":
                        if payload_size_from_header(header) != 0:
                            raise ProtocolError("session_end payload_size must be zero")
                        break

                    if frame_type == "entry_dir":
                        payload_size = payload_size_from_header(header)
                        if payload_size != 0:
                            raise ProtocolError("entry_dir payload_size must be zero")

                        relative_path = header.get("relative_path")
                        if not isinstance(relative_path, str):
                            raise ProtocolError("entry_dir.relative_path must be a string")
                        relative_path = sanitize_relative_path(relative_path)

                        result = _process_dir_entry(config, relative_path)
                        results.append(result)
                        _send_entry_result(conn, result)

                        if result.status == "error" and not config.continue_on_error:
                            break
                        continue

                    if frame_type == "entry_file":
                        payload_size = payload_size_from_header(header)
                        relative_path = header.get("relative_path")
                        if not isinstance(relative_path, str):
                            raise ProtocolError("entry_file.relative_path must be a string")
                        relative_path = sanitize_relative_path(relative_path)

                        raw_mtime = header.get("mtime")
                        mtime: Optional[int]
                        if raw_mtime is None:
                            mtime = None
                        elif isinstance(raw_mtime, int) and raw_mtime >= 0:
                            mtime = raw_mtime
                        else:
                            recv_payload_discard(conn, payload_size, config.chunk_size)
                            result = EntryReceiveResult(
                                relative_path=relative_path,
                                kind="file",
                                status="error",
                                detail="entry_file.mtime must be a non-negative integer",
                                received_bytes=payload_size,
                            )
                            results.append(result)
                            _send_entry_result(conn, result)
                            if not config.continue_on_error:
                                break
                            continue

                        result = _process_file_entry(conn, config, relative_path, payload_size, mtime)
                        results.append(result)
                        total_bytes += result.received_bytes
                        _send_entry_result(conn, result)

                        if result.status == "error" and not config.continue_on_error:
                            break
                        continue

                    raise ProtocolError(f"unsupported frame type: {frame_type}")

                send_frame_header(
                    conn,
                    {
                        "type": "session_result",
                        "payload_size": 0,
                        "total_entries": len(results),
                        "failed_entries": sum(1 for result in results if result.status == "error"),
                    },
                )

                elapsed = time.perf_counter() - start
                successful_entries = sum(
                    1 for result in results if result.status in {"success", "renamed"}
                )
                skipped_entries = sum(1 for result in results if result.status == "skipped")
                failed_entries = sum(1 for result in results if result.status == "error")
                renamed_entries = sum(1 for result in results if result.status == "renamed")

                return ReceiveSessionResult(
                    peer_host=addr[0],
                    peer_port=addr[1],
                    total_entries=len(results),
                    successful_entries=successful_entries,
                    failed_entries=failed_entries,
                    skipped_entries=skipped_entries,
                    renamed_entries=renamed_entries,
                    total_bytes_received=total_bytes,
                    elapsed_seconds=elapsed,
                    entry_results=tuple(results),
                )
    except OSError as exc:
        raise NetworkError(f"failed to receive file: {exc}") from exc


def receive_once(config: ReceiverConfig) -> ReceiveResult:
    session_result = receive_session(config)

    first_file = next(
        (
            entry
            for entry in session_result.entry_results
            if entry.kind == "file" and entry.status in {"success", "renamed"}
        ),
        None,
    )
    if first_file is None:
        raise NetworkError("failed to receive file: session did not contain a successful file entry")

    relative_path = first_file.saved_path or first_file.relative_path
    output_path = resolve_relative_output_path(config.output_dir, relative_path)
    if not output_path.exists():
        raise NetworkError(f"failed to receive file: expected output file does not exist: {output_path}")

    if session_result.failed_entries > 0:
        first_error = next(
            (entry.detail for entry in session_result.entry_results if entry.status == "error"),
            "receiver reported errors",
        )
        raise NetworkError(f"failed to receive file: {first_error}")

    return ReceiveResult(
        filename=Path(relative_path).name,
        filesize=output_path.stat().st_size,
        received_bytes=first_file.received_bytes,
        output_path=output_path,
        peer_host=session_result.peer_host,
        peer_port=session_result.peer_port,
    )
