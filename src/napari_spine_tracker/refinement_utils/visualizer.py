import os, glob
import numpy as np
from qtpy.QtWidgets import QSplitter, QVBoxLayout
from qtpy.QtWidgets import QSplitter, QTabWidget
from qtpy.QtCore import Qt

from napari.components.viewer_model import ViewerModel
from napari_spine_tracker.tabs.multi_view import  QtViewerWrap, DummyWidget


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
        
        self._curr_frame = 0
        self.curr_frame = 0

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

        # get layout and add widgets
        self.viewer_model1 = ViewerModel(title="model1")
        self.viewer_model2 = ViewerModel(title="model2")
        self.qt_viewer1 = QtViewerWrap(self.root_widget.viewer, self.viewer_model1)
        self.qt_viewer2 = QtViewerWrap(self.root_widget.viewer, self.viewer_model2)
        self.tab_widget = QTabWidget()
        w1 = DummyWidget()
        w2 = DummyWidget()
        self.tab_widget.addTab(w1, "Sample 1")
        self.tab_widget.addTab(w2, "Sample 2")
        viewer_splitter = QSplitter()
        viewer_splitter.setOrientation(Qt.Horizontal)
        viewer_splitter.addWidget(self.qt_viewer1)
        viewer_splitter.addWidget(self.qt_viewer2)
        viewer_splitter.setContentsMargins(0, 0, 0, 0)

        self.root_widget.layout.addWidget(viewer_splitter)
        self.root_widget.layout.addWidget(self.tab_widget)

        self.add_images(self.filenames_t1, self.qt_viewer1)
        self.add_images(self.filenames_t2, self.qt_viewer2)

    def add_images(self, filenames, viewer_model):
        for fn in filenames[:3]:
            viewer_model.add_image(os.path.join(self.img_dir, fn), name=fn)
        
