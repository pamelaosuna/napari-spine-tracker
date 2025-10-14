"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""
from typing import TYPE_CHECKING, Optional
import logging
from pathlib import Path

from qtpy.QtWidgets import (
    QHBoxLayout, QPushButton, QWidget, QVBoxLayout,
    QFrame, QMessageBox, QLabel
)
from qtpy.QtCore import Qt, QSettings
from qtpy.QtGui import QFont, QPalette

if TYPE_CHECKING:
    import napari

from napari_spine_tracker.tabs import (
    OpenProject, NewProject, RefineTracking
)
import napari
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrackingCurationWidget(QWidget):
    """
    Main widget for the Napari Spine Tracking Curation plugin.

    This widget provides an interface for user to manage spine tracking 
    projects, including the creation of new projects, opening existing ones,
    and performing detection, depth-tracking and time-tracking refinement.
    """

    def __init__(self, napari_viewer: "napari.Viewer"):
        super().__init__()
        self.viewer = napari_viewer

        # Project state
        self._project_loaded = False
        self._setup_default_directories()

        # UI Settings
        self._settings = QSettings("NapariSpineTracker", "Settings")

        # Create the initial interface
        self._create_initial_widgets()

    def _create_initial_widgets(self):
        """
        Create the initial project selection interface.
        """
        self.setMinimumSize(300, 400)
        self.setWindowTitle("Spine Tracking Curation")

        # Main layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        # Header section
        self._create_header()

        # Create project buttons
        self._create_project_buttons()

        # Status section
        self._create_status_section()
        
        self.setLayout(self.main_layout)
    
    def _maximize_window(self):
        """Maximize the parent window for better workspace."""
        try:
            if self.parent():
                self.parent().setFloating(True)
                self.parent().showMaximized()
        except Exception as e:
            logger.warning(f"Could not maximize window: {e}")

    def _create_header(self):
        """Create the header section with title and description."""
        header_frame = QFrame()
        header_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Napari Spine Tracker")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        
        # Description
        desc_label = QLabel("Manage and refine spine tracking data")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        desc_label.setWordWrap(True)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(desc_label)
        header_frame.setLayout(header_layout)
        
        self.main_layout.addWidget(header_frame)

    def _create_status_section(self):
        """Create the status information section."""
        self.status_label = QLabel("No project loaded")
        self.status_label.setAlignment(Qt.AlignCenter)
        self._update_status_display()
        
        self.main_layout.addWidget(self.status_label)
        self.main_layout.addStretch(1)

    def _create_project_buttons(self):
        """
        Create the main project management buttons.
        """
        button_frame = QFrame()
        button_layout = QVBoxLayout()
        button_layout.setSpacing(15)
        
        # Create project buttons
        self.btn_new_project = self._create_styled_button(
            "📁 New Project", 
            "Create a new spine tracking project",
            self._handle_new_project
        )
        
        self.btn_open_project = self._create_styled_button(
            "📂 Open Project", 
            "Load an existing spine tracking project",
            self._handle_open_project
        )
        
        self.btn_help = self._create_styled_button(
            "❓ Help", 
            "View documentation and shortcuts",
            self._handle_help
        )
        
        # Add buttons to layout
        for btn in [self.btn_new_project, self.btn_open_project, self.btn_help]:
            button_layout.addWidget(btn, alignment=Qt.AlignCenter)
        
        button_frame.setLayout(button_layout)
        self.main_layout.addWidget(button_frame)

    def _create_styled_button(self, text: str, tooltip: str, callback) -> QPushButton:
        """Create a consistently styled button."""
        btn = QPushButton(text)
        btn.setFixedHeight(60)
        btn.setFixedWidth(280)
        btn.setToolTip(tooltip)
        btn.clicked.connect(callback)
        
        # Modern button styling
        btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 8px;
                background-color: #3498db;
                color: white;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
                border-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
                border-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                border-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        
        return btn
        
    def _handle_open_project(self):
        """
        Handle opening existing project.
        """
        logger.info("Opening existing project")
        try:
            self._maximize_window()
            open_project_dialog = OpenProject(self)
            open_project_dialog.exec_()
        except Exception as e:
            logger.error(f"Error opening project: {e}")
            self._show_error_message("Failed to open project", str(e))

    def _handle_help(self):
        print("Help")
        
    def _handle_new_project(self):
        """Handle new project creation."""
        logger.info("Creating new project")
        try:
            self._maximize_window()
            new_project_dialog = NewProject(self)
            new_project_dialog.exec_()
        except Exception as e:
            logger.error(f"Error creating new project: {e}")
            self._show_error_message("Error creating new project", str(e))

    def _setup_default_directories(self):
        home = Path.home()

        # TODO: Use more robust default paths
        self.csv_dir_default = "/Volumes/ExtremeSSD/spines/data/altugs_data/9_morph_4t_sigma_0.3_curated/3D+oob-labels+branchID_blind/grouped_by_fov_for_napari/"
        self.img_dir_default = '/Volumes/ExtremeSSD/spines/data/altugs_data/9_morph_4t_sigma_0.3_curated/3D+oob-labels+branchID_blind/images'
        self.filepath_default = os.path.join(self.csv_dir_default, 'aid2277_Series001.csv') # "aidv853_date220321_stack0_sub12.csv") # 'date040822_stack1_sub11_timetracked.csv')

        logger.info(f"Default CSV directory: {self.csv_dir_default}")
        logger.info(f"Default image directory: {self.img_dir_default}")
        
    def _update_loaded_state(self, loaded: bool, filepath: str, img_dir: str):
        logger.info(f"Updating loaded state: loaded: {loaded}")

        self._project_loaded = loaded

        if loaded:
            # Store project info
            self.filepath = filepath
            self.img_dir = img_dir
            self.csv_dir = os.path.dirname(self.filepath)
            self.filename = os.path.basename(self.filepath)

            # Update UI
            self._update_status_display()

            self._create_tracking_interface()
    
    def _update_status_display(self):
        if self._project_loaded:
            status_text = f"✅ Project loaded: {self.filename}"

            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #27ae60;
                    padding: 15px;
                    background-color: #d5f4e6;
                    border-radius: 6px;
                    border: 1px solid #27ae60;
                }
            """)
        else:
            status_text = "No project loaded"
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #7f8c8d;
                    padding: 15px;
                    background-color: #ecf0f1;
                    border-radius: 6px;
                    border: 1px solid #bdc3c7;
                }
            """)
        
        self.status_label.setText(status_text)
    
    def _clear_all_widgets(self):
        """Remove all widgets from the main layout when switching to tracking mode."""
        # Store items to remove (avoid modifying layout while iterating)
        items_to_remove = []
        
        for i in range(self.main_layout.count()):
            item = self.main_layout.itemAt(i)
            if item and item.widget():
                items_to_remove.append(item.widget())
        
        # Remove all identified widgets
        for widget in items_to_remove:
            self.main_layout.removeWidget(widget)
            widget.deleteLater()
        
        logger.info(f"Cleared {len(items_to_remove)} widgets from main layout")
    
    def _create_tracking_interface(self):
        try:
            # Clear existing widgets from the layout
            self._clear_all_widgets()

            # Create the tracking refinement widget
            self._refine_tracking_widget = RefineTracking(self)

            # Insert the tracking widget between header and status
            self.main_layout.insertWidget(1, self._refine_tracking_widget)

            logger.info("Tracking interface created successfully")
        except Exception as e:
            logger.error(f"Error creating tracking interface: {e}")
            self._show_error_message("Error creating tracking interface", str(e))
    
    def _show_error_message(self, title: str, message: str):
        """Display an error message to the user."""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def is_project_loaded(self) -> bool:
        """Check if a project is currently loaded."""
        return self._project_loaded

if __name__ == '__main__':
    viewer = napari.Viewer()
    widget = TrackingCurationWidget(viewer)
    viewer.window.add_dock_widget(widget, name='Spine Tracking Curation')
    napari.run()