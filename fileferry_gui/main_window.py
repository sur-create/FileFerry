"""Main GUI window for FileFerry."""

from __future__ import annotations

import socket
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QCheckBox,
    QComboBox,
)

from fileferry.cli import default_output_dir
from fileferry.receiver import ReceiverConfig
from fileferry.sender import SessionSenderConfig
from .workers import ReceiverServerWorker, SendSessionWorker


class MainWindow(QMainWindow):
    """FileFerry desktop GUI (Chinese UI)."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FileFerry 文件传输")
        self.resize(1180, 760)

        self._send_worker: Optional[SendSessionWorker] = None
        self._receiver_worker: Optional[ReceiverServerWorker] = None
        self._sender_connected = False

        self._init_ui()
        self._apply_styles()
        self._update_sender_status(False, "未连接")
        self._update_receiver_status(False, "监听未开启")

    def _init_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)

        title = QLabel("FileFerry V1.3 桌面版")
        title.setObjectName("TitleLabel")
        subtitle = QLabel("跨平台文件/文件夹传输（中文界面，手动连接控制）")
        subtitle.setObjectName("SubtitleLabel")

        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)

        splitter = QSplitter(Qt.Orientation.Vertical)

        upper = QWidget()
        upper_layout = QHBoxLayout(upper)
        upper_layout.setContentsMargins(0, 0, 0, 0)
        upper_layout.setSpacing(12)

        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self._build_send_tab(), "发送端")
        self.tab_widget.addTab(self._build_receive_tab(), "接收端")

        upper_layout.addWidget(self.tab_widget)
        splitter.addWidget(upper)

        log_panel = QGroupBox("会话日志")
        log_layout = QVBoxLayout(log_panel)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        log_layout.addWidget(self.log_view)

        splitter.addWidget(log_panel)
        splitter.setSizes([500, 220])

        root_layout.addWidget(splitter)

    def _build_send_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        conn_box = QGroupBox("连接设置")
        conn_layout = QHBoxLayout(conn_box)

        self.send_host_input = QLineEdit("127.0.0.1")
        self.send_port_input = QSpinBox()
        self.send_port_input.setRange(1, 65535)
        self.send_port_input.setValue(9000)

        self.send_connect_btn = QPushButton("开启连接")
        self.send_disconnect_btn = QPushButton("断开连接")
        self.send_disconnect_btn.setEnabled(False)
        self.send_status_label = QLabel()

        conn_layout.addWidget(QLabel("目标 IP"))
        conn_layout.addWidget(self.send_host_input, 2)
        conn_layout.addWidget(QLabel("端口"))
        conn_layout.addWidget(self.send_port_input)
        conn_layout.addWidget(self.send_connect_btn)
        conn_layout.addWidget(self.send_disconnect_btn)
        conn_layout.addWidget(self.send_status_label, 2)

        sources_box = QGroupBox("发送内容")
        sources_layout = QVBoxLayout(sources_box)

        self.send_sources_list = QListWidget()
        self.send_sources_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)

        source_btn_row = QHBoxLayout()
        self.add_file_btn = QPushButton("添加文件")
        self.add_dir_btn = QPushButton("添加文件夹")
        self.remove_selected_btn = QPushButton("移除选中")
        self.clear_sources_btn = QPushButton("清空列表")

        source_btn_row.addWidget(self.add_file_btn)
        source_btn_row.addWidget(self.add_dir_btn)
        source_btn_row.addWidget(self.remove_selected_btn)
        source_btn_row.addWidget(self.clear_sources_btn)
        source_btn_row.addStretch(1)

        sources_layout.addWidget(self.send_sources_list)
        sources_layout.addLayout(source_btn_row)

        options_box = QGroupBox("发送策略")
        options_layout = QHBoxLayout(options_box)

        self.send_conflict_combo = QComboBox()
        self.send_conflict_combo.addItem("覆盖已有文件", "overwrite")
        self.send_conflict_combo.addItem("跳过冲突文件", "skip")
        self.send_conflict_combo.addItem("自动重命名", "rename")

        self.send_continue_checkbox = QCheckBox("失败后继续")
        self.send_continue_checkbox.setChecked(True)

        self.send_timeout_input = QSpinBox()
        self.send_timeout_input.setRange(1, 120)
        self.send_timeout_input.setValue(10)

        self.send_chunk_input = QSpinBox()
        self.send_chunk_input.setRange(1024, 1024 * 1024)
        self.send_chunk_input.setSingleStep(1024)
        self.send_chunk_input.setValue(64 * 1024)

        self.send_start_btn = QPushButton("开始发送")
        self.send_start_btn.setObjectName("PrimaryButton")
        self.send_start_btn.setEnabled(False)

        options_layout.addWidget(QLabel("冲突策略"))
        options_layout.addWidget(self.send_conflict_combo)
        options_layout.addWidget(self.send_continue_checkbox)
        options_layout.addWidget(QLabel("超时(秒)"))
        options_layout.addWidget(self.send_timeout_input)
        options_layout.addWidget(QLabel("块大小(字节)"))
        options_layout.addWidget(self.send_chunk_input)
        options_layout.addStretch(1)
        options_layout.addWidget(self.send_start_btn)

        summary_box = QGroupBox("最近一次发送摘要")
        summary_layout = QHBoxLayout(summary_box)
        self.send_summary_label = QLabel("暂无")
        self.send_summary_label.setWordWrap(True)
        summary_layout.addWidget(self.send_summary_label)

        layout.addWidget(conn_box)
        layout.addWidget(sources_box, 1)
        layout.addWidget(options_box)
        layout.addWidget(summary_box)

        self.send_connect_btn.clicked.connect(self._on_sender_connect)
        self.send_disconnect_btn.clicked.connect(self._on_sender_disconnect)
        self.add_file_btn.clicked.connect(self._on_add_files)
        self.add_dir_btn.clicked.connect(self._on_add_dir)
        self.remove_selected_btn.clicked.connect(self._on_remove_selected_sources)
        self.clear_sources_btn.clicked.connect(self.send_sources_list.clear)
        self.send_start_btn.clicked.connect(self._on_start_send)

        self.send_host_input.textChanged.connect(self._on_sender_config_changed)
        self.send_port_input.valueChanged.connect(self._on_sender_config_changed)

        return tab

    def _build_receive_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        conn_box = QGroupBox("监听设置")
        conn_layout = QHBoxLayout(conn_box)

        self.recv_host_input = QLineEdit("0.0.0.0")
        self.recv_port_input = QSpinBox()
        self.recv_port_input.setRange(1, 65535)
        self.recv_port_input.setValue(9000)

        self.recv_output_input = QLineEdit(str(default_output_dir()))
        self.recv_browse_btn = QPushButton("选择目录")

        conn_layout.addWidget(QLabel("监听 IP"))
        conn_layout.addWidget(self.recv_host_input, 1)
        conn_layout.addWidget(QLabel("端口"))
        conn_layout.addWidget(self.recv_port_input)
        conn_layout.addWidget(QLabel("保存目录"))
        conn_layout.addWidget(self.recv_output_input, 2)
        conn_layout.addWidget(self.recv_browse_btn)

        control_box = QGroupBox("连接控制")
        control_layout = QHBoxLayout(control_box)

        self.recv_conflict_combo = QComboBox()
        self.recv_conflict_combo.addItem("覆盖已有文件", "overwrite")
        self.recv_conflict_combo.addItem("跳过冲突文件", "skip")
        self.recv_conflict_combo.addItem("自动重命名", "rename")

        self.recv_continue_checkbox = QCheckBox("失败后继续")
        self.recv_continue_checkbox.setChecked(True)

        self.recv_timeout_input = QSpinBox()
        self.recv_timeout_input.setRange(1, 120)
        self.recv_timeout_input.setValue(10)

        self.recv_chunk_input = QSpinBox()
        self.recv_chunk_input.setRange(1024, 1024 * 1024)
        self.recv_chunk_input.setSingleStep(1024)
        self.recv_chunk_input.setValue(64 * 1024)

        self.recv_start_btn = QPushButton("开启连接")
        self.recv_start_btn.setObjectName("PrimaryButton")
        self.recv_stop_btn = QPushButton("断开连接")
        self.recv_stop_btn.setEnabled(False)
        self.recv_status_label = QLabel()

        control_layout.addWidget(QLabel("冲突策略"))
        control_layout.addWidget(self.recv_conflict_combo)
        control_layout.addWidget(self.recv_continue_checkbox)
        control_layout.addWidget(QLabel("超时(秒)"))
        control_layout.addWidget(self.recv_timeout_input)
        control_layout.addWidget(QLabel("块大小(字节)"))
        control_layout.addWidget(self.recv_chunk_input)
        control_layout.addStretch(1)
        control_layout.addWidget(self.recv_start_btn)
        control_layout.addWidget(self.recv_stop_btn)
        control_layout.addWidget(self.recv_status_label)

        summary_box = QGroupBox("最近一次接收摘要")
        summary_layout = QHBoxLayout(summary_box)
        self.recv_summary_label = QLabel("暂无")
        self.recv_summary_label.setWordWrap(True)
        summary_layout.addWidget(self.recv_summary_label)

        layout.addWidget(conn_box)
        layout.addWidget(control_box)
        layout.addWidget(summary_box)
        layout.addStretch(1)

        self.recv_browse_btn.clicked.connect(self._on_pick_output_dir)
        self.recv_start_btn.clicked.connect(self._on_receiver_start)
        self.recv_stop_btn.clicked.connect(self._on_receiver_stop)

        return tab

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow { background-color: #eef2f7; }
            QLabel#TitleLabel { font-size: 24px; font-weight: 700; color: #1f2937; }
            QLabel#SubtitleLabel { font-size: 13px; color: #4b5563; }
            QGroupBox {
                border: 1px solid #d1d9e6;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #ffffff;
                font-size: 13px;
                font-weight: 600;
                color: #1f2937;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
            QLineEdit, QSpinBox, QComboBox, QListWidget, QTextEdit {
                border: 1px solid #c8d1df;
                border-radius: 8px;
                padding: 6px;
                background-color: #fcfdff;
                font-size: 13px;
            }
            QPushButton {
                border: 1px solid #c7d0de;
                border-radius: 8px;
                padding: 8px 12px;
                background-color: #f7f9fc;
                color: #1f2937;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #edf3ff; }
            QPushButton:disabled {
                color: #9aa5b1;
                background-color: #f1f4f8;
            }
            QPushButton#PrimaryButton {
                background-color: #2563eb;
                border: 1px solid #1d4ed8;
                color: #ffffff;
            }
            QPushButton#PrimaryButton:hover { background-color: #1d4ed8; }
            """
        )

    def _log(self, message: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_view.append(f"[{ts}] {message}")

    def _show_error(self, title: str, detail: str) -> None:
        QMessageBox.critical(self, title, detail)
        self._log(f"错误：{title} - {detail}")

    def _update_sender_status(self, connected: bool, text: str) -> None:
        self._sender_connected = connected
        color = "#059669" if connected else "#b91c1c"
        self.send_status_label.setText(f"<b style='color:{color};'>{text}</b>")
        self.send_connect_btn.setEnabled(not connected)
        self.send_disconnect_btn.setEnabled(connected)
        self.send_start_btn.setEnabled(connected and self.send_sources_list.count() > 0)

    def _update_receiver_status(self, listening: bool, text: str) -> None:
        color = "#0f766e" if listening else "#7f1d1d"
        self.recv_status_label.setText(f"<b style='color:{color};'>{text}</b>")
        self.recv_start_btn.setEnabled(not listening)
        self.recv_stop_btn.setEnabled(listening)

    def _on_sender_config_changed(self) -> None:
        if self._sender_connected:
            self._update_sender_status(False, "参数已变更，请重新开启连接")

    def _on_sender_connect(self) -> None:
        host = self.send_host_input.text().strip()
        port = self.send_port_input.value()
        if not host:
            self._show_error("连接失败", "目标 IP 不能为空")
            return

        try:
            with socket.create_connection((host, port), timeout=3):
                pass
        except OSError as exc:
            self._show_error("连接失败", f"无法连接 {host}:{port}\n{exc}")
            return

        self._update_sender_status(True, f"已连接 {host}:{port}")
        self._log(f"发送端连接已开启：{host}:{port}")

    def _on_sender_disconnect(self) -> None:
        self._update_sender_status(False, "已断开")
        self._log("发送端连接已断开")

    def _on_add_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, "选择要发送的文件")
        for file_path in files:
            self._add_source_item(file_path)

    def _on_add_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择要发送的文件夹")
        if folder:
            self._add_source_item(folder)

    def _add_source_item(self, path_text: str) -> None:
        normalized = str(Path(path_text).expanduser())
        for row in range(self.send_sources_list.count()):
            if self.send_sources_list.item(row).text() == normalized:
                return
        self.send_sources_list.addItem(QListWidgetItem(normalized))
        self.send_start_btn.setEnabled(self._sender_connected and self.send_sources_list.count() > 0)

    def _on_remove_selected_sources(self) -> None:
        selected = self.send_sources_list.selectedItems()
        for item in selected:
            self.send_sources_list.takeItem(self.send_sources_list.row(item))
        self.send_start_btn.setEnabled(self._sender_connected and self.send_sources_list.count() > 0)

    def _collect_send_sources(self) -> List[Path]:
        sources: List[Path] = []
        for row in range(self.send_sources_list.count()):
            sources.append(Path(self.send_sources_list.item(row).text()))
        return sources

    def _on_start_send(self) -> None:
        if self._send_worker is not None and self._send_worker.isRunning():
            self._show_error("发送中", "当前已有发送任务在运行")
            return

        sources = self._collect_send_sources()
        if not sources:
            self._show_error("发送失败", "请先添加要发送的文件或文件夹")
            return

        config = SessionSenderConfig(
            host=self.send_host_input.text().strip(),
            port=self.send_port_input.value(),
            sources=sources,
            timeout=float(self.send_timeout_input.value()),
            chunk_size=int(self.send_chunk_input.value()),
            conflict_policy=str(self.send_conflict_combo.currentData()),
            continue_on_error=self.send_continue_checkbox.isChecked(),
        )

        self._send_worker = SendSessionWorker(config)
        self._send_worker.completed.connect(self._on_send_completed)
        self._send_worker.failed.connect(self._on_send_failed)
        self._send_worker.finished.connect(self._on_send_finished)

        self.send_start_btn.setEnabled(False)
        self._log("开始发送会话...")
        self._send_worker.start()

    def _on_send_completed(self, result: object) -> None:
        summary = (
            f"总条目 {result.total_entries}，成功 {result.successful_entries}，"
            f"跳过 {result.skipped_entries}，重命名 {result.renamed_entries}，"
            f"失败 {result.failed_entries}，发送字节 {result.total_bytes_sent}，"
            f"耗时 {result.elapsed_seconds:.2f}s"
        )
        self.send_summary_label.setText(summary)
        self._log(f"发送完成：{summary}")

        if result.failed_entries > 0:
            for entry in result.entry_results:
                if entry.status == "error":
                    self._log(f"条目失败：{entry.relative_path}（{entry.kind}）- {entry.detail}")
            QMessageBox.warning(self, "发送完成（含失败）", "会话已完成，但有部分条目失败。")

    def _on_send_failed(self, message: str) -> None:
        self._show_error("发送失败", message)
        self._update_sender_status(False, "连接异常，已断开")

    def _on_send_finished(self) -> None:
        self.send_start_btn.setEnabled(self._sender_connected and self.send_sources_list.count() > 0)

    def _on_pick_output_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择接收保存目录")
        if folder:
            self.recv_output_input.setText(folder)

    def _on_receiver_start(self) -> None:
        if self._receiver_worker is not None and self._receiver_worker.isRunning():
            self._show_error("监听中", "监听已开启，无需重复开启")
            return

        output_dir = Path(self.recv_output_input.text().strip() or str(default_output_dir())).expanduser()
        config = ReceiverConfig(
            host=self.recv_host_input.text().strip() or "0.0.0.0",
            port=self.recv_port_input.value(),
            output_dir=output_dir,
            timeout=float(self.recv_timeout_input.value()),
            chunk_size=int(self.recv_chunk_input.value()),
            conflict_policy=str(self.recv_conflict_combo.currentData()),
            continue_on_error=self.recv_continue_checkbox.isChecked(),
        )

        worker = ReceiverServerWorker(config)
        worker.listening_started.connect(self._on_receiver_listening_started)
        worker.listening_stopped.connect(self._on_receiver_listening_stopped)
        worker.server_error.connect(self._on_receiver_server_error)
        worker.session_completed.connect(self._on_receiver_session_completed)
        worker.session_failed.connect(self._on_receiver_session_failed)

        self._receiver_worker = worker
        self._update_receiver_status(True, "监听启动中...")
        self._log("正在开启接收端监听...")
        worker.start()

    def _on_receiver_stop(self) -> None:
        worker = self._receiver_worker
        if worker is None:
            return
        self._log("正在关闭接收端监听...")
        worker.stop()

    def _on_receiver_listening_started(self, message: str) -> None:
        self._update_receiver_status(True, "已开启")
        self._log(message)

    def _on_receiver_listening_stopped(self, message: str) -> None:
        self._update_receiver_status(False, "已断开")
        self._log(message)

    def _on_receiver_server_error(self, message: str) -> None:
        self._update_receiver_status(False, "监听异常")
        self._show_error("监听失败", message)

    def _on_receiver_session_completed(self, result: object) -> None:
        summary = (
            f"总条目 {result.total_entries}，成功 {result.successful_entries}，"
            f"跳过 {result.skipped_entries}，重命名 {result.renamed_entries}，"
            f"失败 {result.failed_entries}，接收字节 {result.total_bytes_received}，"
            f"耗时 {result.elapsed_seconds:.2f}s"
        )
        self.recv_summary_label.setText(summary)
        self._log(f"接收会话完成：{summary}")

        if result.failed_entries > 0:
            for entry in result.entry_results:
                if entry.status == "error":
                    self._log(f"接收条目失败：{entry.relative_path}（{entry.kind}）- {entry.detail}")

    def _on_receiver_session_failed(self, message: str) -> None:
        self._log(message)

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._receiver_worker is not None and self._receiver_worker.isRunning():
            self._receiver_worker.stop()
            self._receiver_worker.wait(1500)

        if self._send_worker is not None and self._send_worker.isRunning():
            self._send_worker.wait(1500)

        super().closeEvent(event)
