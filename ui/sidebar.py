# ui/sidebar.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QListWidget, QListWidgetItem,
                             QProgressBar, QStyle)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize
from core.mock_data import MOCK_CHANNELS


class Sidebar(QWidget):
    # Signal: Emits (channel_name, channel_ip)
    channel_selected = pyqtSignal(str, str)
    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(280)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

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
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText(" Scanning...")
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.channel_list.clear()
        self.channel_list.hide()
        self.empty_state.show()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_scan)
        self.scan_progress = 0
        self.timer.start(30)

    def update_scan(self):
        self.scan_progress += 2
        self.progress_bar.setValue(self.scan_progress)

        if self.scan_progress >= 100:
            self.timer.stop()
            self.finish_scan()

    def finish_scan(self):
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText(" Scan Network")
        self.progress_bar.hide()
        self.empty_state.hide()
        self.channel_list.show()

        for name, ip in MOCK_CHANNELS:
            self.add_channel_item(name, ip)

        self.status_message.emit(f"Scan Complete. {len(MOCK_CHANNELS)} channels found.")

    def add_channel_item(self, name, ip):
        item = QListWidgetItem(self.channel_list)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("font-weight: bold; color: #e2e8f0; background: transparent;")

        ip_lbl = QLabel(f"{ip}:5000")
        ip_lbl.setStyleSheet("color: #718096; font-size: 11px; background: transparent;")

        layout.addWidget(name_lbl)
        layout.addWidget(ip_lbl)

        item.setSizeHint(QSize(widget.sizeHint().width(), 55))
        self.channel_list.setItemWidget(item, widget)
        # Store data in item for retrieval
        item.setData(Qt.UserRole, (name, ip))

    def on_item_clicked(self, item):
        data = item.data(Qt.UserRole)
        if data:
            name, ip = data
            self.channel_selected.emit(name, ip)