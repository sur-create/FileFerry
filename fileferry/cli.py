"""Command-line entrypoints."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .errors import FileFerryError
from .receiver import ReceiverConfig, receive_once
from .sender import SenderConfig, send_file


def default_output_dir() -> Path:
    argv0 = Path(sys.argv[0])
    candidate = argv0.resolve().parent if argv0.exists() else Path.cwd()
    if candidate.exists() and candidate.is_dir() and os.access(candidate, os.W_OK):
        return candidate
    return Path.cwd()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LAN single-file transfer tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    send_parser = subparsers.add_parser("send", help="send a file to receiver")
    send_parser.add_argument("--host", required=True, help="receiver IP address")
    send_parser.add_argument("--port", required=True, type=int, help="receiver port")
    send_parser.add_argument("--file", required=True, help="local file path to send")
    send_parser.add_argument("--timeout", type=float, default=10.0, help="socket timeout seconds")
    send_parser.add_argument("--chunk-size", type=int, default=64 * 1024, help="chunk size in bytes")

    recv_parser = subparsers.add_parser("recv", help="listen and receive one file")
    recv_parser.add_argument("--host", default="0.0.0.0", help="listen IP address")
    recv_parser.add_argument("--port", required=True, type=int, help="listen port")
    recv_parser.add_argument("--output-dir", help="directory to save file")
    recv_parser.add_argument("--timeout", type=float, help="connection timeout seconds")
    recv_parser.add_argument("--chunk-size", type=int, default=64 * 1024, help="chunk size in bytes")
    return parser


def run_send(args: argparse.Namespace) -> int:
    config = SenderConfig(
        host=args.host,
        port=args.port,
        file_path=Path(args.file).expanduser().resolve(),
        timeout=args.timeout,
        chunk_size=args.chunk_size,
    )
    result = send_file(config)
    print(
        f"sent '{result.filename}' ({result.sent_bytes} bytes) "
        f"to {result.remote_host}:{result.remote_port}"
    )
    return 0


def run_receive(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else default_output_dir()
    config = ReceiverConfig(
        host=args.host,
        port=args.port,
        output_dir=output_dir,
        timeout=args.timeout,
        chunk_size=args.chunk_size,
    )
    print(f"listening on {config.host}:{config.port}, output dir: {config.output_dir}")
    result = receive_once(config)
    print(f"received '{result.filename}' ({result.received_bytes} bytes) -> {result.output_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "send":
            return run_send(args)
        return run_receive(args)
    except FileFerryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
