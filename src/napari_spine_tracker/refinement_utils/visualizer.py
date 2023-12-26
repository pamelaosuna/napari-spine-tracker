import os, glob
import numpy as np
from skimage import io
from qtpy.QtWidgets import QSplitter, QVBoxLayout, QHBoxLayout
from qtpy.QtWidgets import QSplitter, QTabWidget
from qtpy.QtCore import Qt, QEvent, QObject, QItemSelection
from qtpy.QtWidgets import (
    QPushButton,
    QSlider,
    QWidget,
    QLabel,
    QCheckBox,
    QDialog,
    QLineEdit,
    QMessageBox,
    )
from qtpy.QtGui import QIcon, QIntValidator


from napari.layers import Image, Shapes
from napari.layers.shapes._shapes_constants import Mode
from napari.components.viewer_model import ViewerModel
from napari_spine_tracker.tabs.multi_view  import  QtViewerWrap
from superqt import QRangeSlider
from napari.utils.action_manager import action_manager

import pandas as pd

class FrameReader(QWidget):
    """
    Dummy widget showcasing how to place additional widgets to the right
    of the additional viewers. # TODO: rewrite
    """
    def __init__(self, viz, viewer_model, img_dir, filenames, tp_name):
        super().__init__()
        self.tp_name = tp_name
        self.viz = viz
        self.viewer_model = viewer_model
        self.img_dir = img_dir
        self.filenames = filenames

        # self.synchronize = False
        self._prepare_reader()

        action_manager.unbind_shortcut('napari:activate_add_line_mode')
        action_manager.unbind_shortcut('napari:increment_dims_right')
        action_manager.unbind_shortcut('napari:increment_dims_left')
        action_manager.unbind_shortcut('napari:delete_selected_points')

        # # bind key press 'i' to _change_id()
        self.viewer_model.bind_key('i', self._change_id_on_dialog)
        self.viewer_model.bind_key('Backspace', self._delete_shape)
        self.viewer_model.bind_key('Delete', self._delete_shape)

        @self.viewer_model.bind_key('Left', overwrite=True)
        def _decrease_frame(event):
            self._decrease_frame(event)
        
        # action_manager.register_action(
        #     name='napari:_increase_frame',
        #     command=self._increase_frame,
        #     description='Go to next frame',
        #     keymapprovider=ViewerModel,
        # )
        # action_manager.bind_shortcut('napari:_increase_frame', 'Right')

        @self.viewer_model.bind_key('Right', overwrite=True)
        def _increase_frame(event):
            self._increase_frame(event)

    def _prepare_reader(self):
        init_frame_val = 0

        self._old_frame = None
        self.frame_num = init_frame_val

        self._load_images()
        self.viewer_model.add_image(self.imgs[init_frame_val], name=self.filenames[init_frame_val])

        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.setMinimum(0)
        self.frame_slider.setMaximum(len(self.filenames)-1)
        self.frame_slider.setValue(init_frame_val)
        self.frame_slider.valueChanged.connect(self.set_frame)

        self.frame_text = QLabel(f'Frame number: {self.frame_num+1} | Total frames: {len(self.filenames)}')
        self.frame_text.setAlignment(Qt.AlignCenter)
        self.fname_text = QLabel(self.filenames[self.frame_num])
        self.fname_text.setAlignment(Qt.AlignLeft)
        self.fname_text.setStyleSheet("font: 10pt")

        self.show_bboxes_checkbox = QCheckBox('Show Bounding Boxes')
        self.show_bboxes_checkbox.stateChanged.connect(self.show_bboxes_in_frame)

        self.contrast_range_slider = QRangeSlider(Qt.Orientation.Horizontal, self)
        self.contrast_range_slider.valueChanged.connect(self._set_contrast_limits)

        # set contrast limits to be 0 and 2^max_val_bin_len
        self.contrast_range_slider.setRange(0, 2**self.max_val_bin_len)
        self.contrast_range_slider.setValue([0, 2**self.max_val_bin_len])

        layout = QVBoxLayout()
        for w in [self.fname_text, self.frame_text, self.frame_slider, self.show_bboxes_checkbox, self.contrast_range_slider]:
            layout.addWidget(w)
        layout.addStretch(1)
        self.setLayout(layout)

    def set_frame(self, frame):
        self._old_frame = self.frame_num
        self.viz.update_data(self.viewer_model.layers)
        self.viewer_model.layers.remove(self.filenames[self.frame_num])
        self.viewer_model.add_image(self.imgs[frame], name=self.filenames[frame])
        self.frame_slider.setValue(frame)
        self.frame_text.setText(f'Frame number: {frame+1} | Total frames: {len(self.filenames)}')
        # self.fname_text.setText(self.filenames[frame])
        self.frame_num = frame
        self.remove_bboxes()
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

    # def update_synchronize(self):
    #     self.synchronize = not(self.synchronize)

    def _set_contrast_limits(self, values):
        cmin, cmax = values
        self.viewer_model.layers[self.filenames[self.frame_num]].contrast_limits = (cmin, cmax)

    def remove_bboxes(self):
        layers_to_remove = [layer for layer in self.viewer_model.layers if 'bboxes_' in layer.name]
        for layer_name in layers_to_remove:
            self.viewer_model.layers.remove(layer_name)

    def show_bboxes_in_frame(self):
        if not self.show_bboxes_checkbox.isChecked():
            self.viz.update_data(self.viewer_model.layers)
            self.remove_bboxes()
        else:
            objs = self.viz.data[self.viz.data['filename'].str.contains(self.filenames[self.frame_num])]
            if len(objs) == 0:
                return
            text_params = {
                    'string': 'id',
                    'size': 8,
                    'color': 'yellow',
                    'anchor': 'upper_left',
                    'translation': [-1, 1],
                }
            shapes = [[[ymin, xmin], [ymin, xmax], [ymax, xmax], [ymax, xmin]] for ymin, xmin, ymax, xmax in objs[['ymin', 'xmin', 'ymax', 'xmax']].values] 
            ids = [str(id) for id in objs['id'].values]
            # if the intersection of 
            filenames_per_id = [np.unique([os.path.basename(f) for f in self.viz.data[self.viz.data['id']==int(curr_id)]['filename'].values])  
                              for curr_id in ids]
            id_in_both_tps = [list(np.unique([f.split('tp')[1][0] for f in fid])) for fid in filenames_per_id]
            colors = ['yellow' if len(id) == 2 else 'green' for id in id_in_both_tps]
            feats = {'id': ids, 'init_id': ids}
            self.viewer_model.add_shapes(shapes,
                                        shape_type='rectangle',
                                        edge_color=np.array(colors),
                                        face_color='transparent',
                                        name='bboxes_' + self.filenames[self.frame_num],
                                        visible=True,
                                        text=text_params,
                                        features=feats,
                                        )
            shapes_layer = self.viewer_model.layers['bboxes_' + self.filenames[self.frame_num]]
            
            if self.viz.selection_mode.isChecked():
                shapes_layer.mode = Mode.SELECT
                
    def _change_id_on_dialog(self, event):
        if not self.show_bboxes_checkbox.isChecked():
            return
        shapes_layer = self.viewer_model.layers['bboxes_' + self.filenames[self.frame_num]]
        change_id_dialog = IdChanger(self.viz.root_widget, self.viewer_model,
                                     shapes_layer)
        change_id_dialog.show()
    
    # def _update_shapes_layer(self):

    def delete_row_from_data(self, idx):
        self.viz.data.drop(idx, inplace=True)

    def _delete_shape(self, event):
        # if no shape is selected, do nothing
        if not self.show_bboxes_checkbox.isChecked():
            return
        layer_name = 'bboxes_' + self.filenames[self.frame_num]
        shapes_layer = self.viewer_model.layers[layer_name]
        self.idx_selected_shape = [s for s in shapes_layer.selected_data]
        if len(self.idx_selected_shape) != 1:
            print("No rectangle selected")
            return
        self.idx_selected_shape = self.idx_selected_shape[0]
        # remove shape from layer
        # shapes_layer.data.pop(self.idx_selected_shape)
        # shapes_layer.selected_data = []
        # remove shape from data
        id_to_remove = shapes_layer.features['id'].values[self.idx_selected_shape]
            
        text_params = {
            'string': 'id',
            'size': 8,
            'color': 'yellow',
            'anchor': 'upper_left',
            'translation': [-1, 1],
        }
        ymins, xmins = np.array(shapes_layer.data).min(axis=1).T
        ymaxs, xmaxs = np.array(shapes_layer.data).max(axis=1).T
        rects = [[[ymin, xmin], [ymin, xmax], [ymax, xmax], [ymax, xmin]] for ymin, xmin, ymax, xmax in zip(ymins, xmins, ymaxs, xmaxs)]
        rects.pop(self.idx_selected_shape)
        ids = list(shapes_layer.features['id'].values)
        init_ids = list(shapes_layer.features['init_id'].values)
        colors = list(shapes_layer.edge_color)
        ids.pop(self.idx_selected_shape)
        init_ids.pop(self.idx_selected_shape)
        colors.pop(self.idx_selected_shape)

        feats = {'id': ids, 'init_id': init_ids}
        self.viewer_model.layers.remove(layer_name)
        if len(ids) > 0:
            self.viewer_model.add_shapes(rects,
                        shape_type='rectangle',
                        edge_color=colors,
                        face_color='transparent',
                        name=layer_name,
                        visible=True,
                        text=text_params,
                        features=feats,
                        )
            self.viewer_model.layers[layer_name].mode = Mode.SELECT

        idx = self.viz.data[((self.viz.data['filename'].str.contains(self.filenames[self.frame_num])) & (self.viz.data['id'] == int(id_to_remove)))].index
        # print(f'deleting row {idx} from data')
        self.delete_row_from_data(idx)
    
    def _decrease_frame(self, event):
        if self.frame_num > 0:
            # change value of frame slider
            self.frame_slider.setValue(self.frame_num - 1)
            # self.set_frame(self.frame_num - 1)
    
    def _increase_frame(self, event):
        if self.frame_num < len(self.filenames) - 1:
            self.frame_slider.setValue(self.frame_num + 1)
            
