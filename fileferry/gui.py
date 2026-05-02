"""Desktop GUI for FileFerry."""

from __future__ import annotations

import queue
import threading
import traceback
from pathlib import Path
from typing import Callable
from tkinter import END, filedialog, messagebox, ttk
import tkinter as tk

from .cli import default_output_dir
from .errors import ConfigurationError, FileFerryError
from .receiver import ReceiveSessionResult, ReceiverConfig, receive_session
from .sender import SendSessionResult, SessionSenderConfig, send_session


class FileFerryDesktopApp(tk.Tk):
    """Tkinter desktop application for file transfer."""

    def __init__(self) -> None:
        super().__init__()
        self.title("FileFerry")
        self.geometry("920x640")
        self.minsize(780, 520)

        self._events: queue.Queue[tuple[str, object, object]] = queue.Queue()
        self._task_thread: threading.Thread | None = None

        self._status_var = tk.StringVar(value="Ready")
        self._send_host_var = tk.StringVar(value="127.0.0.1")
        self._send_port_var = tk.StringVar(value="9000")
        self._send_timeout_var = tk.StringVar(value="10")
        self._send_conflict_var = tk.StringVar(value="overwrite")
        self._send_continue_var = tk.BooleanVar(value=True)

        self._recv_host_var = tk.StringVar(value="0.0.0.0")
        self._recv_port_var = tk.StringVar(value="9000")
        self._recv_output_var = tk.StringVar(value=str(default_output_dir()))
        self._recv_timeout_var = tk.StringVar(value="")
        self._recv_conflict_var = tk.StringVar(value="overwrite")
        self._recv_continue_var = tk.BooleanVar(value=True)

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(120, self._drain_events)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True)

        send_tab = ttk.Frame(notebook, padding=12)
        recv_tab = ttk.Frame(notebook, padding=12)
        notebook.add(send_tab, text="Send")
        notebook.add(recv_tab, text="Receive")

        self._build_send_tab(send_tab)
        self._build_recv_tab(recv_tab)

        log_frame = ttk.LabelFrame(root, text="Logs", padding=8)
        log_frame.pack(fill="both", expand=True, pady=(12, 0))

        self._log_text = tk.Text(log_frame, height=10, wrap="word", state="disabled")
        self._log_text.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self._log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self._log_text.configure(yscrollcommand=scrollbar.set)

        status_bar = ttk.Frame(root)
        status_bar.pack(fill="x", pady=(8, 0))
        ttk.Label(status_bar, textvariable=self._status_var).pack(side="left")
        ttk.Button(status_bar, text="Clear Logs", command=self._clear_logs).pack(side="right")

    def _build_send_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(1, weight=1)

        ttk.Label(parent, text="Receiver Host").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(parent, textvariable=self._send_host_var).grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(parent, text="Port").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(parent, textvariable=self._send_port_var).grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(parent, text="Timeout (seconds)").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(parent, textvariable=self._send_timeout_var).grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(parent, text="Conflict Policy").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(
            parent,
            values=("overwrite", "skip", "rename"),
            state="readonly",
            textvariable=self._send_conflict_var,
        ).grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Checkbutton(
            parent,
            text="Continue on error",
            variable=self._send_continue_var,
        ).grid(row=4, column=1, sticky="w", pady=4)

        ttk.Label(parent, text="Sources").grid(row=5, column=0, sticky="nw", padx=(0, 8), pady=(8, 4))

        source_frame = ttk.Frame(parent)
        source_frame.grid(row=5, column=1, sticky="nsew", pady=(8, 4))
        parent.rowconfigure(5, weight=1)
        source_frame.columnconfigure(0, weight=1)

        self._source_list = tk.Listbox(source_frame, selectmode="extended", height=8)
        self._source_list.grid(row=0, column=0, sticky="nsew")
        source_frame.rowconfigure(0, weight=1)

        source_scroll = ttk.Scrollbar(source_frame, orient="vertical", command=self._source_list.yview)
        source_scroll.grid(row=0, column=1, sticky="ns")
        self._source_list.configure(yscrollcommand=source_scroll.set)

        source_buttons = ttk.Frame(source_frame)
        source_buttons.grid(row=0, column=2, padx=(8, 0), sticky="ns")
        ttk.Button(source_buttons, text="Add File", command=self._pick_send_files).pack(fill="x", pady=2)
        ttk.Button(source_buttons, text="Add Folder", command=self._pick_send_directory).pack(fill="x", pady=2)
        ttk.Button(source_buttons, text="Remove", command=self._remove_selected_sources).pack(fill="x", pady=2)
        ttk.Button(source_buttons, text="Clear", command=self._clear_sources).pack(fill="x", pady=2)

        self._send_button = ttk.Button(parent, text="Start Send", command=self._start_send)
        self._send_button.grid(row=6, column=1, sticky="e", pady=(10, 0))

    def _build_recv_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(1, weight=1)

        ttk.Label(parent, text="Listen Host").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(parent, textvariable=self._recv_host_var).grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(parent, text="Port").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(parent, textvariable=self._recv_port_var).grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(parent, text="Output Directory").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        output_row = ttk.Frame(parent)
        output_row.grid(row=2, column=1, sticky="ew", pady=4)
        output_row.columnconfigure(0, weight=1)
        ttk.Entry(output_row, textvariable=self._recv_output_var).grid(row=0, column=0, sticky="ew")
        ttk.Button(output_row, text="Browse", command=self._pick_output_directory).grid(row=0, column=1, padx=(8, 0))

        ttk.Label(parent, text="Timeout (optional)").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(parent, textvariable=self._recv_timeout_var).grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Label(parent, text="Conflict Policy").grid(row=4, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(
            parent,
            values=("overwrite", "skip", "rename"),
            state="readonly",
            textvariable=self._recv_conflict_var,
        ).grid(row=4, column=1, sticky="ew", pady=4)

        ttk.Checkbutton(
            parent,
            text="Continue on error",
            variable=self._recv_continue_var,
        ).grid(row=5, column=1, sticky="w", pady=4)

        self._recv_button = ttk.Button(parent, text="Start Receive", command=self._start_receive)
        self._recv_button.grid(row=6, column=1, sticky="e", pady=(10, 0))

    def _pick_send_files(self) -> None:
        selected = filedialog.askopenfilenames(title="Choose files to send")
        if not selected:
            return
        self._append_sources(selected)

    def _pick_send_directory(self) -> None:
        selected = filedialog.askdirectory(title="Choose directory to send")
        if not selected:
            return
        self._append_sources([selected])

    def _pick_output_directory(self) -> None:
        selected = filedialog.askdirectory(title="Choose output directory")
        if selected:
            self._recv_output_var.set(str(Path(selected).expanduser()))

    def _append_sources(self, raw_paths: list[str] | tuple[str, ...]) -> None:
        existing = set(self._source_list.get(0, END))
        for raw in raw_paths:
            normalized = str(Path(raw).expanduser().resolve())
            if normalized not in existing:
                self._source_list.insert(END, normalized)
                existing.add(normalized)

    def _remove_selected_sources(self) -> None:
        indices = list(self._source_list.curselection())
        indices.reverse()
        for idx in indices:
            self._source_list.delete(idx)

    def _clear_sources(self) -> None:
        self._source_list.delete(0, END)

    def _clear_logs(self) -> None:
        self._log_text.configure(state="normal")
        self._log_text.delete("1.0", END)
        self._log_text.configure(state="disabled")

    def _start_send(self) -> None:
        if self._is_busy():
            messagebox.showwarning("FileFerry", "A transfer is already running.")
            return

        try:
            config = SessionSenderConfig(
                host=self._require_text(self._send_host_var.get(), "receiver host"),
                port=self._parse_port(self._send_port_var.get()),
                sources=self._collect_send_sources(),
                timeout=self._parse_timeout(self._send_timeout_var.get(), allow_empty=False),
                conflict_policy=self._send_conflict_var.get(),
                continue_on_error=bool(self._send_continue_var.get()),
            )
        except FileFerryError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        self._start_worker("Sending", lambda: self._run_send(config))

    def _start_receive(self) -> None:
        if self._is_busy():
            messagebox.showwarning("FileFerry", "A transfer is already running.")
            return

        try:
            output_dir = Path(self._require_text(self._recv_output_var.get(), "output directory")).expanduser().resolve()
            config = ReceiverConfig(
                host=self._require_text(self._recv_host_var.get(), "listen host"),
                port=self._parse_port(self._recv_port_var.get()),
                output_dir=output_dir,
                timeout=self._parse_timeout(self._recv_timeout_var.get(), allow_empty=True),
                conflict_policy=self._recv_conflict_var.get(),
                continue_on_error=bool(self._recv_continue_var.get()),
            )
        except FileFerryError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        self._start_worker("Receiving", lambda: self._run_receive(config))

    def _collect_send_sources(self) -> list[Path]:
        values = list(self._source_list.get(0, END))
        if not values:
            raise ConfigurationError("at least one source path is required")
        return [Path(value) for value in values]

    def _start_worker(self, action: str, job: Callable[[], None]) -> None:
        self._set_busy(True, f"{action}...")

        def worker() -> None:
            try:
                job()
            except FileFerryError as exc:
                self._events.put(("log", f"error: {exc}", None))
                self._events.put(("done", False, str(exc)))
            except Exception:
                stack = traceback.format_exc().strip()
                self._events.put(("log", "unexpected error:", None))
                self._events.put(("log", stack, None))
                self._events.put(("done", False, "unexpected error"))

        self._task_thread = threading.Thread(target=worker, daemon=True)
        self._task_thread.start()

    def _run_send(self, config: SessionSenderConfig) -> None:
        self._events.put(("log", f"send to {config.host}:{config.port}", None))
        result = send_session(config)
        self._events.put(("log", self._format_send_summary(result), None))
        for entry in result.entry_results:
            if entry.status == "error":
                self._events.put(("log", f"entry error: {entry.relative_path} ({entry.kind}) - {entry.detail}", None))

        if result.failed_entries > 0:
            self._events.put(("done", False, "send completed with failures"))
            return

        self._events.put(("done", True, "send completed"))

    def _run_receive(self, config: ReceiverConfig) -> None:
        self._events.put(("log", f"listening on {config.host}:{config.port}", None))
        self._events.put(("log", f"output dir: {config.output_dir}", None))
        result = receive_session(config)
        self._events.put(("log", self._format_receive_summary(result), None))
        for entry in result.entry_results:
            if entry.status == "error":
                self._events.put(("log", f"entry error: {entry.relative_path} ({entry.kind}) - {entry.detail}", None))

        if result.failed_entries > 0:
            self._events.put(("done", False, "receive completed with failures"))
            return

        self._events.put(("done", True, "receive completed"))

    def _drain_events(self) -> None:
        while True:
            try:
                event, payload, extra = self._events.get_nowait()
            except queue.Empty:
                break

            if event == "log":
                self._append_log(str(payload))
            elif event == "done":
                success = bool(payload)
                status = str(extra)
                self._set_busy(False, status)
                if not success:
                    messagebox.showerror("FileFerry", status)

        self.after(120, self._drain_events)

    def _append_log(self, text: str) -> None:
        self._log_text.configure(state="normal")
        self._log_text.insert(END, text + "\n")
        self._log_text.see(END)
        self._log_text.configure(state="disabled")

    def _set_busy(self, busy: bool, status_text: str) -> None:
        self._status_var.set(status_text)
        send_state = "disabled" if busy else "normal"
        recv_state = "disabled" if busy else "normal"
        self._send_button.configure(state=send_state)
        self._recv_button.configure(state=recv_state)

    def _is_busy(self) -> bool:
        return self._task_thread is not None and self._task_thread.is_alive()

    def _on_close(self) -> None:
        if self._is_busy():
            close_anyway = messagebox.askyesno(
                "FileFerry",
                "A transfer is still running. Close anyway?",
            )
            if not close_anyway:
                return
        self.destroy()

    @staticmethod
    def _require_text(value: str, field_name: str) -> str:
        text = value.strip()
        if not text:
            raise ConfigurationError(f"{field_name} is required")
        return text

    @staticmethod
    def _parse_port(value: str) -> int:
        try:
            port = int(value)
        except ValueError as exc:
            raise ConfigurationError("port must be an integer") from exc

        if port < 1 or port > 65535:
            raise ConfigurationError("port must be in range 1-65535")
        return port

    @staticmethod
    def _parse_timeout(value: str, *, allow_empty: bool) -> float | None:
        text = value.strip()
        if not text:
            if allow_empty:
                return None
            raise ConfigurationError("timeout is required")

        try:
            timeout = float(text)
        except ValueError as exc:
            raise ConfigurationError("timeout must be a number") from exc

        if timeout <= 0:
            raise ConfigurationError("timeout must be greater than 0")
        return timeout

    @staticmethod
    def _format_send_summary(result: SendSessionResult) -> str:
        return (
            "send summary: "
            f"total={result.total_entries}, success={result.successful_entries}, "
            f"skipped={result.skipped_entries}, renamed={result.renamed_entries}, "
            f"failed={result.failed_entries}, bytes={result.total_bytes_sent}, "
            f"elapsed={result.elapsed_seconds:.3f}s"
        )

    @staticmethod
    def _format_receive_summary(result: ReceiveSessionResult) -> str:
        return (
            "receive summary: "
            f"total={result.total_entries}, success={result.successful_entries}, "
            f"skipped={result.skipped_entries}, renamed={result.renamed_entries}, "
            f"failed={result.failed_entries}, bytes={result.total_bytes_received}, "
            f"elapsed={result.elapsed_seconds:.3f}s"
        )


def launch_desktop_app() -> int:
    app = FileFerryDesktopApp()
    app.mainloop()
    return 0
