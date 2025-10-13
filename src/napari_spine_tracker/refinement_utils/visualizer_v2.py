# 1. Remove unused imports
import os
import numpy as np
from skimage import io
from qtpy.QtWidgets import QVBoxLayout, QSlider, QWidget, QLabel, QCheckBox
from qtpy.QtCore import Qt
from napari.layers.shapes._shapes_constants import Mode
from napari.components.viewer_model import ViewerModel
from superqt import QRangeSlider
from napari.utils.action_manager import action_manager
from napari_spine_tracker.refinement_utils.id_changer import IdChanger

# Remove matplotlib import and optimize color generation
COLORS = [(i/20, (i*7)%20/20, (i*13)%20/20) for i in range(20)]  # Generate colors without matplotlib

class FrameReader(QWidget):
    def __init__(self, viz, viewer_model: ViewerModel, img_dir: str, filenames: list, tp_name: str):
        super().__init__()  
        self.tp_name = tp_name
        self.viz = viz
        self.viewer_model = viewer_model
        self.img_dir = img_dir
        self.filenames = filenames
        self.text_params = None
        self.img = None
        self._old_frame = None
        self.frame_num = 0
        self.shapes_layer = None
        
        # Cache frequently used values
        self._total_frames = len(self.filenames)
        
        self._prepare_reader()
        self._setup_shortcuts()
        self.extract_data_to_draw()

    def _setup_shortcuts(self):
        """Separate method for cleaner organization"""
        shortcuts_to_unbind = [
            'napari:activate_add_line_mode', 'napari:increment_dims_right',
            'napari:increment_dims_left', 'napari:delete_selected_points',
            'napari:activate_add_rectangle_mode', 'napari:activate_add_ellipse_mode',
            'napari:activate_add_path_mode', 'napari:activate_add_polygon_mode',
            'napari:delete_selected_shapes', 'napari:activate_labels_picker_mode'
        ]
        for shortcut in shortcuts_to_unbind:
            action_manager.unbind_shortcut(shortcut)

        # Bind keys
        key_bindings = {
            'Backspace': self._delete_shape,
            'Delete': self._delete_shape,
            'S': self._change_selection_mode_status,
            'Escape': self._cancel_action,
            'Left': self._decrease_frame,
            'Right': self._increase_frame,
            'R': self._add_bbox
        }
        
        for key, method in key_bindings.items():
            if key in ['Left', 'Right', 'R']:
                self.viewer_model.bind_key(key, method, overwrite=True)
            else:
                self.viewer_model.bind_key(key, method)

    def _load_image(self, frame_num):
        """Optimize image loading"""
        filepath = os.path.join(self.img_dir, self.filenames[frame_num])
        self.img = io.imread(filepath)
        self.img_height, self.img_width = self.img.shape[:2]
        
        # More efficient max value calculation
        max_val = self.img.max()
        self.max_val_bin_len = max_val.bit_length()

    def extract_data_to_draw(self):
        """Optimize data extraction"""
        data = self.viz.manager.get_data()
        current_filename = self.filenames[self.frame_num]
        
        # Use vectorized operations where possible
        self.objs = data[data['filename'].str.contains(current_filename)]
        self.viz.change_next_new_id(data['id'].max() + 1)
        
        if len(self.objs) == 0:
            self.ids = []
            self.coords = []
            self.colors = []
            return
            
        self.ids = self.objs['id'].astype(str).tolist()
        
        # Vectorized coordinate calculation
        bbox_data = self.objs[['ymin', 'xmin', 'ymax', 'xmax']].values
        self.coords = [
            [[ymin, xmin], [ymin, xmax], [ymax, xmax], [ymax, xmin]]
            for ymin, xmin, ymax, xmax in bbox_data
        ]
        
        # Optimize color assignment
        if self.tp_name is not None:
            tp_mask = data['filename'].str.contains(self.tp_name)
            ids_this_tp = set(data[tp_mask]['id'].values)
            ids_other_tp = set(data[~tp_mask]['id'].values)
            ids_both_tps = ids_this_tp.intersection(ids_other_tp)
            
            self.colors = [
                COLORS[int(id_val) % 20] if int(id_val) in ids_both_tps else (1, 0, 1)
                for id_val in self.ids
            ]
        else:
            self.colors = [COLORS[int(id_val) % 20] for id_val in self.ids]

    def set_frame(self, frame):
        """Optimize frame setting"""
        if frame == self.frame_num:  # Early return if same frame
            return
            
        self._old_frame = self.frame_num

        # Only update coordinates if shapes layer exists and has been modified
        if self.shapes_layer is not None:
            self._update_coords()
            self.viewer_model.layers.remove(self.shapes_layer)
            self.shapes_layer = None
        
        # Remove old layer
        if self.filenames[self.frame_num] in self.viewer_model.layers:
            self.viewer_model.layers.remove(self.filenames[self.frame_num])
        
        # Load new image
        self._load_image(frame)
        self.viewer_model.add_image(self.img, name=self.filenames[frame])
        
        # Update UI elements
        self.frame_slider.setValue(frame)
        filename_display = os.path.basename(self.filenames[frame])
        self.frame_text.setText(
            f'Frame number: {frame+1} | Total frames: {self._total_frames}\n {filename_display}'
        )
        self.frame_num = frame
        
        # Extract data and show boxes in one go
        # self.remove_bboxes()
        self.extract_data_to_draw()
        if self.show_bboxes_checkbox.isChecked():
            self.show_bboxes_in_frame()
        # self.show_bboxes_in_frame()
        
        self._set_contrast_limits(self.contrast_range_slider.value())

    def _prepare_reader(self):
        """Initialize UI components"""
        self._load_image(self.frame_num)
        self.viewer_model.add_image(self.img, name=self.filenames[self.frame_num])

        # Create UI components
        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.setRange(0, self._total_frames - 1)
        self.frame_slider.setValue(self.frame_num)
        self.frame_slider.valueChanged.connect(self.set_frame)

        self.frame_text = QLabel(f'Frame number: {self.frame_num+1} | Total frames: {self._total_frames}')
        self.frame_text.setAlignment(Qt.AlignCenter)

        self.show_bboxes_checkbox = QCheckBox('Show Bounding Boxes')
        self.show_bboxes_checkbox.stateChanged.connect(self.show_bboxes_in_frame)

        self.contrast_range_slider = QRangeSlider(Qt.Orientation.Horizontal, self)
        self.contrast_range_slider.valueChanged.connect(self._set_contrast_limits)

        # Set contrast limits
        max_contrast = 2**self.max_val_bin_len
        self.contrast_range_slider.setRange(0, max_contrast)
        self.contrast_range_slider.setValue([0, max_contrast])

        # Layout setup
        layout = QVBoxLayout()
        widgets = [self.frame_text, self.frame_slider, self.show_bboxes_checkbox, self.contrast_range_slider]
        for widget in widgets:
            layout.addWidget(widget)
        layout.addStretch(1)
        self.setLayout(layout)

    def show_bboxes_in_frame(self):
        """Optimize bbox display"""
        if not self.show_bboxes_checkbox.isChecked():
            self.remove_bboxes()
            return
            
        if len(self.objs) == 0:
            return

        layer_name = f'bboxes_{self.filenames[self.frame_num]}'
        
        # Create shapes layer with optimized parameters
        self.shapes_layer = self.viewer_model.add_shapes(
            self.coords,
            shape_type='rectangle',
            edge_color=np.array(self.colors),
            face_color='transparent',
            name=layer_name,
            visible=True,
            text=self.text_params,
            features={'id': self.ids},
        )

        if hasattr(self.viz, 'selection_mode') and self.viz.selection_mode.isChecked():
            self.shapes_layer.mode = Mode.SELECT