class IdChanger(QDialog):
    def __init__(self, parent:QWidget, viewer_model, shapes_layer):
        super().__init__(parent)
        self.viewer_model = viewer_model
        self.idx_selected_shape = [s for s in shapes_layer.selected_data]
        if len(self.idx_selected_shape) != 1:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please select one rectangle")
            self.close()
            msg.exec_()
        self.idx_selected_shape = self.idx_selected_shape[0]
        self.layer_name = shapes_layer.name
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
        self.text_id.returnPressed.connect(self._close_dialog)
        # use Esc to cancel
        # self.text_id.keyPressEvent = lambda event: self.close() if event.key() == Qt.Key_Escape else None
        main_layout.addWidget(self.text_id)
        self.setLayout(main_layout)

    def _close_dialog(self):
        if self.text_id.text() != '':
            new_id = self.text_id.text()
            shapes_layer = self.viewer_model.layers[self.layer_name]
            
            text_params = {
                'string': 'id',
                'size': 8,
                'color': 'yellow',
                'anchor': 'upper_left',
                'translation': [-1, 1],
            }
            ymins, xmins = np.array(shapes_layer.data).min(axis=1).T
            ymaxs, xmaxs = np.array(shapes_layer.data).max(axis=1).T
            rects = [[[ymin, xmin], [ymin, xmax], [ymax, xmax], [ymax, xmin]] for ymin, xmin, ymax, xmax in zip(ymins, xmins, ymaxs, xmaxs)]
            ids = shapes_layer.features['id'].values
            ids[self.idx_selected_shape] = str(new_id)
            init_ids = shapes_layer.features['init_id'].values
            colors = shapes_layer.edge_color
            feats = {'id': ids, 'init_id': init_ids}
            self.viewer_model.layers.remove(self.layer_name)
            self.viewer_model.add_shapes(rects,
                        shape_type='rectangle',
                        edge_color=colors,
                        face_color='transparent',
                        name=self.layer_name,
                        visible=True,
                        text=text_params,
                        features=feats,
                        )
            self.viewer_model.layers[self.layer_name].mode = Mode.SELECT
            # print(f'Changing ID to {new_id}')
            self.close()
            
