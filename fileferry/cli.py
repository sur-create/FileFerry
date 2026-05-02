"""Command-line entrypoints."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List

from .errors import FileFerryError
from .receiver import ReceiverConfig, receive_session
from .sender import SessionSenderConfig, send_session


def default_output_dir() -> Path:
    argv0 = Path(sys.argv[0])
    candidate = argv0.resolve().parent if argv0.exists() else Path.cwd()
    if candidate.exists() and candidate.is_dir() and os.access(candidate, os.W_OK):
        return candidate
    return Path.cwd()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LAN file transfer tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    send_parser = subparsers.add_parser("send", help="send files/directories to receiver")
    send_parser.add_argument("--host", required=True, help="receiver IP address")
    send_parser.add_argument("--port", required=True, type=int, help="receiver port")

    source_group = send_parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--file", help="single file path (legacy compatibility)")
    source_group.add_argument(
        "--src",
        action="append",
        help="source path to send; repeat for multiple files/directories",
    )

    send_parser.add_argument(
        "--conflict",
        choices=["overwrite", "skip", "rename"],
        default="overwrite",
        help="how receiver handles target conflicts",
    )
    send_parser.add_argument(
        "--continue-on-error",
        dest="continue_on_error",
        action="store_true",
        default=True,
        help="continue sending subsequent entries when one entry fails (default)",
    )
    send_parser.add_argument(
        "--fail-fast",
        dest="continue_on_error",
        action="store_false",
        help="stop after first entry failure",
    )
    send_parser.add_argument("--timeout", type=float, default=10.0, help="socket timeout seconds")
    send_parser.add_argument("--chunk-size", type=int, default=64 * 1024, help="chunk size in bytes")

    recv_parser = subparsers.add_parser("recv", help="listen and receive one session")
    recv_parser.add_argument("--host", default="0.0.0.0", help="listen IP address")
    recv_parser.add_argument("--port", required=True, type=int, help="listen port")
    recv_parser.add_argument("--output-dir", help="directory to save file")
    recv_parser.add_argument(
        "--conflict",
        choices=["overwrite", "skip", "rename"],
        default="overwrite",
        help="how to handle existing target paths",
    )
    recv_parser.add_argument(
        "--continue-on-error",
        dest="continue_on_error",
        action="store_true",
        default=True,
        help="continue receiving subsequent entries when one entry fails (default)",
    )
    recv_parser.add_argument(
        "--fail-fast",
        dest="continue_on_error",
        action="store_false",
        help="stop after first entry failure",
    )
    recv_parser.add_argument("--timeout", type=float, help="connection timeout seconds")
    recv_parser.add_argument("--chunk-size", type=int, default=64 * 1024, help="chunk size in bytes")
    return parser


def _collect_sources(args: argparse.Namespace) -> List[Path]:
    if args.file:
        return [Path(args.file).expanduser()]
    assert args.src is not None
    return [Path(item).expanduser() for item in args.src]


def run_send(args: argparse.Namespace) -> int:
    config = SessionSenderConfig(
        host=args.host,
        port=args.port,
        sources=_collect_sources(args),
        timeout=args.timeout,
        chunk_size=args.chunk_size,
        conflict_policy=args.conflict,
        continue_on_error=args.continue_on_error,
    )
    result = send_session(config)

    print(f"session sent to {result.remote_host}:{result.remote_port}")
    print(
        "summary: "
        f"total={result.total_entries}, success={result.successful_entries}, "
        f"skipped={result.skipped_entries}, renamed={result.renamed_entries}, "
        f"failed={result.failed_entries}, bytes={result.total_bytes_sent}, "
        f"elapsed={result.elapsed_seconds:.3f}s"
    )

    for entry in result.entry_results:
        if entry.status == "error":
            print(
                f"entry error: {entry.relative_path} ({entry.kind}) - {entry.detail}",
                file=sys.stderr,
            )

    if result.failed_entries > 0:
        return 1
    return 0


def run_receive(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else default_output_dir()
    config = ReceiverConfig(
        host=args.host,
        port=args.port,
        output_dir=output_dir,
        timeout=args.timeout,
        chunk_size=args.chunk_size,
        conflict_policy=args.conflict,
        continue_on_error=args.continue_on_error,
    )
    print(f"listening on {config.host}:{config.port}, output dir: {config.output_dir}")
    result = receive_session(config)

    print(
        "summary: "
        f"total={result.total_entries}, success={result.successful_entries}, "
        f"skipped={result.skipped_entries}, renamed={result.renamed_entries}, "
        f"failed={result.failed_entries}, bytes={result.total_bytes_received}, "
        f"elapsed={result.elapsed_seconds:.3f}s"
    )

    for entry in result.entry_results:
        if entry.status == "error":
            print(
                f"entry error: {entry.relative_path} ({entry.kind}) - {entry.detail}",
                file=sys.stderr,
            )

    if result.failed_entries > 0:
        return 1
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
