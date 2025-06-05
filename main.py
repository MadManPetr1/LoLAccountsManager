# main.py
import sys
from PySide6.QtWidgets import QApplication
from app.ui_main import MainWindow

if __name__ == "__main__":
    # QGuiApplication.setHighDpiScaleFactorRoundingPolicy must be called
    # before creating QApplication, so we do it in ui_main if needed.
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())