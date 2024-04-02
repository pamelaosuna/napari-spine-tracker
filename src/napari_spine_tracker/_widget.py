"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""
from typing import TYPE_CHECKING

from magicgui import magic_factory
from qtpy.QtWidgets import QHBoxLayout, QPushButton, QWidget, QVBoxLayout
from qtpy.QtCore import Qt

if TYPE_CHECKING:
    import napari

from napari_spine_tracker.tabs import *
import napari
import os

class ExampleQWidget(QWidget):
    # your QWidget.__init__ can optionally request the napari viewer instance
    # in one of two ways:
    # 1. use a parameter called `napari_viewer`, as done here
    # 2. use a type annotation of 'napari.viewer.Viewer' for any parameter
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        btn = QPushButton("Click me!")
        btn.clicked.connect(self._on_click)

        self.setLayout(QHBoxLayout())
        self.layout().addWidget(btn)

    def _on_click(self):
        print("napari has", len(self.viewer.layers), "layers")

@magic_factory
def example_magic_widget(img_layer: "napari.layers.Image"):
    print(f"you have selected {img_layer}")

# Uses the `autogenerate: true` flag in the plugin manifest
# to indicate it should be wrapped as a magicgui to autogenerate
# a widget.
def example_function_widget(img_layer: "napari.layers.Image"):
    print(f"you have selected {img_layer}")

class TrackingCurationWidget(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        # hide panel layer controls
        # self.viewer.window._qt_viewer.dockLayerControls.toggleViewAction().trigger()
        # self.viewer.window._qt_viewer.dockLayerList.toggleViewAction().trigger()

        self.set_default_dirs()
        self.data_loaded = False

        self._create_initial_widgets()

    def _create_initial_widgets(self):
        btn_new_project = QPushButton("New Project")
        btn_open_project = QPushButton("Open Project")
        btn_help = QPushButton("Help")

        btn_open_project.clicked.connect(self._open_project)
        btn_help.clicked.connect(self._help)
        btn_new_project.clicked.connect(self._new_project)

        self.layout = QVBoxLayout()
        for btn in [btn_new_project, btn_open_project, btn_help]:
            btn.setFixedHeight(50)
            btn.setFixedWidth(200)
            btn.setStyleSheet("font-size: 20px;")
            self.layout.addWidget(btn, alignment=Qt.AlignCenter)
        
        self.setLayout(self.layout)
        
    def _open_project(self):
        self.parent().setFloating(True)
        self.parent().showMaximized()
        # print("Open Project")
        open_project = OpenProject(self)
        open_project.show()
    
    def _help(self):
        print("Help")
        
    def _new_project(self):
        print("New Project")
        self.parent().setFloating(True)
        self.parent().showMaximized()
        new_project = NewProject(self)
        new_project.show()

    def set_default_dirs(self):
        self.csv_dir_default = os.path.join(os.getcwd(), '..', '..', 'Documents/spines/data/data_train_test_val/annotations_simonsdata/tmp/curated/') # 'Documents/spines/data/bens_data/results/lr_0.001_warmup_None_momentum_0.6_L2_None_union/time_tracking') #'eval_ttrack') #
        self.img_dir_default = os.path.join(os.getcwd(), '..',  '..', 'Documents/spines/data/data_train_test_val/images_simonsdata/aid052N2D5_stack1/') # , 'subs') #, "..", "benzo_pipeline", "A1_preprocessed", "8bit", "subs") # 'Documents', 'spines', 'data', 'bens_data', 'processed', 'img_512')
        self.filepath_default = os.path.join(self.csv_dir_default, 'aid052N2D5_tp1_stack1_default_aug_False_epoch_19_theta_0.5_delta_0.1_Test.csv') # "aidv853_date220321_stack0_sub12.csv") # 'date040822_stack1_sub11_timetracked.csv') 
        
        
    def _update_loaded_state(self, loaded, filepath, img_dir):
        # print("Updating project state")
        self.data_loaded = loaded
        self.filepath = filepath
        self.img_dir = img_dir
        self.csv_dir = os.path.dirname(self.filepath)
        self.filename = os.path.basename(self.filepath)

        if loaded:
            self._create_curation_widgets()
    
    def _create_curation_widgets(self):
        # print("Creating curation widgets")
        # remove btn_new_project, btn_open_project, btn_help
        for _ in range(3):
            self.layout.removeWidget(self.layout.itemAt(0).widget())

        self.refine_timetracking = RefineTracking(self)

if __name__ == '__main__':
    viewer = napari.Viewer()
    napari.run()