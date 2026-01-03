import sys
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox
from PySide6.QtWidgets import QLineEdit, QLabel,QVBoxLayout, QHBoxLayout 

from utils import Process


class Win(QWidget):
    def __init__(self):
        super().__init__()
        self.project_path = None
        self.p = None  # Process object
        
        self.setWindowTitle("Hello Qt")
        self.resize(400, 300)

        # -------------------- Components --------------------
        # Text input box
        self.edit = QLineEdit() 
        self.edit.setPlaceholderText("Enter project path")


        # Submit button
        self.btn = QPushButton("Submit")
        self.btn.setObjectName("submitBtn")
        # Process button
        self.process_btn = QPushButton("Process")
        self.process_btn.setObjectName("processBtn")
        # Copy button
        self.copy_btn = QPushButton("Copy Attachments")
        self.copy_btn.setObjectName("copyBtn")
        # Delete empty directories button
        self.delete_btn = QPushButton("Delete Empty Directories")
        self.delete_btn.setObjectName("deleteBtn")

        # Add pointer
        for b in self.findChildren(QPushButton):
            b.setCursor(Qt.PointingHandCursor)


        # for text show
        self.out = QLabel("")

        # -------------------- Layout --------------------
        layout = QVBoxLayout(self) # QVBoxLayout is vertical layout
        layout.addWidget(self.edit)
        # layout.addWidget(self.btn, alignment=Qt.AlignHCenter)
        layout.addWidget(self.btn)
        layout.addWidget(self.out)

        row = QHBoxLayout() # QHBoxLayout is horizontal layout
        row.addWidget(self.process_btn, 1)
        row.addStretch() # This creates a flexible space between the two buttons
        row.addWidget(self.copy_btn, 1)        
        layout.addLayout(row)
        row.setSpacing(10)  # Set spacing between buttons
        layout.addWidget(self.delete_btn)

        # layout.addStretch(1) 
        
    
        # Binding function and submit button
        self.btn.clicked.connect(self.on_submit)
        self.edit.returnPressed.connect(self.on_submit)
        # Binding function and process button
        self.process_btn.clicked.connect(self.load_project)
        # Binding function and copy button
        self.copy_btn.clicked.connect(self.copy_attachments)
        # Binding function and delete button
        self.delete_btn.clicked.connect(self.remove_empty_directories)


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
            self.out.setText(f"The project path is set: {text}")
    
    def check_path(self, path):
        if path == "":
            # if the path is empty, show warning
            QMessageBox.warning(self, "Warning", "The project path is empty!")
            return False

        p = Path(path)
        exists = p.exists()
        is_dir = p.is_dir()

        if exists and is_dir:
            self.project_path = path
            return True
        else:
            QMessageBox.warning(self, "Warning", "Please enter a valid project path!")
            return False

            
    def load_project(self):
        if self.project_path is None:
            QMessageBox.warning(self, "Warning", "Please set the project path first!")
            return
        self.p = Process(self.project_path, "attachments")
        num_md_files = len(self.p.list_of_md_files)
        num_attachments = len(self.p.attachments)

        if num_md_files == 0:
            QMessageBox.warning(self, "Warning", "No markdown files found in the project path!")
            self.project_path = None
            return

        self.p = Process(self.project_path, "attachments")
        QMessageBox.information(self, "Info", f"Process done!\nFind {num_md_files} markdown files.\nFind {num_attachments} attachments.")

    def copy_attachments(self):
        if self.p is None:
            QMessageBox.warning(self, "Warning", "Please load the project first!")
            return
        
        if self.p.copy_attachments():
            QMessageBox.information(self, "Info", "Attachments copied successfully!")
        else:
            QMessageBox.warning(self, "Warning", "No markdown files to process. Please load the project first!")
        pass
    
    def remove_empty_directories(self):
        if self.p is None:
            QMessageBox.warning(self, "Warning", "Please load the project first!")
            return
        
        num_removed = self.p.remove_empty_directories()
        QMessageBox.information(self, "Info", f"Removed {num_removed} empty directories.")
    

if __name__ == "__main__":
    app = QApplication(sys.argv)

    qss_path = r"./style/window.qss"
    qss = Path(qss_path).read_text(encoding="utf-8")
    app.setStyleSheet(qss)

    w = Win()
    w.resize(480, 170)
    w.show()
    sys.exit(app.exec())
