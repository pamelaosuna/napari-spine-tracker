from qtpy.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLineEdit, QDialog, QMessageBox
from qtpy.QtCore import Qt

import os

from napari_spine_tracker.refinement_utils.manager import TrackletManager, DetectionManager
from napari_spine_tracker.refinement_utils.multi_viewer import MultiViewer, SingleViewer

def refine_detections(root_widget,
                      datafile,
                      img_dir):
    manager = DetectionManager(root_widget)
    if datafile.endswith(".csv"):
        manager.load_tracklets_from_csv(datafile)
    else:
        print("File type not supported, please select a .csv file")
        return None
    viz = SingleViewer(root_widget,
                        manager, 
                        img_dir,
                        detection_refinement=True,
                        )
    return manager, viz

def refine_time_tracklets(root_widget,
                         datafile, 
                         img_dir, 
                         filter_t1, 
                         filter_t2
                         ):
    manager = TrackletManager(root_widget)
    if datafile.endswith(".csv"):
        manager.load_tracklets_from_csv(datafile)
    else:
        print("File type not supported, please select a .csv file")
        return None
    
    viz = MultiViewer(root_widget, 
                    manager, 
                    img_dir, 
                    filter_t1, 
                    filter_t2
                    )

    return manager, viz

def refine_depth_tracklets(root_widget,
                          datafile,
                          img_dir):
    manager = TrackletManager(root_widget)
    if datafile.endswith(".csv"):
        manager.load_tracklets_from_csv(datafile)
    else:
        print("File type not supported, please select a .csv file")
        return None
    viz = SingleViewer(root_widget, 
                        manager, 
                        img_dir
                        )

    return manager, viz

class TimepointSetter(QDialog):
    def __init__(self, parent):
        super(TimepointSetter, self).__init__(parent)
        self.parent = parent
        self.setWindowTitle("Set timepoint filters")

        self.create_widgets()

        print("Setting timepoint filters")
    
    def _set_filter_t1(self):
        self.parent.filter_t1 = self.text_filter_t1.text()
    
    def _set_filter_t2(self):
        self.parent.filter_t2 = self.text_filter_t2.text()

    def create_widgets(self):
        main_layout = QVBoxLayout(self)
        main_layout.addStretch()

        self.text_filter_t1 = QLineEdit()
        self.text_filter_t2 = QLineEdit()
        self.text_filter_t1.setPlaceholderText("Filter by timepoint 1, e.g. _tp1_")
        self.text_filter_t2.setPlaceholderText("Filter by timepoint 2, e.g. _tp2_")
        self.text_filter_t1.textChanged.connect(self._set_filter_t1)
        self.text_filter_t2.textChanged.connect(self._set_filter_t2)
        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.close_dialog)

        main_layout.addWidget(self.text_filter_t1)
        main_layout.addWidget(self.text_filter_t2)
        main_layout.addWidget(ok_btn)
    
    def close_dialog(self):
        if self.parent.filter_t1 is None or self.parent.filter_t2 is None:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Please enter timepoints to filter images by")
            msg.setWindowTitle("Error")
            msg.exec_()
            return
        self.close()

class RefineTracking(QWidget):
    def __init__(self, root):
        super(RefineTracking, self).__init__(root)
        print("Created RefineTracking widget")

        self.root = root
        self.filter_t1 = "_tp1_" # default
        self.filter_t2 = "_tp2_" # default
        self.tracked_axis = None # time or depth
        self.launched = False
        self._set_page()

    @property
    def filepath(self):
        return os.path.join(self.root.csv_dir, self.root.filename)

    @property
    def img_dir(self):
        return self.root.img_dir
    
    def _set_page(self):
        launch_detection_btn = QPushButton("Launch detection refinement")
        launch_detection_btn.clicked.connect(self._launch_refinement_detection)

        launch_depthtracking_btn = QPushButton("Launch depth-tracking refinement")
        launch_depthtracking_btn.clicked.connect(self._launch_refinement_across_depth)

        launch_timetracking_btn = QPushButton("Launch time-tracking refinement")
        launch_timetracking_btn.clicked.connect(self._launch_refinement_across_time)

        set_tp_filters_btn = QPushButton("Set timepoint filters")
        set_tp_filters_btn.clicked.connect(self._set_tp_filters)
       
        for btn in [launch_detection_btn, launch_depthtracking_btn, 
                    launch_timetracking_btn, set_tp_filters_btn]:
            btn.setFixedHeight(50)
            btn.setFixedWidth(350)
            btn.setStyleSheet("font-size: 20px;")
            self.root.layout.addWidget(btn, alignment=Qt.AlignCenter)
            
    def _set_tp_filters(self):
        setting_timepoints = TimepointSetter(self)
        setting_timepoints.show()

    def _launch_refinement_across_time(self):
        print("Launching refinement")
        datafile = self.filepath
        img_dir = self.img_dir
        if self.filter_t1 is None or self.filter_t2 is None:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Please enter timepoints to filter images by")
            msg.setWindowTitle("Error")
            msg.exec_()
            return

        self._update_launched_state(True)
        self.manager, self.viz = refine_time_tracklets(self.root,
                                                      datafile,
                                                      img_dir,
                                                      self.filter_t1,
                                                      self.filter_t2)

    def _launch_refinement_across_depth(self):
        print("Launching refinement")
        datafile = self.filepath
        img_dir = self.img_dir
        
        self._update_launched_state(True)
        self.manager, self.viz = refine_depth_tracklets(self.root,
                                                       datafile,
                                                       img_dir)
    
    def _launch_refinement_detection(self):
        print("Launching refinement")
        datafile = self.filepath
        img_dir = self.img_dir
        
        self._update_launched_state(True)
        self.manager, self.viz = refine_detections(self.root,
                                                    datafile,
                                                    img_dir)
    
    def _update_launched_state(self, launched):
        print("Updating viewer state")
        self.launched = launched

        if launched:
            for _ in range(3):
                self.root.layout.removeWidget(self.root.layout.itemAt(0).widget())
        





