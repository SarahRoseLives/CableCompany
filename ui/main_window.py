# ui/main_window.py

from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QLabel
from assets.styles import DARK_THEME_QSS
from ui.sidebar import Sidebar
from ui.video_player import VideoPlayer


class IPTVViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CableCompany - IPTV Viewer")
        self.resize(1100, 750)
        self.setStyleSheet(DARK_THEME_QSS)

        self.setup_ui()

    def setup_ui(self):
        # Central Widget & Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Components
        self.create_menu_bar()

        self.sidebar = Sidebar()
        self.video_player = VideoPlayer()

        # Connect Components
        self.sidebar.channel_selected.connect(self.video_player.play_stream)
        self.sidebar.status_message.connect(self.update_status)
        self.video_player.status_message.connect(self.update_status)

        # Add to Layout
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.video_player)

        self.create_status_bar()

    def create_menu_bar(self):
        menu = self.menuBar()
        menu.addMenu("File")
        menu.addMenu("View")
        menu.addMenu("Settings")
        menu.addMenu("Help")

    def create_status_bar(self):
        self.status = self.statusBar()
        self.status.showMessage("Ready")

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 10, 0)

        lbl1 = QLabel("Multicast: Idle")
        lbl2 = QLabel("Disk: 450GB Free")

        layout.addWidget(lbl1)
        layout.addSpacing(15)
        layout.addWidget(lbl2)

        self.status.addPermanentWidget(container)

    def update_status(self, message):
        self.status.showMessage(message)