"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""
from typing import TYPE_CHECKING

from magicgui import magic_factory
from qtpy.QtWidgets import QHBoxLayout, QPushButton, QWidget, QVBoxLayout

if TYPE_CHECKING:
    import napari

from napari_spine_tracker.tabs import *
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

class TrackingCorrectionWidget(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        self.set_default_dirs()
        self.loaded = False

        self.create_initial_widgets()
    
    def create_initial_widgets(self):
        btn_new_project = QPushButton("New Project")
        btn_open_project = QPushButton("Open Project")
        btn_save_project = QPushButton("Save Project")
        btn_help = QPushButton("Help")

        btn_open_project.clicked.connect(self._open_project)
        btn_save_project.clicked.connect(self._save_project)
        btn_help.clicked.connect(self._help)
        btn_new_project.clicked.connect(self._new_project)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(btn_new_project)
        self.layout().addWidget(btn_open_project)
        self.layout().addWidget(btn_save_project)
        self.layout().addWidget(btn_help)

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
        self.ims_dir_default = os.path.join(os.getcwd(), "..", "benzo_pipeline", "A2_registered", "8bit", "subs")
    
    def _update_project_state(self, loaded, filepath, ims_dir):
        print("Updating project state")
        self.loaded = loaded
        self.filepath = filepath
        self.ims_dir = ims_dir
        self.csv_dir = os.path.dirname(self.filepath)
        self.filename = os.path.basename(self.filepath)

        if loaded:
            self.create_correction_widgets()
    
    def create_correction_widgets(self):
        print("Creating correction widgets")
        