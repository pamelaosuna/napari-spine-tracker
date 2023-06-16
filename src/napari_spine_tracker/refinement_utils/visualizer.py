import os, glob
import numpy as np
from skimage import io
from qtpy.QtWidgets import QSplitter, QVBoxLayout
from qtpy.QtWidgets import QSplitter, QTabWidget
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QPushButton,
    QSlider,
    QWidget,
    QLabel,
    QCheckBox,
    )
from qtpy.QtGui import QIcon

from napari.components.viewer_model import ViewerModel
from napari_spine_tracker.tabs.multi_view import  QtViewerWrap
from superqt import QRangeSlider

class FrameReader(QWidget):
    """
    Dummy widget showcasing how to place additional widgets to the right
    of the additional viewers.
    """
    def __init__(self, viz, viewer_model, img_dir, filenames):
        super().__init__()
        self.viz = viz
        self.viewer_model = viewer_model
        self.img_dir = img_dir
        self.filenames = filenames

        self.synchronize = False
        self.show_bboxes = False

        self._prepare_reader()


    def _prepare_reader(self):
        init_frame_val = 0

        self.frame_num = init_frame_val
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
        self.show_bboxes_checkbox.setChecked(self.show_bboxes)
        self.show_bboxes_checkbox.stateChanged.connect(self.show_bboxes_in_frame)

        self.contrast_range_slider = QRangeSlider(Qt.Orientation.Horizontal, self)
        self.contrast_range_slider.valueChanged.connect(self._set_contrast_limits)

        # # when user presses click + shift, the selection mode is toggled
        # self.viewer_model.events.mouse_press.connect(self._toggle_select)

        layout = QVBoxLayout()
        for w in [self.fname_text, self.frame_text, self.frame_slider, self.show_bboxes_checkbox, self.contrast_range_slider]:
            layout.addWidget(w)
        layout.addStretch(1)
        self.setLayout(layout)

        self._add_init_images()
        self.viewer_model.layers[init_frame_val].visible = True

    def set_frame(self, frame):
        for layer in self.viewer_model.layers:
            layer.visible = False
        self.viewer_model.layers[frame].visible = True
        self.frame_slider.setValue(frame)
        self.frame_text.setText(f'Frame number: {frame}')
        self.fname_text.setText(self.filenames[frame])
        self.frame_num = frame
        self.show_bboxes_in_frame()

    def _add_init_images(self):
        print(f'Adding {len(self.filenames)} images to viewer')
        imgs = []
        for fn in self.filenames:
            img = io.imread(os.path.join(self.img_dir, fn))
            imgs.append(img)
            self.viewer_model.add_image(img, name=fn)
            self.viewer_model.layers[fn].visible = False

        imgs = np.array(imgs)
        max_val = np.max(imgs)
        # convert max_val to binary and see how many digits it has
        max_val_bin = bin(max_val)[2:]
        max_val_bin_len = len(max_val_bin)

        # set contrast limits to be 0 and 2^max_val_bin_len
        self.contrast_range_slider.setRange(0, 2**max_val_bin_len)
        self.contrast_range_slider.setValue([0, 2**max_val_bin_len])

    def update_synchronize(self):
        self.synchronize = not(self.synchronize)

    def _set_contrast_limits(self, values):
        cmin, cmax = values
        self.viewer_model.layers[self.filenames[self.frame_num]].contrast_limits = (cmin, cmax)

    def show_bboxes_in_frame(self):
        if self.show_bboxes_checkbox.isChecked():
            # make invisible all bboxes except for the ones in the current frame
            for layer in self.viewer_model.layers:
                if 'bboxes_' in layer.name:
                    if layer.name.split('_')[1].split('_')[0] == str(self.frame_num):
                        layer.visible = True
                    else:
                        layer.visible = False
        else:
            for layer in self.viewer_model.layers:
                if 'bboxes_' in layer.name:
                    layer.visible = False
    
    # def _toggle_select(self, event):
    #     # if user clicks on a shape and presses 'shift', select the shape
    #     if event.key == 'Shift':
    #         if event.item is not None and 'bbox_' in event.item.name:
    #             event.item.selected = not(event.item.selected)
    #             self.viewer_model.layers[self.filenames[self.frame_num]].refresh()
    #             self.viewer_model.layers[self.filenames[self.frame_num]].events.data_view_changed()

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
        
        self.synchronize = False # synchronize frame slider across viewers

        self.unq_filenames = manager.unq_filenames
        # self.objects = manager.objects
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
            return
        
        self._prepare_visualizer()
        self._add_init_bboxes()

    def _prepare_visualizer(self):
        self.viewer_model1 = ViewerModel(title="model1")
        self.viewer_model2 = ViewerModel(title="model2")
        self.qt_viewer1 = QtViewerWrap(self.root_widget.viewer, self.viewer_model1)
        self.qt_viewer2 = QtViewerWrap(self.root_widget.viewer, self.viewer_model2)
        self.frame_reader1 = FrameReader(self, self.viewer_model1, self.img_dir, self.filenames_t1)
        self.frame_reader2 = FrameReader(self, self.viewer_model2, self.img_dir, self.filenames_t2)
        
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

        self.root_widget.layout.addWidget(viewer_splitter)
        self.root_widget.layout.setSpacing(0)
        self.root_widget.layout.addWidget(self.sync_checkbox, alignment=Qt.AlignCenter)
        self.root_widget.layout.addWidget(toolbar_splitter)
    
    def _toggle_synchronize(self, state):
        self.synchronize = not(self.synchronize)
        self.frame_reader1.update_synchronize()
        self.frame_reader2.update_synchronize()
        if state == Qt.Checked:
            self.frame_reader1.frame_slider.valueChanged.connect(self.frame_reader2.set_frame)
            self.frame_reader2.frame_slider.valueChanged.connect(self.frame_reader1.set_frame)
        else:
            self.frame_reader1.frame_slider.valueChanged.disconnect(self.frame_reader2.set_frame)
            self.frame_reader2.frame_slider.valueChanged.disconnect(self.frame_reader1.set_frame)
    
    def _add_init_bboxes(self):
        text_params = {
                    'string': 'id',
                    'size': 8,
                    'color': 'red',
                    'anchor': 'upper_left',
                    'translation': [-1, 1],
                }
        for frame_num in range(len(self.filenames_t1)):
            objs_t1 = self.data[self.data['filename'].str.contains(self.filenames_t1[frame_num])]
            for i, row in objs_t1.iterrows():
                xmin, ymin, xmax, ymax = row[['xmin', 'ymin', 'xmax', 'ymax']]
                bbox_rect = [[ymin, xmin], [ymin, xmax], [ymax, xmax], [ymax, xmin]]
                id = row['id']
                feats = {
                    'id': [str(id)],
                }
                c = 'red' if str(row['class']) == 'spine' else 'green'
                text_params['color'] = c
                self.viewer_model1.add_shapes(bbox_rect,
                                       features=feats,
                                       shape_type='rectangle',
                                       edge_color=c,
                                       face_color='transparent',
                                       name=f'bbox_{frame_num}_{id}',
                                       visible=False,
                                       text=text_params,
                                       )

            objs_t2 = self.data[self.data['filename'].str.contains(self.filenames_t2[frame_num])]
            for i, row in objs_t2.iterrows():
                c = 'red' if str(row['class']) == 'spine' else 'green'
                text_params['color'] = c
                xmin, ymin, xmax, ymax = row[['xmin', 'ymin', 'xmax', 'ymax']]
                bbox_rect = [[ymin, xmin], [ymin, xmax], [ymax, xmax], [ymax, xmin]]
                id = row['id']
                feats = {
                    'id': [str(id)],
                }
                self.viewer_model2.add_shapes(bbox_rect,
                                       features=feats,
                                       shape_type='rectangle',
                                       edge_color=c,
                                       face_color='transparent',
                                       name=f'bbox_{frame_num}_{id}',
                                       visible=False,
                                       text=text_params,
                                       )

        


            


        
