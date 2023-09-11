import os, glob
import numpy as np
from skimage import io
from qtpy.QtWidgets import QSplitter, QVBoxLayout
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
        self.last_interacted_shape = None

        self._prepare_reader()

        # bind key press 'i' to _change_id()
        self.viewer_model.bind_key('i', self.viz._change_id_on_dialog)

    def _prepare_reader(self):
        init_frame_val = 76

        self._old_frame = None
        self.frame_num = init_frame_val

        self._load_images()
        self.viewer_model.add_image(self.imgs[init_frame_val], name=self.filenames[init_frame_val])

        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.setMinimum(0)
        self.frame_slider.setMaximum(len(self.filenames)-1)
        self.frame_slider.setValue(init_frame_val)
        self.frame_slider.valueChanged.connect(self.set_frame)

        self.frame_text = QLabel(f'Frame number: {self.frame_num}')
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
        self.frame_text.setText(f'Frame number: {frame}')
        self.fname_text.setText(self.filenames[frame])
        self.frame_num = frame
        self.remove_bboxes()
        self.show_bboxes_in_frame()
        self._set_contrast_limits(self.contrast_range_slider.value())

    def _load_images(self):
        print(f'Adding {len(self.filenames)} images to viewer')
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
        for layer in self.viewer_model.layers:
            if 'bbox_' in layer.name:
                self.viewer_model.layers.remove(layer)

    def show_bboxes_in_frame(self):
        if not self.show_bboxes_checkbox.isChecked():
            self.update_data(self.viewer_model.layers)
            self.remove_bboxes()
        else:
            objs = self.viz.data[self.viz.data['filename'].str.contains(self.filenames[self.frame_num])]
            text_params = {
                    'string': 'id',
                    'size': 8,
                    'color': 'yellow',
                    'anchor': 'upper_left',
                    'translation': [-1, 1],
                }
            for i, row in objs.iterrows():
                xmin, ymin, xmax, ymax = row[['xmin', 'ymin', 'xmax', 'ymax']]
                bbox_rect = [[ymin, xmin], [ymin, xmax], [ymax, xmax], [ymax, xmin]]
                id = row['id']
                feats = {
                    'id': [str(id)],
                }
                c = 'yellow' if str(row['class']) == 'spine' else 'green'
                text_params['color'] = c
                layer_name = f'bbox_{id}_{self.filenames[self.frame_num]}'
                self.viewer_model.add_shapes(bbox_rect,
                                       features=feats,
                                       shape_type='rectangle',
                                       edge_color=c,
                                       face_color='transparent',
                                       name=layer_name,
                                       visible=True,
                                       text=text_params,
                                       )
                shape_layer = self.viewer_model.layers[layer_name]
                if self.viz.selection_mode.isChecked():
                    shape_layer.mode = Mode.SELECT
                
                @shape_layer.mouse_drag_callbacks.append
                def click_drag(layer, event):
                    if self.show_bboxes_checkbox.isChecked() and self.viz.selection_mode.isChecked():
                        # print('mouse down')
                        dragged = False
                        yield

                        # on move
                        while event.type == 'mouse_move':
                            # print(event.position)
                            dragged = True
                            yield

                        self.viz.update_last_interacted_shape(shape_layer)
                        # on release
                        # if dragged:
                        #     print('drag end')
                        # else:
                        #     print('clicked')
                        #     print(layer_name)
        
class IdChanger(QDialog):
    def __init__(self, parent:QWidget, shape_layer):
        super().__init__(parent)
        self.shape_layer = shape_layer
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
            feats = {'id': [str(new_id)],
                }
            self.shape_layer.features = feats
            print(f'Changing ID to {new_id}')
            self.close()
            
class TrackletVisualizer:
    def __init__(self, 
                 root_plugin_widget, 
                 manager, 
                 img_dir,
                 filter_t1=None,
                 filter_t2=None
                 ):
        print("TrackletVisualizer created")
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
        # self.filenames_t1 = ["aidv853_date220321_tp1_stack0_sub11_layer076.png", "aidv853_date220321_tp1_stack0_sub11_layer077.png"] # TODO: remove after testing
        # self.filenames_t2 = ["aidv853_date220321_tp2_stack0_sub11_layer076.png", "aidv853_date220321_tp2_stack0_sub11_layer077.png"] # TODO: remove after testing

        if len(self.all_filenames) > 0:
            self.curr_stack = self.all_filenames[0].split('_layer')[0]
        else:
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
        self.root_widget.layout.addWidget(self.sync_checkbox, alignment=Qt.AlignCenter)
        self.root_widget.layout.addWidget(self.selection_mode, alignment=Qt.AlignCenter)
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
        if state == Qt.Checked:
            for vm, fr in zip([self.viewer_model1, self.viewer_model2], [self.frame_reader1, self.frame_reader2]):
                if fr.show_bboxes_checkbox.isChecked():
                    # make all bboxes in the current frame selectable
                    self._make_selectable(vm)
        else:
            for vm in [self.viewer_model1, self.viewer_model2]:
                self._make_unselectable(vm)
        
    def _make_selectable(self, viewer_model):
        bboxes_names = [layer.name for layer in viewer_model.layers if 'bbox_' in layer.name]
        for bn in bboxes_names:
            bbox = viewer_model.layers[bn]
            bbox.mode = Mode.SELECT
            print(f"bbox {bn} is now selectable")
    
    def _make_unselectable(self, viewer_model):
        for layer in viewer_model.layers:
            if 'bbox_' in layer.name:
                layer.mode = Mode.PAN_ZOOM
    
    def update_last_interacted_shape(self, shape):
        self.last_interacted_shape = shape

    def update_data(self, layers):
        shapes = [layer for layer in layers if 'bbox_' in layer.name]
        for s in shapes:
            old_id = int(s.name.split('bbox_')[1].split('_')[0])
            name = s.name.split(f'bbox_{old_id}_')[1]

            ymin, xmin = s.data[0].min(axis=0)
            ymax, xmax = s.data[0].max(axis=0)
            curr_id = int(s.text.values[0])

            cols = ['xmin', 'ymin', 'xmax', 'ymax', 'id']
            vals = [xmin, ymin, xmax, ymax, curr_id]

            idx = self.data.loc[(self.data['filename'].str.contains(name)) & (self.data['id'] == old_id)].index[0]
            for c, v in zip(cols, vals):
                self.data.loc[idx, c] = v
            # self.data.loc[idx, 'id'] = curr_id
            
    def _change_id_on_dialog(self, viewer_model):
        if self.last_interacted_shape is None:
            print('No rectangle selected')
            return
        change_id_dialog = IdChanger(self.root_widget, 
                                     self.last_interacted_shape)
        change_id_dialog.show()
    
    # def update_id_selected_rect(self, new_id):
    #     # find the row to modify in viz.data and set the new id
    #     frame_num, id = self.last_interacted_shape.name.split('_')[1:3]
    #     frame_reader = self.frame_reader1 if self.last_interacted_shape.name.endswith('_frame1') else self.frame_reader2
    #     filename = frame_reader.filenames[frame_num]





        


            


        
