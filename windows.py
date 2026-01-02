import sys
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QPushButton
from PySide6.QtWidgets import QLineEdit, QLabel,QVBoxLayout, QMessageBox


class Win(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Hello Qt")
        self.resize(400, 300)

        # Text input box
        self.edit = QLineEdit() 
        self.edit.setPlaceholderText("Enter project path")

        # Submit button
        self.btn = QPushButton("Submit")

        # for text show
        self.out = QLabel("")

        layout = QVBoxLayout(self)
        layout.addWidget(self.edit)
        layout.addWidget(self.btn)
        layout.addWidget(self.btn, alignment=Qt.AlignHCenter)
        layout.addWidget(self.out)

    
        # Binding function and submit button
        self.btn.clicked.connect(self.on_submit)
        self.edit.returnPressed.connect(self.on_submit)

        # Let the window accept focus when clicked
        self.setFocusPolicy(Qt.StrongFocus)

    def mousePressEvent(self, event):
        # remove focus from QLineEdit after click any where on the background
        self.edit.clearFocus()

        # also remove focus from other widgets
        self.setFocus()
        super().mousePressEvent(event)

    def on_submit(self):
        text = self.edit.text()
        judge = self.check_path(text)
        if judge:
            self.out.setText(f"You typed: {text}")
    
    def check_path(self, path):
        p = Path(path)
        exists = p.exists()
        is_dir = p.is_dir()

        if exists and is_dir:
            self.project_path = path
            return True
        else:
            QMessageBox.warning(self, "Warning", "Please enter a valid project path!")
            return False

            
    def load_project():
        pass

if __name__ == "__main__":

    # Main window
    app = QApplication(sys.argv)

    # Load .qss path (a file similar to css)
    qss_path = r"./style/window.qss"
    qss = Path(qss_path).read_text(encoding="utf-8")
    app.setStyleSheet(qss)

    # Create a window
    w = Win()
    w.resize(480, 170)
    w.show()
    sys.exit(app.exec())
