import os
import numpy as np
from skimage import io
from qtpy.QtWidgets import QVBoxLayout
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QSlider,
    QWidget,
    QLabel,
    QCheckBox,
    QVBoxLayout,
    )

from napari.layers.shapes._shapes_constants import Mode
from napari.components.viewer_model import ViewerModel
from superqt import QRangeSlider
from napari.utils.action_manager import action_manager
from napari_spine_tracker.refinement_utils.id_changer import IdChanger

import matplotlib.pyplot as plt

# use cmap from matplotlib
cmap = plt.cm.get_cmap('tab20')
# convert to rbg
COLORS = [cmap(i)[:3] for i in range(20)]

class FrameReader(QWidget):
    """
    Manages the direct interaction with the rendered frames and the bounding boxes
    """
    def __init__(self, 
                 viz, 
                 viewer_model: ViewerModel, 
                 img_dir: str, 
                 filenames: list, 
                 tp_name: str):
        super().__init__()  
        self.tp_name = tp_name
        self.viz = viz
        self.viewer_model = viewer_model
        self.img_dir = img_dir
        self.filenames = filenames
        self.text_params = None

        self._prepare_reader()

        shortcuts_to_unbind= ['napari:activate_add_line_mode',
                                'napari:increment_dims_right',
                                'napari:increment_dims_left',
                                'napari:delete_selected_points',
                                'napari:activate_add_rectangle_mode',
                                'napari:activate_add_ellipse_mode',
                                'napari:activate_add_path_mode',
                                'napari:activate_add_polygon_mode',
                                'napari:delete_selected_shapes',
                                'napari:activate_add_path_mode',
                                'napari:activate_labels_picker_mode',
                                'napari:activate_add_line_mode',
                                # 'napari:activate_points_select_mode',
                                # 'napari:activate_select_mode',
        ]
        for s in shortcuts_to_unbind:
            action_manager.unbind_shortcut(s)

        # key bindings
        self.viewer_model.bind_key('Backspace', self._delete_shape)
        self.viewer_model.bind_key('Delete', self._delete_shape)
        self.viewer_model.bind_key('S', self._change_selection_mode_status)
        self.viewer_model.bind_key('Escape', self._cancel_action)

        @self.viewer_model.bind_key('Left', overwrite=True)
        def _decrease_frame(event):
            self._decrease_frame(event)
        
        @self.viewer_model.bind_key('Right', overwrite=True)
        def _increase_frame(event):
            self._increase_frame(event)

        @self.viewer_model.bind_key('R', overwrite=True)
        def _add_bbox(event):
            self._add_bbox(event)

        # bbox data
        self.extract_data_to_draw()
        self.shapes_layer = None

    def _prepare_reader(self):
        init_frame_val = 0

        self._old_frame = None
        self.frame_num = init_frame_val

        self._load_images()
        self.viewer_model.add_image(self.imgs[init_frame_val], 
                                    name=self.filenames[init_frame_val])

        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.setRange(0, len(self.filenames)-1)
        self.frame_slider.setValue(init_frame_val)
        self.frame_slider.valueChanged.connect(self.set_frame)

        self.frame_text = QLabel(f'Frame number: {self.frame_num+1} | Total frames: {len(self.filenames)}')
        self.frame_text.setAlignment(Qt.AlignCenter)
        # self.fname_text = QLabel(self.filenames[self.frame_num])
        # self.fname_text.setAlignment(Qt.AlignLeft)
        # self.fname_text.setStyleSheet("font: 10pt")

        self.show_bboxes_checkbox = QCheckBox('Show Bounding Boxes')
        self.show_bboxes_checkbox.stateChanged.connect(self.show_bboxes_in_frame)

        self.contrast_range_slider = QRangeSlider(Qt.Orientation.Horizontal, self)
        self.contrast_range_slider.valueChanged.connect(self._set_contrast_limits)

        # set contrast limits to be 0 and 2^max_val_bin_len
        self.contrast_range_slider.setRange(0, 2**self.max_val_bin_len)
        self.contrast_range_slider.setValue([0, 2**self.max_val_bin_len])

        layout = QVBoxLayout()
        for w in [self.frame_text, self.frame_slider, self.show_bboxes_checkbox, self.contrast_range_slider]: # self.fname_text, 
            layout.addWidget(w)
        layout.addStretch(1)
        self.setLayout(layout)

    def set_frame(self, frame):
        self._old_frame = self.frame_num
        # TODO: before updating data, check that no id is repeated, and if so, ask the user to change it
        self.viewer_model.layers.remove(self.filenames[self.frame_num])
        self.viewer_model.add_image(self.imgs[frame], name=self.filenames[frame])
        self.frame_slider.setValue(frame)
        self.frame_text.setText(f'Frame number: {frame+1} | Total frames: {len(self.filenames)}')
        self.frame_num = frame
        # use drawn coordinates to update data in case user has changed them
        # self._update_coords()
        self.remove_bboxes()
        self.extract_data_to_draw()
        self.show_bboxes_in_frame()
        self._set_contrast_limits(self.contrast_range_slider.value())

    def _load_images(self):
        # print(f'Adding {len(self.filenames)} images to viewer')
        imgs = []
        for fn in self.filenames:
            img = io.imread(os.path.join(self.img_dir, fn))
            imgs.append(img)

        self.imgs = np.array(imgs)
        max_val = np.max(imgs)
        max_val_bin = bin(max_val)[2:]
        self.max_val_bin_len = len(max_val_bin)
    
    def extract_data_to_draw(self):
        data = self.viz.manager.get_data()
        self.objs = data[data['filename'].str.contains(self.filenames[self.frame_num])]
        self.viz.change_next_new_id(data['id'].max() + 1)
        self.ids = [str(id) for id in self.objs['id'].values]
        self.coords = [
                [[ymin, xmin], [ymin, xmax], [ymax, xmax], [ymax, xmin]] 
                      for ymin, xmin, ymax, xmax in self.objs[['ymin', 'xmin', 'ymax', 'xmax']].values
                      ]
        if self.tp_name is not None:
            self.ids_this_tp = np.unique(data[data['filename'].str.contains(self.tp_name)]['id'].values)
            self.ids_other_tp = np.unique(data[~data['filename'].str.contains(self.tp_name)]['id'].values)
            self.ids_both_tps = np.intersect1d(self.ids_this_tp, self.ids_other_tp)
            self.colors = [COLORS[int(id)%20] if int(id) in self.ids_both_tps else (1, 0, 1) for id in self.ids]
        else:
            self.ids_both_tps = []
            self.colors = [COLORS[int(id)%20] for id in self.ids]

    def repaint_bboxes(self):
        if self.shapes_layer is not None:
            self.viewer_model.layers.remove(self.shapes_layer)
            self.shapes_layer = None
        self.show_bboxes_in_frame()

    def _set_contrast_limits(self, values):
        cmin, cmax = values
        self.viewer_model.layers[self.filenames[self.frame_num]].contrast_limits = (cmin, cmax)

    def remove_bboxes(self):
        if self.shapes_layer is not None:
            self._update_coords()
            self.viewer_model.layers.remove(self.shapes_layer)
            self.shapes_layer = None

    def show_bboxes_in_frame(self):
        if not self.show_bboxes_checkbox.isChecked():
            self.remove_bboxes()
            return
        elif len(self.objs) == 0:
            # print('No objects in this frame')
            return
        else:
            layer_name = 'bboxes_' + self.filenames[self.frame_num]
            self.viewer_model.add_shapes(self.coords,
                                        shape_type='rectangle',
                                        edge_color=np.array(self.colors),
                                        face_color='transparent',
                                        name=layer_name,
                                        visible=True,
                                        text=self.text_params,
                                        features={'id': self.ids},
                                        )
            self.shapes_layer = self.viewer_model.layers[layer_name]

            if self.viz.selection_mode.isChecked():
                self.shapes_layer.mode = Mode.SELECT
    
    def _add_bbox(self, event):
        if self.shapes_layer is not None and self.shapes_layer.mode == Mode.ADD_RECTANGLE:
            self.shapes_layer.mode = Mode.SELECT
            return
        
        if not self.show_bboxes_checkbox.isChecked():
            self.show_bboxes_checkbox.setChecked(True)
        if not self.viz.selection_mode.isChecked():
            self.viz.selection_mode.setChecked(True)
        
        # activate add rectangle mode
        self._update_coords()
        layer_name = 'bboxes_' + self.filenames[self.frame_num]
        if self.shapes_layer is None:
            self.shapes_layer = self.viewer_model.add_shapes(name=layer_name,
                                                             shape_type='rectangle',
                                                             features={'id':[]},
                                                             edge_color='green',
                                                             face_color='transparent',
                                                             visible=True,
                                                             text=self.text_params)
        self.shapes_layer.mode = Mode.ADD_RECTANGLE
        
        @self.shapes_layer.mouse_drag_callbacks.append
        def click_drag(layer, event):
            # print('mouse down')
            dragged = False
            yield
            # on move
            while event.type == 'mouse_move':
                dragged = True
                yield
            # on release
            if dragged:
                self.shapes_layer.mode = Mode.SELECT
                self.shapes_layer.selected_data = [len(self.shapes_layer.data) - 1]
                data = self.viz.manager.get_data()
                self.shapes_layer.features['id'][len(self.shapes_layer.data) - 1] = data['id'].max() + 1
                ymin, xmin = np.array(self.shapes_layer.data[-1]).min(axis=0)
                ymax, xmax = np.array(self.shapes_layer.data[-1]).max(axis=0)
                new_row = {'xmin': xmin,
                           'ymin': ymin, 
                           'xmax': xmax, 
                           'ymax': ymax, 
                           'id': data['id'].max() + 1,
                           'filename': self.filenames[self.frame_num], 
                           'score': 1,
                           'class': 'spine', 
                           'width': 512, 
                           'height': 512,
                           }
                self.viz.manager.add_new_tracklet(new_row)
                if not self.show_bboxes_checkbox.isChecked():
                    return
                self._update_coords()
                self.extract_data_to_draw()
                self.repaint_bboxes()

    def _delete_shape(self, event):
        if not self.show_bboxes_checkbox.isChecked():
            return
        
        if len(list(self.shapes_layer.selected_data)) == 0: # TODO: what happens if selected more than one shape?
            print("No rectangle selected")
            return
        
        self._update_coords()
        fn = self.shapes_layer.name.split('bboxes_')[1]
        ids_to_remove = self.shapes_layer.features['id'].values[list(self.shapes_layer.selected_data)].astype(str)
        data = self.viz.manager.get_data()
        idxs_rows = data[
                (data['filename'].str.contains(fn)) &
                (data['id'].astype(str).isin(ids_to_remove))
            ].index
        self.viz.manager.remove_tracklet(idxs_rows)

        self.extract_data_to_draw()
        self.repaint_bboxes()
    
    def _update_coords(self):
        if self.shapes_layer is not None:
            self.viz.manager.update_coords(self.shapes_layer.name,
                                            self.shapes_layer.data, 
                                            self.shapes_layer.features['id'].values)
            self.extract_data_to_draw()
    
    def _decrease_frame(self, event):
        if self.frame_num > 0:
            self.frame_slider.setValue(self.frame_num - 1)
    
    def _increase_frame(self, event):
        if self.frame_num < len(self.filenames) - 1:
            self.frame_slider.setValue(self.frame_num + 1)
    
    def get_shapes_layer_name(self):
        if self.shapes_layer is None:
            return None
        return self.shapes_layer.name
    
    def _cancel_action(self, event):
        if self.id_changer is not None:
            self.id_changer.close()
            self.id_changer = None
        elif self.shapes_layer is not None and self.shapes_layer.mode == Mode.ADD_RECTANGLE:
            self.shapes_layer.mode = Mode.SELECT
        
    def _change_selection_mode_status(self, event):
        if self.shapes_layer is not None:
            self.viz.selection_mode.setChecked(not self.viz.selection_mode.isChecked())
