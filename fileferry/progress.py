"""Transfer progress data structures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TransferProgress:
    """Snapshot of a transfer session or entry progress."""

    direction: str
    stage: str
    total_entries: int = 0
    completed_entries: int = 0
    current_index: int = 0
    relative_path: str = ""
    kind: str = ""
    entry_bytes_done: int = 0
    entry_bytes_total: int = 0
    session_bytes_done: int = 0
    session_bytes_total: int = 0
    speed_bytes_per_sec: float = 0.0
    eta_seconds: Optional[float] = None
    message: str = ""
    detail: str = ""

