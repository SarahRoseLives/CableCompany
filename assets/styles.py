# assets/styles.py

DARK_THEME_QSS = """
QMainWindow {
    background-color: #1a202c;
}
QWidget {
    font-family: 'DejaVu Sans', 'Arial', sans-serif;
    color: #e2e8f0;
    font-size: 14px;
}

/* --- Menu Bar --- */
QMenuBar {
    background-color: #2d3748;
    border-bottom: 1px solid #4a5568;
    color: #e2e8f0;
}
QMenuBar::item:selected {
    background-color: #4a5568;
}

/* --- Sidebar --- */
#Sidebar {
    background-color: #171923;
    border-right: 1px solid #4a5568;
}
#SidebarHeader {
    background-color: #2d3748;
    border-bottom: 1px solid #4a5568;
}
QPushButton#ScanBtn {
    background-color: #3182ce;
    color: white;
    border-radius: 4px;
    padding: 6px;
    font-weight: bold;
    border: none;
    text-align: center;
}
QPushButton#ScanBtn:hover {
    background-color: #4299e1;
}
QPushButton#ScanBtn:pressed {
    background-color: #2b6cb0;
}

/* --- Channel List --- */
QListWidget {
    background-color: #171923;
    border: none;
    outline: none;
}
QListWidget::item {
    border-bottom: 1px solid #2d3748;
}
QListWidget::item:selected {
    background-color: #2b6cb0;
    border-left: 4px solid #63b3ed;
}
QListWidget::item:hover:!selected {
    background-color: #2d3748;
}

/* --- Video Area --- */
#VideoFrame {
    background-color: black;
}
#PlaceholderText {
    color: #718096;
    font-size: 18px;
}

/* --- Controls Bar --- */
#ControlsBar {
    background-color: #2d3748;
    border-top: 1px solid #4a5568;
}
QPushButton.controlBtn {
    background-color: transparent;
    border: none;
    border-radius: 4px;
}
QPushButton.controlBtn:hover {
    background-color: #4a5568;
}

/* Record Button */
QPushButton#RecordBtn {
    border: 1px solid #718096;
    border-radius: 15px;
    padding: 4px 12px;
    color: #e2e8f0;
    background-color: transparent;
}
QPushButton#RecordBtn:checked {
    background-color: #742a2a;
    border: 1px solid #f56565;
    color: white;
}

/* --- Status Bar --- */
QStatusBar {
    background-color: #2a4365;
    color: white;
    font-size: 12px;
}
"""