class FrameReaderWithIDs(FrameReader):
    
    def __init__(self, viz, viewer_model: ViewerModel, img_dir: str, filenames: list, tp_name: str):
        super().__init__(viz, viewer_model, img_dir, filenames, tp_name)
        self.viewer_model.bind_key('i', self._change_id_on_dialog)
        self.id_changer = None
        self.text_params =   {
                'string': 'id',
                'size': 10,
                'color': 'blue', # 'red', 
                'anchor': 'upper_left',
                'translation': [-1, 1],
                }

    def _change_id_on_dialog(self, event):
        if not self.show_bboxes_checkbox.isChecked():
            return
        if not 'nan' in self.shapes_layer.features['id'].values:
            self._update_coords()
        self.id_changer = IdChanger(self.viz, 
                                     self.viz.root_widget, 
                                     self.viewer_model,
                                     self.shapes_layer)
        self.id_changer.exec_()
        self.id_changer = None
        # self._update_coords()
        self.extract_data_to_draw()
        self.repaint_bboxes()
    
    def _add_bbox(self, event):
        if self.shapes_layer is not None and self.shapes_layer.mode == Mode.ADD_RECTANGLE:
            self.shapes_layer.mode = Mode.SELECT
            return
        
        if not self.show_bboxes_checkbox.isChecked():
            self.show_bboxes_checkbox.setChecked(True)
        if not self.viz.selection_mode.isChecked():
            self.viz.selection_mode.setChecked(True)
        
        # activate add rectangle mode
        self._update_coords()
        layer_name = 'bboxes_' + self.filenames[self.frame_num]
        if self.shapes_layer is None:
            self.shapes_layer = self.viewer_model.add_shapes(name=layer_name,
                                                             shape_type='rectangle',
                                                             features={'id':[]},
                                                             edge_color='green',
                                                             face_color='transparent',
                                                             visible=True,
                                                             text=self.text_params)
        self.shapes_layer.mode = Mode.ADD_RECTANGLE
        
        @self.shapes_layer.mouse_drag_callbacks.append
        def click_drag(layer, event):
            # print('mouse down')
            dragged = False
            yield
            # on move
            while event.type == 'mouse_move':
                dragged = True
                yield
            # on release
            if dragged:
                self.shapes_layer.mode = Mode.SELECT
                self.shapes_layer.selected_data = [len(self.shapes_layer.data) - 1]
                self.shapes_layer.features['id'][len(self.shapes_layer.data) - 1] = 'nan'
                ymin, xmin = np.array(self.shapes_layer.data[-1]).min(axis=0)
                ymax, xmax = np.array(self.shapes_layer.data[-1]).max(axis=0)
                new_row = {'xmin': xmin,
                           'ymin': ymin, 
                           'xmax': xmax, 
                           'ymax': ymax, 
                           'id': 'nan',
                           'filename': self.filenames[self.frame_num], 
                           'score': 1,
                           'class': 'spine', 
                           'width': 512, 
                           'height': 512,
                           }
                self.viz.manager.add_new_tracklet(new_row)
                self._change_id_on_dialog(event=None)
    