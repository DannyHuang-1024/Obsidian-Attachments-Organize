import sys
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QMessageBox,
    QLineEdit, QLabel,QVBoxLayout, QHBoxLayout,
    QDialog
)

from utils import Process

BASE_DIR = Path(__file__).resolve().parent


class SettingWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Attachment Folder Name")
        self.edit = QLineEdit(self)
        self.edit.setPlaceholderText("Enter Attachments folder name")
        self.close_btn = QPushButton("Close")
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.clicked.connect(self.accept)  # closes dialog
        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("saveBtn")
        self.save_btn.clicked.connect(self.save_settings)
        
        qss_path = BASE_DIR / "style" / "settingWindow.qss"
        qss = qss_path.read_text(encoding="utf-8")
        self.setStyleSheet(qss)

        layout = QVBoxLayout(self)
        layout.addWidget(self.edit)
    
        row = QHBoxLayout()
        row.addWidget(self.save_btn)
        row.addWidget(self.close_btn)
        layout.addLayout(row)
    
    def save_settings(self):
        folder_name = self.edit.text().strip()
        if folder_name:
            QMessageBox.information(self, "Info", f"Attachment folder name set to: {folder_name}")
        else:
            folder_name = "attachments"  # default name
            QMessageBox.information(self, "Info", f"Attachment folder name set to default: {folder_name}")

        # Store the folder name
        self.folder_name = folder_name
        self.accept()  # Close the dialog
    
    def get_folder_name(self) -> str:
        return getattr(self, "folder_name", "")


class Win(QWidget):
    def __init__(self):
        super().__init__()
        self.project_path = None
        self.attachment_folder_name = "attachments"
        self.p = None  # Process object
        
        self.setWindowTitle("Obsidian Organizer")
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
        # Settings button
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setObjectName("settingsBtn")

        # Delete empty directories button
        self.remove_btn = QPushButton("Remove Empty Dirs")
        self.remove_btn.setObjectName("deleteBtn")

        # Add pointer
        for b in (self.btn, self.process_btn, self.remove_btn, self.settings_btn):
            b.setCursor(Qt.PointingHandCursor)


        # for text show
        self.out = QLabel("")

        # -------------------- Layout --------------------
        layout = QVBoxLayout(self) # QVBoxLayout is vertical layout
        layout.addWidget(self.edit)
        # layout.addWidget(self.btn, alignment=Qt.AlignHCenter)
        layout.addWidget(self.btn)
        layout.addWidget(self.process_btn)

        row = QHBoxLayout() # QHBoxLayout is horizontal layout
        row.addWidget(self.remove_btn, 1)
        row.addWidget(self.settings_btn, 1)
        layout.addStretch(1)
        layout.addLayout(row)
        layout.addWidget(self.out)
    
        # Binding function and submit button
        self.btn.clicked.connect(self.on_submit)
        self.edit.returnPressed.connect(self.on_submit)
        # Binding function and process button
        self.process_btn.clicked.connect(self.process)
        # Binding function and delete button
        self.remove_btn.clicked.connect(self.remove_trash)
        # Binding function and settings button
        self.settings_btn.clicked.connect(self.open_settings)

        # Let the window accept focus when clicked
        self.setFocusPolicy(Qt.StrongFocus)
    
    def open_settings(self):
        # modal (block main window until closed)
        dlg = SettingWindow(self)
        if dlg.exec() == QDialog.Accepted:
            folder_name = dlg.get_folder_name()
            if folder_name:
                self.out.setText(f"Attachment folder name set to: {folder_name}")
                self.attachment_folder_name = folder_name

    def mousePressEvent(self, event):
        # remove focus from QLineEdit after click any where on the background
        self.edit.clearFocus()

        # also remove focus from other widgets
        self.setFocus()
        super().mousePressEvent(event)

    def on_submit(self):
        """
        Submit the project path
        and load project if valid
        """
        text = self.edit.text()
        judge = self.check_path(text)
        if judge:
            self.out.setText(f"The project path is set: {text}")
            self.load_project()
    
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
        self.p = Process(self.project_path, self.attachment_folder_name)

        num_md_files = len(self.p.list_of_md_files)
        num_attachments = len(self.p.attachments)

        if num_md_files == 0:
            QMessageBox.warning(self, "Warning", "No markdown files found in the project path!")
            self.project_path = None
            return

        QMessageBox.information(self, "Info", f"Process done!\nFind {num_md_files} markdown files.\nFind {num_attachments} attachments.")

    def process(self):
        if self.p is None:
            QMessageBox.warning(self, "Warning", "Please load the project first!")
            return
        
        result = self.p.remove()
        QMessageBox.information(
            self,
            "Info",
            f"Removed {result['removed_attachments']} unused attachments and {result['removed_directories']} empty directories.",
        )

    def copy_attachments(self):
        if self.p is None:
            QMessageBox.warning(self, "Warning", "Please load the project first!")
            return
        
        if self.p.copy_attachments():
            QMessageBox.information(self, "Info", "Attachments copied successfully!")
        else:
            QMessageBox.warning(self, "Warning", "No markdown files to process. Please load the project first!")
    
    def remove_trash(self):
        if self.p is None:
            QMessageBox.warning(self, "Warning", "Please load the project first!")
            return
        
        num_dir_removed, failed = self.p.remove_empty_directories()
        msg = f"Removed {num_dir_removed} empty directories."
        if failed:
            msg += f"\nSkipped {len(failed)} directories."
        QMessageBox.information(self, "Info", msg)
        


if __name__ == "__main__":
    app = QApplication(sys.argv)

    qss_path = BASE_DIR / "style" / "window.qss"
    qss = qss_path.read_text(encoding="utf-8")
    app.setStyleSheet(qss)

    w = Win()
    w.resize(480, 170)
    w.show()
    sys.exit(app.exec())
