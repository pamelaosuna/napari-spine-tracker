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

from napari.components.viewer_model import ViewerModel
from napari_spine_tracker.tabs.multi_view import  QtViewerWrap

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

        self.btn = QPushButton("Perform action")
        init_frame_val = 0
        self.frame_num = 0
        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.setMinimum(0)
        self.frame_slider.setMaximum(len(filenames)-1)
        self.frame_slider.setValue(init_frame_val)

        self.frame_text = QLabel(f'Frame number: {self.frame_num}')
        self.frame_text.setAlignment(Qt.AlignCenter)
        self.fname_text = QLabel(self.filenames[self.frame_num])
        self.fname_text.setAlignment(Qt.AlignLeft)
        self.fname_text.setStyleSheet("font: 10pt")

        self.show_bboxes_checkbox = QCheckBox('Show Bounding Boxes')
        self.show_bboxes_checkbox.setChecked(self.show_bboxes)
        self.show_bboxes_checkbox.stateChanged.connect(self.show_bboxes_in_frame)

        # self.contrast_range_slider = QSlider(Qt.Horizontal)
        # self.contrast_range_slider.valueChanged.connect(self._set_contrast_limits)

        self.frame_slider.valueChanged.connect(self.set_frame)
        
        # self.spin = QDoubleSpinBox()
        layout = QVBoxLayout()
        layout.addWidget(self.fname_text)
        layout.addWidget(self.frame_text)
        layout.addWidget(self.frame_slider)
        layout.addWidget(self.show_bboxes_checkbox)
        # layout.addWidget(self.spin)
        layout.addWidget(self.btn)
        layout.addStretch(1)
        self.setLayout(layout)

        self.add_images()
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

    def add_images(self):
        print(f'Adding {len(self.filenames)} images to viewer')
        for fn in self.filenames:
            img = io.imread(os.path.join(self.img_dir, fn))
            self.viewer_model.add_image(img, name=fn)
            self.viewer_model.layers[fn].visible = False
    
    def update_synchronize(self):
        self.synchronize = not(self.synchronize)

    def _set_contrast_limits(self, cmin, cmax):
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

        self.filenames = manager.filenames
        self.objects = manager.objects
        self.data = manager.data

        self.stack_names = np.unique([f.split('_layer')[0] for f in self.filenames])
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
        self.add_bboxes()

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
    
    def add_bboxes(self):
        text_params = {
                    'string': 'lalala',
                    'size': 20,
                    'color': 'red',
                    'anchor': 'upper_left',
                    'translation': [-1, 1],
                    }
        for frame_num in range(len(self.filenames_t1)):
            objs_t1 = self.objects[self.objects[:, -2] == self.filenames_t1[frame_num]]
            for obj in objs_t1:
                x1, y1, x2, y2 = obj[:4]
                rect = [[y1, x1], [y1, x2], [y2, x2], [y2, x1]]
                id = obj[-3]
                # text_params['string'] = str(id)
                self.viewer_model1.add_shapes(rect,
                                       shape_type='rectangle',
                                       edge_color='red',
                                       face_color='transparent',
                                       name=f'bboxes_{frame_num}_{id}',
                                       visible=False,
                                       )

            objs_t2 = self.objects[self.objects[:, -2] == self.filenames_t2[frame_num]]
            for obj in objs_t2:
                x1, y1, x2, y2 = obj[:4]
                rect = [[y1, x1], [y1, x2], [y2, x2], [y2, x1]]
                id = obj[-3]
                # text_params['string'] = str(id)
                self.viewer_model2.add_shapes(rect,
                                       shape_type='rectangle',
                                       edge_color='red',
                                       face_color='transparent',
                                       name=f'bboxes_{frame_num}_{id}',
                                       visible=False,
                                       )
            
            


        
