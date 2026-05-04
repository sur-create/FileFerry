"""Pure UI state helpers for FileFerry desktop widgets."""

from __future__ import annotations

from typing import Optional, Tuple

from fileferry.progress import TransferProgress


def format_bytes(value: float) -> str:
    if value < 0:
        value = 0
    units = ["B", "KB", "MB", "GB", "TB"]
    amount = float(value)
    for unit in units:
        if amount < 1024.0 or unit == units[-1]:
            if unit == "B":
                return f"{int(amount)} {unit}"
            return f"{amount:.1f} {unit}"
        amount /= 1024.0
    return f"{amount:.1f} TB"


def format_speed(bytes_per_second: float) -> str:
    if bytes_per_second <= 0:
        return "0 B/s"
    return f"{format_bytes(bytes_per_second)}/s"


def format_eta(seconds: Optional[float]) -> str:
    if seconds is None or seconds < 0:
        return "未知"
    total_seconds = int(round(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def progress_percent(done: int, total: int) -> int:
    if total <= 0:
        return 0
    return max(0, min(100, int(done * 100 / total)))


def send_button_state(
    connected: bool,
    has_sources: bool,
    busy: bool,
) -> Tuple[str, bool, str]:
    if busy:
        return "发送中...", False, "当前已有发送任务在运行"
    if not connected:
        return "先开启连接", False, "请先建立发送端连接"
    if not has_sources:
        return "请先添加文件", False, "请先添加要发送的文件或文件夹"
    return "开始发送", True, "点击开始传输"


def progress_overview(progress: TransferProgress) -> str:
    total_entries = progress.total_entries or 0
    completed_entries = progress.completed_entries or 0
    entry_label = f"{completed_entries}/{total_entries}" if total_entries else f"{completed_entries}"
    session_bytes = format_bytes(progress.session_bytes_done)
    session_total = format_bytes(progress.session_bytes_total) if progress.session_bytes_total else "未知"
    parts = [f"会话进度 {entry_label}", f"已传 {session_bytes} / {session_total}"]
    if progress.speed_bytes_per_sec > 0:
        parts.append(f"速度 {format_speed(progress.speed_bytes_per_sec)}")
    if progress.eta_seconds is not None:
        parts.append(f"剩余 {format_eta(progress.eta_seconds)}")
    if progress.message:
        parts.append(progress.message)
    return " | ".join(parts)

