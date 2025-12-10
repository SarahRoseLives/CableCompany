# main.py
import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import IPTVViewer


def main():
    app = QApplication(sys.argv)

    # "Fusion" style is the best base for custom themes
    app.setStyle("Fusion")

    window = IPTVViewer()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()