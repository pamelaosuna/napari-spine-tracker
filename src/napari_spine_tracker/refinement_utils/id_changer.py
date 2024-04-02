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
from qtpy.QtGui import QIntValidator

from napari.layers import Shapes
from napari.layers.shapes._shapes_constants import Mode
from napari.components.viewer_model import ViewerModel

class IdChanger(QDialog):
    def __init__(self,
                 viz,
                 parent:QWidget, 
                 viewer_model: ViewerModel, 
                 shapes_layer: Shapes):
        super().__init__(parent)
        self.viz = viz
        self.viewer_model = viewer_model
        self.shapes_layer = shapes_layer
        if len(self.shapes_layer.selected_data) == 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please select one rectangle")
            self.close()
            msg.exec_()
        self.idx_selected_shape = list(self.shapes_layer.selected_data)[-1]
        self.id_to_change = self.shapes_layer.features['id'].values[self.idx_selected_shape]
        self.setWindowTitle("Change ID")
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(200, 100)
        
        self._prepare_dialog()

    def _prepare_dialog(self):
        main_layout = QVBoxLayout(self)
        self.text_id = QLineEdit()
        self.text_id.setPlaceholderText("Enter new ID")
        self.text_id.setValidator(QIntValidator())
        self.text_id.setFocus()
        self.text_id.returnPressed.connect(self._check_valid_id)

        # add info about next new id
        self.info_next_new_id = QLabel(f'Next new ID: {self.viz.next_new_id}')
        self.info_next_new_id.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.info_next_new_id)

        # use Esc to cancel
        # self.text_id.keyPressEvent = lambda event: self.close() if event.key() == Qt.Key_Escape else None
        main_layout.addWidget(self.text_id)
        self.setLayout(main_layout)
    
    def _check_valid_id(self):
        # invalid_id = True
        new_id = self.text_id.text()
        ids = self.shapes_layer.features['id'].values
        if new_id in ids:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("ID already exists")
            msg.exec_()
            self.text_id.clear()
            self.text_id.setFocus()
        elif new_id != '':
            # invalid_id = False
            self.shapes_layer.mode = Mode.SELECT
            self._close_dialog(new_id)

    def _close_dialog(self, new_id):
            fn = self.shapes_layer.name.split('bboxes_')[1]
            data = self.viz.manager.get_data()
            idx_row = data[
                (data['filename'].str.contains(fn)) &
                (data['id'].astype(str) == str(self.id_to_change))
            ].index
            self.viz.manager.change_id(idx_row, int(new_id))
            self.shapes_layer.mode = Mode.SELECT
            self.close()
