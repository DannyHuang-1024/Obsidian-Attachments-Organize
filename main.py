import os
import sys
from utils import Process
import pathlib as Path

from PySide6.QtWidgets import QApplication
from windows import Win

project_path = r".\resources\test"

if __name__ == "__main__":
    p = Process(project_path)
    p.copy_attachments()
    p.remove_unused_attachments()

    # # Main window
    # app = QApplication(sys.argv)

    # # Load .qss path (a file similar to css)
    # qss_path = r"./style/window.qss"
    # qss = Path(qss_path).read_text(encoding="utf-8")
    # app.setStyleSheet(qss)

    # # Create a window
    # w = Win()
    # w.resize(480, 170)
    # w.show()
    # sys.exit(app.exec())







