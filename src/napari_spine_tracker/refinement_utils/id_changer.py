import logging

from qtpy.QtCore import Qt
from qtpy.QtCore import Signal
from qtpy.QtWidgets import (
    QWidget,
    QLabel,
    QDialog,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    )
from qtpy.QtGui import QIntValidator

from napari.layers import Shapes
from napari.layers.shapes._shapes_constants import Mode
from napari.components.viewer_model import ViewerModel

logger = logging.getLogger(__name__)
class IdChanger(QDialog):
    id_changed = Signal(int, int) # old_id, new_id

    def __init__(self,
                 viz,
                 parent:QWidget,
                 viewer_model: ViewerModel,
                 shapes_layer: Shapes):
        super().__init__(parent)
        self.viz = viz
        self.viewer_model = viewer_model
        self.shapes_layer = shapes_layer

        # Validate selection
        if not self._validate_selection():
            return
        
        self._setup_dialog()
        self._setup_ui()
        self._connect_signals()

    def _validate_selection(self) -> bool:
        """
        Validate that a shape is selected
        """
        if len(self.shapes_layer.selected_data) == 0:
            QMessageBox.warning(
                self.parent(),
                'Selection Required',
                'Please select one rectangle before changing its ID.'
            )
            self.reject()
            return False
        
        self.idx_selected_shape = list(self.shapes_layer.selected_data)[-1]
        self.id_to_change = int(self.shapes_layer.features['id'].values[self.idx_selected_shape])
        return True
    
    def _setup_dialog(self):
        """
        Configure dialog properties.
        """
        self.setWindowTitle("Change ID")
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(300, 180)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

    def _setup_ui(self):
        """
        Create dialog UI.
        """
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Current ID info
        current_info = QLabel(f"Current ID: {self.id_to_change}")
        current_info.setStyleSheet("font-weight: bold; color: #2c3e50;")
        current_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(current_info)
        
        # Next available ID hint
        next_info = QLabel(f"Next available ID: {self.viz.next_new_id}")
        # next_info.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        next_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(next_info)
        
        # Input field
        self.text_id = QLineEdit()
        self.text_id.setPlaceholderText("Enter new ID")
        self.text_id.setValidator(QIntValidator(0, 99999))
        self.text_id.setText(str(self.viz.next_new_id))  # Pre-fill with suggested ID
        self.text_id.selectAll()  # Select all text for easy replacement
        layout.addWidget(self.text_id)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.cancel_button = QPushButton("Cancel")
        self.ok_button = QPushButton("Change ID")
        self.ok_button.setDefault(True)
        
        # Style buttons
        for btn in [self.cancel_button, self.ok_button]:
            btn.setFixedHeight(35)
            btn.setMinimumWidth(90)
        
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db; color: white; border: none;
                border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:pressed { background-color: #21618c; }
        """)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        layout.addLayout(button_layout)
        
        # Set focus to input
        self.text_id.setFocus()

    def _connect_signals(self):
        """
        Connect UI signals.
        """
        self.text_id.returnPressed.connect(self._validate_and_apply)
        self.ok_button.clicked.connect(self._validate_and_apply)
        self.cancel_button.clicked.connect(self._cancel)
    
    def _validate_and_apply(self):
        """
        Validate input and apply ID change.
        """
        new_id_text = self.text_id.text().strip()
        
        if not new_id_text:
            self._show_validation_error("Please enter an ID.")
            return
            
        try:
            new_id = int(new_id_text)
        except ValueError:
            self._show_validation_error("Please enter a valid number.")
            return
        
        if new_id < 0:
            self._show_validation_error("ID must be a positive number.")
            return
        
        # Check for duplicate IDs
        existing_ids = set(self.shapes_layer.features['id'].values)
        if new_id in existing_ids and new_id != self.id_to_change:
            self._show_validation_error(f"ID {new_id} already exists. Please choose a different ID.")
            return
        
        # Apply the change
        self._apply_id_change(new_id)

    def _apply_id_change(self, new_id: int):
        """Apply the ID change."""
        try:
            # Update shapes layer features
            current_features = dict(self.shapes_layer.features)
            current_ids = current_features['id'].astype(int)
            current_ids[self.idx_selected_shape] = new_id
            current_features['id'] = current_ids
            self.shapes_layer.features = current_features
            
            # Update data manager
            fn = self.shapes_layer.name.split('bboxes_')[1]
            data = self.viz.manager.get_data()

            # Find the row(s) that match this shape
            mask = (data['filename'].str.contains(fn, na=False)) & \
                    (data['id'].astype(str) == str(self.id_to_change))
            idx_row = data[mask].index
            
            if len(idx_row) > 0:
                self.viz.manager.change_id(idx_row, new_id)
                logging.info(f"Updated {len(idx_row)} row(s) in data manager for ID change.")
            else:
                logging.warning(f"No matching row found in data manager for ID {self.id_to_change} and filename {fn}.")
            
            # Update next new ID if necessary
            if new_id >= self.viz.next_new_id:
                self.viz.change_next_new_id(new_id + 1)
            
            # Emit signal and close
            self.id_changed.emit(self.id_to_change, new_id)
            self.shapes_layer.mode = Mode.SELECT
            
            logger.info(f"Changed ID from {self.id_to_change} to {new_id}")
            self.accept()
            
        except Exception as e:
            logger.error(f"Error changing ID: {e}")
            self._show_validation_error(f"Error changing ID: {e}")
    
    def _show_validation_error(self, message: str):
        """Show validation error message."""
        QMessageBox.warning(self, "Invalid Input", message)
        self.text_id.setFocus()
        self.text_id.selectAll()

    def _cancel(self):
        """
        Cancel the dialog.
        """
        self.shapes_layer.mode = Mode.SELECT
        self.reject()

    def keyPressEvent(self, event):
        """Handle keyboard events."""
        if event.key() == Qt.Key_Escape:
            self._cancel()
        else:
            super().keyPressEvent(event)
