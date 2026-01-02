import sys
from PySide6.QtWidgets import QApplication, QWidget




if __name__ == "__main__":
    # Main window
    app = QApplication(sys.argv)

    w=QWidget()
    w.setWindowTitle("Hello Qt")
    w.resize(400, 300)
    w.show()

    sys.exit(app.exec())
