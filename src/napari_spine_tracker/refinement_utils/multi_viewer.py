import os, glob

import numpy as np

from qtpy.QtWidgets import (
    QPushButton,
    QSplitter, 
    QHBoxLayout,
    QSplitter,
    QCheckBox,
    QMessageBox
)

from napari_spine_tracker.tabs.multi_view  import  QtViewerWrap
from napari.components.viewer_model import ViewerModel
from napari_spine_tracker.refinement_utils.visualizer import FrameReader, FrameReaderWithIDs
from napari.layers.shapes._shapes_constants import Mode
from qtpy.QtCore import Qt

class MultiViewer:
    def __init__(self, 
                 root_plugin_widget, 
                 manager, 
                 img_dir,
                 filter_t1='_tp1_', #None,
                 filter_t2='_tp2_' # None
                 ):
        # print("MultiViewer created")
        self.root_widget = root_plugin_widget
        self.img_dir = img_dir
        self.manager = manager
        
        self.stack_names = np.unique([f.split('_layer')[0] for f in self.manager.get_unq_filenames()])
        
        self._extract_filenames_by_tp(filter_t1, filter_t2)
        data = self.manager.get_data()
        if len(data) == 0:
            self.next_new_id = 0
        else:
            self.next_new_id = np.max(data['id'].values) + 1

        if len(self.all_filenames) == 0:
            dialog = QMessageBox()
            dialog.setWindowTitle("Error")
            dialog.setText("The file is empty")
            dialog.exec_()
            print("No images found in the selected folder")
            return
        else:
            self.curr_stack = self.all_filenames[0].split('_layer')[0]
        
        self._prepare_visualizer()
        self._create_initial_widgets()
        
    def _create_initial_widgets(self):
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save)
        help_btn = QPushButton("Help")
        help_btn.clicked.connect(self.manager.help)

        h_layout = QHBoxLayout()
        h_layout.addStretch()

        for i, btn in enumerate([save_btn, help_btn]):
            btn.setFixedHeight(50)
            btn.setFixedWidth(200)
            btn.setStyleSheet('font-size: 20px;')
            h_layout.addWidget(btn, alignment=Qt.AlignCenter)
            if i != len([save_btn, help_btn]) - 1:
                h_layout.addSpacing(10)

        h_layout.addStretch()
        self.root_widget.layout.addLayout(h_layout)

    def _prepare_visualizer(self):
        self.viewer_model1 = ViewerModel(title="model1")
        self.viewer_model2 = ViewerModel(title="model2")
        self.qt_viewer1 = QtViewerWrap(self.root_widget.viewer, self.viewer_model1)
        self.qt_viewer2 = QtViewerWrap(self.root_widget.viewer, self.viewer_model2)
        self.frame_reader1 = FrameReader(self, self.viewer_model1, self.img_dir, self.filenames_t1, 'tp1')
        self.frame_reader2 = FrameReader(self, self.viewer_model2, self.img_dir, self.filenames_t2, 'tp2')

        self.frame_readers = [self.frame_reader1, self.frame_reader2]
        
        toolbar_splitter = QSplitter()
        toolbar_splitter.setOrientation(Qt.Horizontal)
        for fr in self.frame_readers:
            toolbar_splitter.addWidget(fr)
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
        self.root_widget.layout.addWidget(toolbar_splitter)

    def _extract_filenames_by_tp(self, filter_t1, filter_t2):
        all_filenames = []
        for sn in self.stack_names:
            all_filenames += list(glob.glob(os.path.join(self.img_dir, f"{sn}_layer*.png")))
        self.all_filenames = sorted([os.path.basename(f) for f in all_filenames])
        self.filenames_t1 = [f for f in self.all_filenames if filter_t1 in f]
        self.filenames_t2 = [f for f in self.all_filenames if filter_t2 in f]

    def _save(self):
        for fr in self.frame_readers:
            fr._update_coords()
        self.manager.save()

    def _toggle_synchronize(self, state):
        if state == Qt.Checked:
            self.frame_reader1.frame_slider.valueChanged.connect(self.frame_reader2.set_frame)
            self.frame_reader2.frame_slider.valueChanged.connect(self.frame_reader1.set_frame)
        else:
            self.frame_reader1.frame_slider.valueChanged.disconnect(self.frame_reader2.set_frame)
            self.frame_reader2.frame_slider.valueChanged.disconnect(self.frame_reader1.set_frame)
    
    def _toggle_selection_mode(self, state):
        for fr in self.frame_readers:
            shapes_layer_name = fr.get_shapes_layer_name()
            if fr.show_bboxes_checkbox.isChecked() and shapes_layer_name is not None:
                if state == Qt.Checked:            
                    fr.shapes_layer.mode = Mode.SELECT
                else:
                    fr.shapes_layer.mode = Mode.PAN_ZOOM
    
    def change_next_new_id(self, next_new_id):
        self.next_new_id = next_new_id

