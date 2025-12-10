# ui/sidebar.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QListWidget, QListWidgetItem,
                             QProgressBar, QStyle)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from core.scanner import ScannerWorker


class Sidebar(QWidget):
    # Signal: Emits (channel_name, channel_ip)
    channel_selected = pyqtSignal(str, str)
    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(280)  # Slightly wider for cross-platform fonts

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.scanner_thread = None

        self.setup_ui()

    def setup_ui(self):
        # --- Header ---
        header = QWidget()
        header.setObjectName("SidebarHeader")
        header_layout = QVBoxLayout(header)

        # Title
        title_layout = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(self.style().standardPixmap(QStyle.SP_ComputerIcon))
        title_text = QLabel("Channels")
        title_text.setStyleSheet("font-weight: bold; font-size: 16px; color: white;")
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_text)
        title_layout.addStretch()

        # Scan Button
        btn_layout = QHBoxLayout()
        self.scan_btn = QPushButton(" Scan Network")
        self.scan_btn.setObjectName("ScanBtn")
        self.scan_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.scan_btn.setCursor(Qt.PointingHandCursor)
        self.scan_btn.clicked.connect(self.start_scan)

        filter_btn = QPushButton()
        filter_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        filter_btn.setObjectName("FilterBtn")
        filter_btn.setFixedSize(30, 30)

        btn_layout.addWidget(self.scan_btn)
        btn_layout.addWidget(filter_btn)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(
            "QProgressBar { background: #4a5568; border: none; } QProgressBar::chunk { background: #4299e1; }")
        self.progress_bar.hide()

        header_layout.addLayout(title_layout)
        header_layout.addSpacing(10)
        header_layout.addLayout(btn_layout)
        header_layout.addWidget(self.progress_bar)

        # --- List Area ---
        self.channel_list = QListWidget()
        self.channel_list.itemClicked.connect(self.on_item_clicked)
        self.channel_list.hide()

        self.empty_state = QLabel("No channels found.\nClick Scan to search.")
        self.empty_state.setAlignment(Qt.AlignCenter)
        self.empty_state.setStyleSheet("color: #718096; font-style: italic; padding: 20px;")

        # --- Footer ---
        footer = QLabel("Protocol: UDP/RTP")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("padding: 8px; color: #718096; font-size: 11px; border-top: 1px solid #2d3748;")

        self.layout.addWidget(header)
        self.layout.addWidget(self.empty_state)
        self.layout.addWidget(self.channel_list)
        self.layout.addWidget(footer)

    def start_scan(self):
        # Update UI for scanning state
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText(" Stop Scan")

        # Switch button functionality to STOP
        try:
            self.scan_btn.clicked.disconnect()
        except TypeError:
            pass  # Handle case where nothing was connected
        self.scan_btn.clicked.connect(self.stop_scan)

        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.channel_list.clear()
        self.channel_list.hide()
        self.empty_state.show()

        # Initialize Real Scanner
        # Scanning 239.255.0.1 to 239.255.0.20 on port 1234 (Based on your Go code)
        self.scanner_thread = ScannerWorker(start_ip="239.255.0.1", port=1234, limit=20)

        # Connect signals
        self.scanner_thread.progress.connect(self.update_progress_bar)
        self.scanner_thread.status.connect(lambda msg: self.status_message.emit(msg))
        self.scanner_thread.channel_found.connect(self.add_channel_item)
        self.scanner_thread.finished.connect(self.finish_scan)

        self.scanner_thread.start()

    def stop_scan(self):
        if self.scanner_thread and self.scanner_thread.isRunning():
            self.status_message.emit("Stopping scan...")
            self.scanner_thread.stop()
            self.scanner_thread.wait()
        # finish_scan will be called by the thread finishing,
        # but if we forced it, we might need to reset UI manually if the thread logic differs
        self.finish_scan(0)

    def update_progress_bar(self, val):
        self.progress_bar.setValue(val)

    def add_channel_item(self, name, ip):
        self.empty_state.hide()
        self.channel_list.show()

        item = QListWidgetItem(self.channel_list)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        # Margins critical for text not being cut off on Linux
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("font-weight: bold; color: #e2e8f0; background: transparent;")

        # Display IP and Port (matching your Go port)
        ip_lbl = QLabel(f"{ip}:1234")
        ip_lbl.setStyleSheet("color: #718096; font-size: 11px; background: transparent;")

        layout.addWidget(name_lbl)
        layout.addWidget(ip_lbl)

        # Set size hint to ensure item has height
        item.setSizeHint(QSize(widget.sizeHint().width(), 55))

        self.channel_list.setItemWidget(item, widget)
        # Store data in item for retrieval
        item.setData(Qt.UserRole, (name, ip))

    def finish_scan(self, count):
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText(" Scan Network")

        # Reset button functionality to START
        try:
            self.scan_btn.clicked.disconnect()
        except TypeError:
            pass
        self.scan_btn.clicked.connect(self.start_scan)

        self.progress_bar.hide()

        # Update status message based on results
        # Note: 'count' here might be the total found, or just a signal arg
        # The worker emits the total count found
        msg = "Scan Complete."
        if isinstance(count, int) and count > 0:
            msg = f"Scan Complete. {count} channels found."
        elif self.channel_list.count() > 0:
            msg = f"Scan Complete. {self.channel_list.count()} channels found."

        self.status_message.emit(msg)

    def on_item_clicked(self, item):
        data = item.data(Qt.UserRole)
        if data:
            name, ip = data
            self.channel_selected.emit(name, ip)