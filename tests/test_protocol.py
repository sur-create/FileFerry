from __future__ import annotations

import socket
import struct
import tempfile
import unittest
from pathlib import Path

from fileferry.errors import ProtocolError
from fileferry.protocol import (
    FileMetadata,
    decode_header,
    encode_header,
    recv_exact,
    resolve_relative_output_path,
    sanitize_filename,
    sanitize_relative_path,
)


class ProtocolTests(unittest.TestCase):
    def test_encode_decode_round_trip(self) -> None:
        original = FileMetadata(filename="demo.txt", filesize=1024)
        payload = encode_header(original)

        prefix = payload[:4]
        body = payload[4:]
        (length,) = struct.unpack("!I", prefix)
        self.assertEqual(length, len(body))

        parsed = decode_header(body)
        self.assertEqual(parsed, original)

    def test_invalid_filename_rejected(self) -> None:
        with self.assertRaises(ProtocolError):
            sanitize_filename("../a.txt")
        with self.assertRaises(ProtocolError):
            sanitize_filename("folder\\a.txt")
        with self.assertRaises(ProtocolError):
            sanitize_relative_path("../a.txt")
        with self.assertRaises(ProtocolError):
            sanitize_relative_path("/a.txt")

    def test_recv_exact_raises_on_disconnect(self) -> None:
        left, right = socket.socketpair()
        self.addCleanup(left.close)
        self.addCleanup(right.close)

        left.sendall(b"abc")
        left.close()
        with self.assertRaises(ProtocolError):
            recv_exact(right, 4)

    def test_resolve_relative_output_path_rejects_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            self.assertEqual(
                resolve_relative_output_path(root, "a/b.txt"),
                root / "a" / "b.txt",
            )
            with self.assertRaises(ProtocolError):
                resolve_relative_output_path(root, "../b.txt")


if __name__ == "__main__":
    unittest.main()