class SingleViewer(MultiViewer):
    # class heriting from MultiViewer, but with only one viewer, thus, no timepoints and no synchronization
    def __init__(self, 
                 root_plugin_widget, 
                 manager, 
                 img_dir,
                 detection_refinement=False,
                 ):
        # # print("MultiViewer created")
        self.root_widget = root_plugin_widget
        self.img_dir = img_dir
        self.manager = manager
        self.detection_ref = detection_refinement
        
        self.stack_names = np.unique([f.split('_layer')[0] for f in self.manager.get_unq_filenames()])
        
        self._extract_filenames_by_tp()
        data = self.manager.get_data()
        if not self.detection_ref:
            if len(data) == 0:
                self.next_new_id = 0
            else:
                self.next_new_id = np.max(data['id'].values) + 1 # here

        if len(self.all_filenames) == 0:
            print("No images found in the selected folder")
            return
        else:
            self.curr_stack = self.all_filenames[0].split('_layer')[0]
        
        self._prepare_visualizer()
        self._create_initial_widgets()
    
    # override the _prepare_visualizer method
    def _prepare_visualizer(self):
        self.viewer_model1 = ViewerModel(title="model1")
        self.qt_viewer1 = QtViewerWrap(self.root_widget.viewer, 
                                       self.viewer_model1)
        if self.detection_ref:
            self.frame_reader1 = FrameReader(self, self.viewer_model1, 
                                         self.img_dir, 
                                         self.all_filenames,
                                         tp_name=None,
                                         )
        else:
            self.frame_reader1 = FrameReaderWithIDs(self, self.viewer_model1, 
                                         self.img_dir, 
                                         self.all_filenames,
                                         tp_name=None,
                                         )

        self.frame_readers = [self.frame_reader1]
        
        toolbar_splitter = QSplitter()
        toolbar_splitter.setOrientation(Qt.Horizontal)
        for fr in self.frame_readers:
            toolbar_splitter.addWidget(fr)
        toolbar_splitter.setContentsMargins(0, 0, 0, 0)
        
        viewer_splitter = QSplitter()
        viewer_splitter.setOrientation(Qt.Horizontal)
        viewer_splitter.addWidget(self.qt_viewer1)
        viewer_splitter.setContentsMargins(0, 0, 0, 0)

        # self.sync_checkbox = QCheckBox("Synchronize frame number")
        # self.sync_checkbox.stateChanged.connect(self._toggle_synchronize)
        # self.sync_checkbox.setChecked(False)

        self.selection_mode = QCheckBox("Selection mode")
        self.selection_mode.stateChanged.connect(self._toggle_selection_mode)
        self.selection_mode.setChecked(False)

        self.root_widget.layout.addWidget(viewer_splitter)
        self.root_widget.layout.setSpacing(0)

        h_layout = QHBoxLayout()
        h_layout.addStretch(1)
        for w in [self.selection_mode]: # self.sync_checkbox, 
            h_layout.addWidget(w, alignment=Qt.AlignCenter)
        h_layout.addStretch(1)
        self.root_widget.layout.addLayout(h_layout)
        self.root_widget.layout.addWidget(toolbar_splitter)

    def _extract_filenames_by_tp(self):
        all_filenames = []
        for sn in self.stack_names:
            all_filenames += list(glob.glob(os.path.join(self.img_dir, f"{sn}_layer*.png")))
        self.all_filenames = sorted([os.path.basename(f) for f in all_filenames])



        