"""Protocol primitives for TCP transport."""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from pathlib import Path
from socket import socket
from typing import Any

from .errors import ProtocolError

HEADER_PREFIX_BYTES = 4
MAX_HEADER_BYTES = 64 * 1024


@dataclass(frozen=True)
class FileMetadata:
    filename: str
    filesize: int


def sanitize_filename(filename: str) -> str:
    if not filename:
        raise ProtocolError("filename cannot be empty")
    if filename in {".", ".."}:
        raise ProtocolError("invalid filename")
    if "/" in filename or "\\" in filename:
        raise ProtocolError("filename cannot contain path separators")
    return filename


def encode_header(metadata: FileMetadata) -> bytes:
    sanitize_filename(metadata.filename)
    if metadata.filesize < 0:
        raise ProtocolError("filesize cannot be negative")

    header_obj = {"filename": metadata.filename, "filesize": metadata.filesize}
    header = json.dumps(header_obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(header) > MAX_HEADER_BYTES:
        raise ProtocolError(f"header too large: {len(header)} bytes")
    return struct.pack("!I", len(header)) + header


def decode_header(header: bytes) -> FileMetadata:
    try:
        payload: Any = json.loads(header.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("invalid JSON header") from exc

    if not isinstance(payload, dict):
        raise ProtocolError("header must be a JSON object")
    if "filename" not in payload or "filesize" not in payload:
        raise ProtocolError("header must contain filename and filesize")
    if not isinstance(payload["filename"], str):
        raise ProtocolError("filename must be a string")
    if not isinstance(payload["filesize"], int):
        raise ProtocolError("filesize must be an integer")
    if payload["filesize"] < 0:
        raise ProtocolError("filesize cannot be negative")

    return FileMetadata(filename=sanitize_filename(payload["filename"]), filesize=payload["filesize"])


def recv_exact(sock: socket, size: int) -> bytes:
    if size < 0:
        raise ProtocolError("invalid read size")

    chunks = bytearray()
    while len(chunks) < size:
        packet = sock.recv(size - len(chunks))
        if not packet:
            raise ProtocolError("connection closed unexpectedly")
        chunks.extend(packet)
    return bytes(chunks)


def recv_metadata(sock: socket) -> FileMetadata:
    prefix = recv_exact(sock, HEADER_PREFIX_BYTES)
    (header_size,) = struct.unpack("!I", prefix)
    if header_size == 0:
        raise ProtocolError("header length cannot be zero")
    if header_size > MAX_HEADER_BYTES:
        raise ProtocolError(f"header too large: {header_size} bytes")
    raw_header = recv_exact(sock, header_size)
    return decode_header(raw_header)


def resolve_output_path(output_dir: Path, filename: str) -> Path:
    return output_dir / sanitize_filename(filename)