class TrackletVisualizer:
    def __init__(self, 
                 root_plugin_widget, 
                 manager, 
                 img_dir,
                 filter_t1='_tp1_', #None,
                 filter_t2='_tp2_' # None
                 ):
        # print("TrackletVisualizer created")
        self.root_widget = root_plugin_widget
        self.img_dir = img_dir
        self.manager = manager
        
        # self.synchronize = False # synchronize frame slider across viewers

        self.unq_filenames = manager.unq_filenames
        self.data = manager.data

        self.stack_names = np.unique([f.split('_layer')[0] for f in self.unq_filenames])
        all_filenames = []
        for sn in self.stack_names:
            all_filenames += list(glob.glob(os.path.join(self.img_dir, f"{sn}_layer*.png")))
        self.all_filenames = sorted([os.path.basename(f) for f in all_filenames])
        self.filenames_t1 = [f for f in self.all_filenames if filter_t1 in f]
        self.filenames_t2 = [f for f in self.all_filenames if filter_t2 in f]

        if len(self.all_filenames) > 0:
            self.curr_stack = self.all_filenames[0].split('_layer')[0]
        else:
            print("No images found in the selected folder")
            return
        
        self._prepare_visualizer()

    def _prepare_visualizer(self):
        self.viewer_model1 = ViewerModel(title="model1")
        self.viewer_model2 = ViewerModel(title="model2")
        self.qt_viewer1 = QtViewerWrap(self.root_widget.viewer, self.viewer_model1)
        self.qt_viewer2 = QtViewerWrap(self.root_widget.viewer, self.viewer_model2)
        self.frame_reader1 = FrameReader(self, self.viewer_model1, self.img_dir, self.filenames_t1, 'tp1')
        self.frame_reader2 = FrameReader(self, self.viewer_model2, self.img_dir, self.filenames_t2, 'tp2')
        
        toolbar_splitter = QSplitter()
        toolbar_splitter.setOrientation(Qt.Horizontal)
        toolbar_splitter.addWidget(self.frame_reader1)
        toolbar_splitter.addWidget(self.frame_reader2)
        toolbar_splitter.setContentsMargins(0, 0, 0, 0)
        
        viewer_splitter = QSplitter()
        viewer_splitter.setOrientation(Qt.Horizontal)
        viewer_splitter.addWidget(self.qt_viewer1)
        viewer_splitter.addWidget(self.qt_viewer2)
        viewer_splitter.setContentsMargins(0, 0, 0, 0)

        self.sync_checkbox = QCheckBox("Synchronize frame number")
        self.sync_checkbox.stateChanged.connect(self._toggle_synchronize)
        self.sync_checkbox.setChecked(False)

        self.selection_mode = QCheckBox("Selection mode")
        self.selection_mode.stateChanged.connect(self._toggle_selection_mode)
        self.selection_mode.setChecked(False)

        self.root_widget.layout.addWidget(viewer_splitter)
        self.root_widget.layout.setSpacing(0)

        h_layout = QHBoxLayout()
        h_layout.addStretch(1)
        for w in [self.sync_checkbox, self.selection_mode]:
            h_layout.addWidget(w, alignment=Qt.AlignCenter)
        h_layout.addStretch(1)
        self.root_widget.layout.addLayout(h_layout)
        # self.root_widget.layout.addWidget(self.sync_checkbox, alignment=Qt.AlignCenter)
        # self.root_widget.layout.addWidget(self.selection_mode, alignment=Qt.AlignCenter)
        self.root_widget.layout.addWidget(toolbar_splitter)
    
    def _toggle_synchronize(self, state):
        # self.synchronize = not(self.synchronize)
        # self.frame_reader1.update_synchronize()
        # self.frame_reader2.update_synchronize()
        if state == Qt.Checked:
            self.frame_reader1.frame_slider.valueChanged.connect(self.frame_reader2.set_frame)
            self.frame_reader2.frame_slider.valueChanged.connect(self.frame_reader1.set_frame)
        else:
            self.frame_reader1.frame_slider.valueChanged.disconnect(self.frame_reader2.set_frame)
            self.frame_reader2.frame_slider.valueChanged.disconnect(self.frame_reader1.set_frame)
    
    def _toggle_selection_mode(self, state):
        for vm, fr in zip([self.viewer_model1, self.viewer_model2], [self.frame_reader1, self.frame_reader2]):
            shapes_layer_name = [layer.name for layer in vm.layers if 'bboxes_' in layer.name]
            if fr.show_bboxes_checkbox.isChecked() and len(shapes_layer_name) > 0:
                shapes_layer_name = 'bboxes_' + fr.filenames[fr.frame_num]
                if state == Qt.Checked:            
                    vm.layers[shapes_layer_name].mode = Mode.SELECT
                else:
                    vm.layers[shapes_layer_name].mode = Mode.PAN_ZOOM

    def update_data(self, layers):
        all_shapes_layer = [layer for layer in layers if 'bboxes_' in layer.name]

        for shapes_layer in all_shapes_layer:
            ids = shapes_layer.features['id'].values.astype(int)
            ymins, xmins = np.array(shapes_layer.data).min(axis=1).T
            ymaxs, xmaxs = np.array(shapes_layer.data).max(axis=1).T
            filenames = [shapes_layer.name.split('bboxes_')[1]] * len(ids)
            score = [1] * len(ids)
            classes = ['spine'] * len(ids)
            width = [512] * len(ids)
            height = [512] * len(ids)

            cols = ['xmin', 'ymin', 'xmax', 'ymax', 
                    'id', 'filename', 'score', 'class',
                    'width', 'height']
            
            rows2drop = self.data[self.data['filename'].str.contains(filenames[0])]
            self.data.drop(rows2drop.index, inplace=True)

            vals = [xmins, ymins, xmaxs, ymaxs,
                    ids, filenames, score, classes,
                    width, height]
            
            new_data = dict(zip(cols, vals))
            new_data = pd.DataFrame(new_data)
            self.manager.data = pd.concat([self.data, new_data], ignore_index=True)
            self.data = self.manager.data

            # old_ids = shapes_layer.features['init_id'].values.astype(int)
            # curr_ids = shapes_layer.features['id'].values.astype(int)

            # ymins, xmins = np.array(shapes_layer.data).min(axis=1).T
            # ymaxs, xmaxs = np.array(shapes_layer.data).max(axis=1).T

            # cols = ['xmin', 'ymin', 'xmax', 'ymax', 'id']
            # vals = [xmins, ymins, xmaxs, ymaxs, curr_ids]

            # idxs = self.data[(self.data['filename'].str.contains(shapes_layer.name.split('bboxes_')[1])) & (self.data['id'].isin(old_ids))].index
            # # print(f'Updating {len(idxs)} rows in data')
            # for c, v in zip(cols, vals):
            #     self.data.loc[idxs, c] = v




        


            


        
