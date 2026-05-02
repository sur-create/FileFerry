"""Protocol primitives for TCP transport."""

from __future__ import annotations

import json
import os
import struct
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from socket import socket
from typing import Any, BinaryIO, Mapping

from .errors import ProtocolError

HEADER_PREFIX_BYTES = 4
MAX_HEADER_BYTES = 64 * 1024
PROTOCOL_VERSION = "1.2"


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


def sanitize_relative_path(relative_path: str) -> str:
    if not isinstance(relative_path, str):
        raise ProtocolError("relative_path must be a string")
    if not relative_path:
        raise ProtocolError("relative_path cannot be empty")
    if "\\" in relative_path:
        raise ProtocolError("relative_path cannot contain backslashes")

    pure = PurePosixPath(relative_path)
    if pure.is_absolute():
        raise ProtocolError("relative_path cannot be absolute")
    if not pure.parts:
        raise ProtocolError("relative_path cannot be empty")

    cleaned_parts = []
    for part in pure.parts:
        if part in {"", ".", ".."}:
            raise ProtocolError("relative_path cannot contain . or ..")
        cleaned_parts.append(part)
    return "/".join(cleaned_parts)


def resolve_relative_output_path(output_dir: Path, relative_path: str) -> Path:
    normalized = sanitize_relative_path(relative_path)
    target = output_dir / Path(*normalized.split("/"))

    root_resolved = output_dir.resolve()
    target_resolved = target.resolve(strict=False)

    try:
        common = os.path.commonpath([str(root_resolved), str(target_resolved)])
    except ValueError as exc:
        raise ProtocolError("relative_path escapes output directory") from exc

    if common != str(root_resolved):
        raise ProtocolError("relative_path escapes output directory")
    return target


def _encode_json_header(header_obj: Mapping[str, Any]) -> bytes:
    try:
        header = json.dumps(header_obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ProtocolError("header is not JSON-serializable") from exc

    if len(header) > MAX_HEADER_BYTES:
        raise ProtocolError(f"header too large: {len(header)} bytes")
    return header


def encode_header(metadata: FileMetadata) -> bytes:
    sanitize_filename(metadata.filename)
    if metadata.filesize < 0:
        raise ProtocolError("filesize cannot be negative")

    header = _encode_json_header({"filename": metadata.filename, "filesize": metadata.filesize})
    return struct.pack("!I", len(header)) + header


def decode_header(header: bytes) -> FileMetadata:
    payload = _decode_json_header(header)

    if "filename" not in payload or "filesize" not in payload:
        raise ProtocolError("header must contain filename and filesize")
    if not isinstance(payload["filename"], str):
        raise ProtocolError("filename must be a string")
    if not isinstance(payload["filesize"], int):
        raise ProtocolError("filesize must be an integer")
    if payload["filesize"] < 0:
        raise ProtocolError("filesize cannot be negative")

    return FileMetadata(filename=sanitize_filename(payload["filename"]), filesize=payload["filesize"])


def _decode_json_header(header: bytes) -> dict[str, Any]:
    try:
        payload: Any = json.loads(header.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("invalid JSON header") from exc

    if not isinstance(payload, dict):
        raise ProtocolError("header must be a JSON object")
    return payload


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


def send_frame_header(sock: socket, header_obj: Mapping[str, Any]) -> None:
    header = _encode_json_header(header_obj)
    sock.sendall(struct.pack("!I", len(header)))
    sock.sendall(header)


def recv_frame_header(sock: socket) -> dict[str, Any]:
    prefix = recv_exact(sock, HEADER_PREFIX_BYTES)
    (header_size,) = struct.unpack("!I", prefix)
    if header_size == 0:
        raise ProtocolError("header length cannot be zero")
    if header_size > MAX_HEADER_BYTES:
        raise ProtocolError(f"header too large: {header_size} bytes")
    return _decode_json_header(recv_exact(sock, header_size))


def payload_size_from_header(header_obj: Mapping[str, Any]) -> int:
    payload_size = header_obj.get("payload_size", 0)
    if not isinstance(payload_size, int):
        raise ProtocolError("payload_size must be an integer")
    if payload_size < 0:
        raise ProtocolError("payload_size cannot be negative")
    return payload_size


def recv_payload_to_file(sock: socket, size: int, fp: BinaryIO, chunk_size: int) -> int:
    if chunk_size <= 0:
        raise ProtocolError("chunk_size must be greater than 0")

    remaining = size
    received = 0
    while remaining > 0:
        packet = sock.recv(min(chunk_size, remaining))
        if not packet:
            raise ProtocolError("connection closed before receiving all file bytes")
        fp.write(packet)
        received += len(packet)
        remaining -= len(packet)
    return received


def recv_payload_discard(sock: socket, size: int, chunk_size: int) -> int:
    if chunk_size <= 0:
        raise ProtocolError("chunk_size must be greater than 0")

    remaining = size
    received = 0
    while remaining > 0:
        packet = sock.recv(min(chunk_size, remaining))
        if not packet:
            raise ProtocolError("connection closed before receiving all file bytes")
        received += len(packet)
        remaining -= len(packet)
    return received


def send_file_payload(sock: socket, fp: BinaryIO, chunk_size: int) -> int:
    if chunk_size <= 0:
        raise ProtocolError("chunk_size must be greater than 0")

    sent = 0
    while True:
        chunk = fp.read(chunk_size)
        if not chunk:
            break
        sock.sendall(chunk)
        sent += len(chunk)
    return sent


def resolve_output_path(output_dir: Path, filename: str) -> Path:
    return output_dir / sanitize_filename(filename)
