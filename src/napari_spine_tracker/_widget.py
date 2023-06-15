"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""
from typing import TYPE_CHECKING

from magicgui import magic_factory
from qtpy.QtWidgets import QHBoxLayout, QPushButton, QWidget, QVBoxLayout
from qtpy.QtWidgets import QSplitter, QTabWidget
from qtpy.QtCore import Qt
from napari.components.viewer_model import ViewerModel


if TYPE_CHECKING:
    import napari

from napari_spine_tracker.tabs import *
import napari
import os
import numpy as np

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

        # self.viewer.window.add_dock_widget(self, area="right", name="t1")
        # self.viewer.window.add_dock_widget(self, area="right", name="t2")

        self.set_default_dirs()
        self.data_loaded = False

        self.create_initial_widgets()
    
    def create_initial_widgets(self):
        btn_new_project = QPushButton("New Project")
        btn_open_project = QPushButton("Open Project")
        # btn_save_project = QPushButton("Save Project")
        btn_help = QPushButton("Help")

        btn_open_project.clicked.connect(self._open_project)
        # btn_save_project.clicked.connect(self._save_project)
        btn_help.clicked.connect(self._help)
        btn_new_project.clicked.connect(self._new_project)

        self.layout = QVBoxLayout()
        self.layout.addWidget(btn_new_project)
        self.layout.addWidget(btn_open_project)
        # self.layout.addWidget(btn_save_project)
        self.layout.addWidget(btn_help)
        
        self.setLayout(self.layout)

    def _open_project(self):
        print("Open Project")
        open_project = OpenProject(self)
        open_project.show()
    
    def _save_project(self):
        print("Save Project")
        # TODO

    def _help(self):
        print("Help")
        # TODO
    
    def _new_project(self):
        print("New Project")
        # TODO

    def set_default_dirs(self):
        self.csv_dir_default = os.path.join(os.getcwd(), "..", "eval_ttrack")
        self.img_dir_default = os.path.join(os.getcwd(), "..", "benzo_pipeline", "A2_registered", "8bit", "subs")
    
    def _update_loaded_state(self, loaded, filepath, img_dir):
        print("Updating project state")
        self.data_loaded = loaded
        self.filepath = filepath
        self.img_dir = img_dir
        self.csv_dir = os.path.dirname(self.filepath)
        self.filename = os.path.basename(self.filepath)

        if loaded:
            self.create_curation_widgets()
    
    def create_curation_widgets(self):
        print("Creating curation widgets")
        # remove btn_new_project, btn_open_project, btn_help
        for _ in range(3):
            self.layout.removeWidget(self.layout.itemAt(0).widget())

        self.refine_timetracking = RefineTimeTracking(self)

if __name__ == '__main__':
    # viewer = napari.Viewer()
    # napari.run()

    # add the image
    viewer = napari.Viewer()

    person = np.array([[505, 60], [402, 71], [383, 42], [251, 95], [212, 59],
                   [131, 137], [126, 187], [191, 204], [171, 248], [211, 260],
                   [273, 243], [264, 225], [430, 173], [512, 160]])

    building = np.array([[310, 382], [229, 381], [209, 401], [221, 411],
                     [258, 411], [300, 412], [306, 435], [268, 434],
                     [265, 454], [298, 461], [307, 461], [307, 507],
                     [349, 510], [352, 369], [330, 366], [330, 366]])
    
    polygons = [building]



    text_parameters = {
        "string": "label",
        "size": 100,
        "color": "red",
        "anchor": "center",
    }


    # add the polygons
    shapes_layer = viewer.add_shapes(polygons, 
                                     shape_type='polygon', 
                                     edge_width=2,
                                      edge_color='coral', 
                                      face_color='transparent',
                                      text=text_parameters,
                                      )
    napari.run()




