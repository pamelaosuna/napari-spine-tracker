from qtpy.QtWidgets import QVBoxLayout
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QWidget,
    QLabel,
    QDialog,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    )

class NamePatternLoader(QDialog):
    """
    Dialog to pop up when the user tries to load a csv file with no data.
    Allows the user to enter the name pattern of the images to load.
    """
    def __init__(self,
                 manager,
                 parent:QWidget):
        super().__init__(parent)
        self.manager = manager

        self.setWindowTitle("Name Pattern")
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(200, 100)

        self._prepare_dialog()
    
    def _prepare_dialog(self):
        main_layout = QVBoxLayout(self)
        # text with the instructions first
        label = QLabel("No detections found in csv file. Please enter the name pattern of the images to load:")
        main_layout.addWidget(label)
        # line edit then
        self.text_pattern = QLineEdit()
        self.text_pattern.setPlaceholderText("e.g. aidv890_date010203_tp2_stack7_sub11")
        self.text_pattern.setFocus()
        self.text_pattern.returnPressed.connect(self._update_pattern)

        main_layout.addWidget(self.text_pattern)
        self.setLayout(main_layout)

    def _update_pattern(self):
        if self.text_pattern.text() != "":
            self.manager.name_pattern = self.text_pattern.text()
            self.close()