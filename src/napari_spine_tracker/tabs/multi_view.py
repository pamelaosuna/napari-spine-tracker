"""
This is an example on how to have more than one viewer in the same napari window.
Additional viewers state will be synchronized with the main viewer.
Switching to 3D display will only impact the main viewer.

This example also contain option to enable cross that will be moved to the
current dims point (`viewer.dims.point`).
"""

import numpy as np
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QSlider,
)
from napari.qt import QtViewer

class QtViewerWrap(QtViewer):
    def __init__(self, main_viewer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_viewer = main_viewer

    def _qt_open(
        self,
        filenames: list,
        stack: bool,
        plugin: str = None,
        layer_type: str = None,
        **kwargs,
    ):
        """for drag and drop open files"""
        self.main_viewer.window._qt_viewer._qt_open(
            filenames, stack, plugin, layer_type, **kwargs
        )