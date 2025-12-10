# ui/sidebar.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QListWidget, QListWidgetItem,
                             QProgressBar, QStyle, QLineEdit, QComboBox, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from core.scanner import ScannerWorker


class Sidebar(QWidget):
    # Signals
    channel_selected = pyqtSignal(str, str)  # Emits (name, ip)
    status_message = pyqtSignal(str)  # Emits status text for the main window bar

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(280)  # Slightly wider for cross-platform font rendering

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.scanner_thread = None

        self.setup_ui()

    def setup_ui(self):
        # --- Header Section ---
        header = QWidget()
        header.setObjectName("SidebarHeader")
        header_layout = QVBoxLayout(header)

        # 1. Title Row
        title_layout = QHBoxLayout()
        title_icon = QLabel()
        title_icon.setPixmap(self.style().standardPixmap(QStyle.SP_ComputerIcon))
        title_text = QLabel("Channels")
        title_text.setStyleSheet("font-weight: bold; font-size: 16px; color: white;")
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_text)
        title_layout.addStretch()

        # 2. Mode Selection (Smart vs Custom)
        mode_layout = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Smart Scan (Auto)", "Custom Range"])
        self.mode_combo.setStyleSheet("""
            QComboBox { background: #171923; color: white; border: 1px solid #4a5568; padding: 3px; }
            QComboBox QAbstractItemView { background: #2d3748; color: white; selection-background-color: #3182ce; }
        """)
        self.mode_combo.currentIndexChanged.connect(self.toggle_inputs)
        mode_layout.addWidget(self.mode_combo)

        # 3. Custom Input (Hidden by default)
        self.range_input = QLineEdit("239.255.0.*")
        self.range_input.setPlaceholderText("e.g. 239.*.0.1")
        self.range_input.setToolTip(
            "Use * as a wildcard. Examples:\n239.255.0.* (Scans 0-255)\n239.*.0.1 (Scans subnets)")
        self.range_input.setStyleSheet("""
            QLineEdit { 
                background: #171923; 
                color: white; 
                border: 1px solid #4a5568; 
                border-radius: 4px; 
                padding: 4px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #63b3ed;
            }
        """)
        self.range_input.hide()  # Initially hidden

        # 4. Action Button
        btn_layout = QHBoxLayout()
        self.scan_btn = QPushButton(" Start Scan")
        self.scan_btn.setObjectName("ScanBtn")
        self.scan_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.scan_btn.setCursor(Qt.PointingHandCursor)
        self.scan_btn.clicked.connect(self.start_scan)

        btn_layout.addWidget(self.scan_btn)

        # 5. Progress Bar (Hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(
            "QProgressBar { background: #4a5568; border: none; } QProgressBar::chunk { background: #4299e1; }")
        self.progress_bar.hide()

        # Add all to header layout
        header_layout.addLayout(title_layout)
        header_layout.addSpacing(5)
        header_layout.addLayout(mode_layout)
        header_layout.addWidget(self.range_input)
        header_layout.addSpacing(5)
        header_layout.addLayout(btn_layout)
        header_layout.addWidget(self.progress_bar)

        # --- List Area ---
        self.channel_list = QListWidget()
        self.channel_list.itemClicked.connect(self.on_item_clicked)
        self.channel_list.hide()

        # Empty State
        self.empty_state = QLabel("Click 'Start Scan' to\nauto-discover channels.")
        self.empty_state.setAlignment(Qt.AlignCenter)
        self.empty_state.setStyleSheet("color: #718096; font-style: italic; padding: 20px;")

        # --- Footer ---
        footer = QLabel("Protocol: UDP Multicast")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("padding: 8px; color: #718096; font-size: 11px; border-top: 1px solid #2d3748;")

        # Final Assembly
        self.layout.addWidget(header)
        self.layout.addWidget(self.empty_state)
        self.layout.addWidget(self.channel_list)
        self.layout.addWidget(footer)

    def toggle_inputs(self):
        """Switches between Smart Scan (no input) and Custom Range (input visible)"""
        if self.mode_combo.currentIndex() == 1:  # Custom Range
            self.range_input.show()
            self.empty_state.setText("Enter range and scan.")
        else:  # Smart Scan
            self.range_input.hide()
            self.empty_state.setText("Click 'Start Scan' to\nauto-discover channels.")

    def start_scan(self):
        # 1. Safety Check: If thread is somehow already running, kill it first
        if self.scanner_thread and self.scanner_thread.isRunning():
            self.scanner_thread.stop()
            self.scanner_thread.wait()

        mode_idx = self.mode_combo.currentIndex()
        scan_mode = "smart" if mode_idx == 0 else "custom"
        custom_range = self.range_input.text().strip()

        # Validation for custom range
        if scan_mode == "custom" and (not custom_range or custom_range.count('.') != 3):
            self.status_message.emit("Error: Invalid IP format. Use 239.x.x.x")
            return

        # 2. Update UI State
        self.scan_btn.setEnabled(False)  # Temporarily disable to prevent double clicks
        self.scan_btn.setText(" Stop")

        # Swap click connection to stop_scan
        try:
            self.scan_btn.clicked.disconnect()
        except:
            pass
        self.scan_btn.clicked.connect(self.stop_scan)
        self.scan_btn.setEnabled(True)  # Re-enable

        # Reset List
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.channel_list.clear()
        self.channel_list.hide()
        self.empty_state.show()
        self.empty_state.setText("Scanning..." if scan_mode == "custom" else "Smart Scanning...")

        # 3. Initialize Scanner Thread
        # Port 1234 matches your Go streamer
        self.scanner_thread = ScannerWorker(mode=scan_mode, custom_range=custom_range, port=1234)

        # Connect Signals
        self.scanner_thread.progress.connect(self.update_progress_bar)
        self.scanner_thread.status.connect(lambda msg: self.status_message.emit(msg))
        self.scanner_thread.channel_found.connect(self.add_channel_item)

        # KEY: Connect 'finished' to 'finish_scan'
        # This ensures the UI only resets when the thread ACTUALLY dies.
        self.scanner_thread.finished.connect(self.finish_scan)

        self.scanner_thread.start()

    def stop_scan(self):
        """
        Signal the thread to stop, but DO NOT BLOCK the UI waiting for it.
        The 'finished' signal will trigger 'finish_scan' when it's done.
        """
        if self.scanner_thread and self.scanner_thread.isRunning():
            self.status_message.emit("Stopping scan...")
            self.scan_btn.setEnabled(False)  # Disable button to prevent spamming
            self.scan_btn.setText(" Stopping...")
            self.scanner_thread.stop()
            # WE DO NOT CALL wait() HERE. It freezes the GUI.

    def update_progress_bar(self, val):
        self.progress_bar.setValue(val)

    def add_channel_item(self, name, ip):
        # Found a channel? Hide empty state
        self.empty_state.hide()
        self.channel_list.show()

        # Create List Item
        item = QListWidgetItem(self.channel_list)

        # Custom Widget for multi-line support
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("font-weight: bold; color: #e2e8f0; background: transparent;")

        ip_lbl = QLabel(f"{ip}:1234")
        ip_lbl.setStyleSheet("color: #718096; font-size: 11px; background: transparent;")

        layout.addWidget(name_lbl)
        layout.addWidget(ip_lbl)

        # Set Item Size Hint (Crucial for Layout)
        item.setSizeHint(QSize(widget.sizeHint().width(), 55))

        self.channel_list.setItemWidget(item, widget)
        # Store metadata
        item.setData(Qt.UserRole, (name, ip))

    def finish_scan(self, count):
        # UI State: Ready
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText(" Start Scan")

        # Swap click connection back to start_scan
        try:
            self.scan_btn.clicked.disconnect()
        except:
            pass
        self.scan_btn.clicked.connect(self.start_scan)

        self.progress_bar.hide()

        msg = "Scan Complete."
        final_count = self.channel_list.count()
        if final_count > 0:
            msg = f"Scan Complete. {final_count} channels found."
        else:
            self.empty_state.setText("No channels found.")

        self.status_message.emit(msg)

    def on_item_clicked(self, item):
        data = item.data(Qt.UserRole)
        if data:
            name, ip = data
            self.channel_selected.emit(name, ip)