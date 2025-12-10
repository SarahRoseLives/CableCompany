# ui/video_player.py

import random
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QSlider, QSizePolicy, QStyle)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt5.QtGui import QColor


class VideoPlayer(QWidget):
    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.is_playing = False
        self.is_recording = False

        self.setup_ui()

    def setup_ui(self):
        # --- Video Frame ---
        self.video_frame = QFrame()
        self.video_frame.setObjectName("VideoFrame")
        self.video_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        vf_layout = QVBoxLayout(self.video_frame)
        self.placeholder = QLabel("Select a channel to start streaming")
        self.placeholder.setObjectName("PlaceholderText")
        self.placeholder.setAlignment(Qt.AlignCenter)
        vf_layout.addWidget(self.placeholder)

        # OSD
        self.osd = QLabel(self.video_frame)
        self.osd.setStyleSheet("background-color: rgba(0,0,0,180); color: white; padding: 10px; border-radius: 4px;")
        self.osd.hide()

        # --- Controls ---
        controls = QWidget()
        controls.setObjectName("ControlsBar")
        controls.setFixedHeight(65)
        c_layout = QHBoxLayout(controls)
        c_layout.setContentsMargins(20, 0, 20, 0)

        # Play Button
        self.play_btn = QPushButton()
        self.play_btn.setFixedSize(40, 40)
        self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_btn.setStyleSheet("border-radius: 20px; background-color: rgba(255,255,255,0.1); border: none;")
        self.play_btn.clicked.connect(self.toggle_play)

        # Volume
        vol_icon = QLabel()
        vol_icon.setPixmap(self.style().standardPixmap(QStyle.SP_MediaVolume))

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #4a5568; border-radius: 2px; }
            QSlider::sub-page:horizontal { background: #4299e1; border-radius: 2px; }
            QSlider::handle:horizontal { background: white; width: 12px; margin: -4px 0; border-radius: 6px; }
        """)

        # Record Button
        self.rec_btn = QPushButton("Record")
        self.rec_btn.setObjectName("RecordBtn")
        self.rec_btn.setCheckable(True)
        self.rec_btn.clicked.connect(self.toggle_record)

        # Fullscreen Icon
        fs_btn = QPushButton()
        fs_btn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMaxButton))
        fs_btn.setStyleSheet("background: transparent; border: none;")

        # Layout Assembly
        c_layout.addWidget(self.play_btn)
        c_layout.addSpacing(15)
        c_layout.addWidget(vol_icon)
        c_layout.addWidget(self.volume_slider)
        c_layout.addStretch()
        c_layout.addWidget(self.rec_btn)
        c_layout.addSpacing(10)
        c_layout.addWidget(fs_btn)

        self.layout.addWidget(self.video_frame)
        self.layout.addWidget(controls)

    def play_stream(self, name, ip):
        self.is_playing = True
        self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.status_message.emit(f"Buffering: {name}...")

        self.placeholder.setText("")

        # Simulate video content with random gradient
        c1 = QColor(random.randint(20, 100), random.randint(20, 100), random.randint(100, 200)).name()
        c2 = QColor(random.randint(20, 100), random.randint(20, 100), random.randint(100, 200)).name()
        self.video_frame.setStyleSheet(
            f"QFrame#VideoFrame {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {c1}, stop:1 {c2}); }}")

        # Show OSD
        self.osd.setText(f"<b>{name}</b><br><span style='font-size:10px; color:#ccc'>1080p | {ip}</span>")
        self.osd.adjustSize()
        self.osd.move(self.video_frame.width() - self.osd.width() - 20, 20)
        self.osd.show()

        QTimer.singleShot(2500, self.osd.hide)
        QTimer.singleShot(1000, lambda: self.status_message.emit(f"Playing: {name} (12 Mbps)"))

    def toggle_play(self):
        self.is_playing = not self.is_playing
        icon = QStyle.SP_MediaPause if self.is_playing else QStyle.SP_MediaPlay
        self.play_btn.setIcon(self.style().standardIcon(icon))

        if not self.is_playing:
            self.status_message.emit("Paused")
            self.video_frame.setStyleSheet("QFrame#VideoFrame { background-color: #1a202c; }")
            self.placeholder.setText("Paused")

    def toggle_record(self):
        if self.rec_btn.isChecked():
            self.is_recording = True
            self.rec_btn.setText(" Recording")
            self.status_message.emit("Recording started...")
        else:
            self.is_recording = False
            self.rec_btn.setText(" Record")
            self.status_message.emit("Recording Saved.")