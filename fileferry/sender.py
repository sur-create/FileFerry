"""File sender implementation."""

from __future__ import annotations

import socket
from dataclasses import dataclass
from pathlib import Path

from .errors import ConfigurationError, NetworkError
from .protocol import FileMetadata, encode_header

DEFAULT_CHUNK_SIZE = 64 * 1024


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

    file_size = config.file_path.stat().st_size
    metadata = FileMetadata(filename=config.file_path.name, filesize=file_size)
    payload_header = encode_header(metadata)

    sent_total = 0
    try:
        with socket.create_connection((config.host, config.port), timeout=config.timeout) as sock:
            sock.sendall(payload_header)
            with config.file_path.open("rb") as fp:
                while True:
                    chunk = fp.read(config.chunk_size)
                    if not chunk:
                        break
                    sock.sendall(chunk)
                    sent_total += len(chunk)
    except OSError as exc:
        raise NetworkError(f"failed to send file: {exc}") from exc

    return SendResult(
        filename=metadata.filename,
        filesize=metadata.filesize,
        sent_bytes=sent_total,
        remote_host=config.host,
        remote_port=config.port,
    )
