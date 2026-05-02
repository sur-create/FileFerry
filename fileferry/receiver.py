"""File receiver implementation."""

from __future__ import annotations

import socket
from dataclasses import dataclass
from pathlib import Path

from .errors import ConfigurationError, NetworkError, ProtocolError
from .protocol import recv_metadata, resolve_output_path

DEFAULT_CHUNK_SIZE = 64 * 1024


@dataclass(frozen=True)
class ReceiverConfig:
    host: str
    port: int
    output_dir: Path
    timeout: float | None = None
    chunk_size: int = DEFAULT_CHUNK_SIZE


@dataclass(frozen=True)
class ReceiveResult:
    filename: str
    filesize: int
    received_bytes: int
    output_path: Path
    peer_host: str
    peer_port: int


def _validate_config(config: ReceiverConfig) -> None:
    if not config.host:
        raise ConfigurationError("listen host is required")
    if config.port < 1 or config.port > 65535:
        raise ConfigurationError("port must be in range 1-65535")
    if config.timeout is not None and config.timeout <= 0:
        raise ConfigurationError("timeout must be greater than 0")
    if config.chunk_size <= 0:
        raise ConfigurationError("chunk size must be greater than 0")


def receive_once(config: ReceiverConfig) -> ReceiveResult:
    _validate_config(config)
    config.output_dir.mkdir(parents=True, exist_ok=True)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((config.host, config.port))
            server.listen(1)
            conn, addr = server.accept()
            with conn:
                if config.timeout is not None:
                    conn.settimeout(config.timeout)
                metadata = recv_metadata(conn)
                output_path = resolve_output_path(config.output_dir, metadata.filename)
                remaining = metadata.filesize
                received = 0
                with output_path.open("wb") as fp:
                    while remaining > 0:
                        packet = conn.recv(min(config.chunk_size, remaining))
                        if not packet:
                            raise ProtocolError("connection closed before receiving all file bytes")
                        fp.write(packet)
                        received += len(packet)
                        remaining -= len(packet)

                return ReceiveResult(
                    filename=metadata.filename,
                    filesize=metadata.filesize,
                    received_bytes=received,
                    output_path=output_path,
                    peer_host=addr[0],
                    peer_port=addr[1],
                )
    except OSError as exc:
        raise NetworkError(f"failed to receive file: {exc}") from exc
