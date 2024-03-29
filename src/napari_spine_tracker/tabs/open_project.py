import os
from qtpy import QtWidgets, QtGui, QtCore

class OpenProject(QtWidgets.QDialog):
    def __init__(self, parent):
        super(OpenProject, self).__init__(parent)
        self.parent = parent
        self.setWindowTitle("Load Existing Project")

        self.filename = ""
        self.filepath = ""
        self.ims_dir = self.parent.ims_dir_default
        self.csv_dir = self.parent.csv_dir_default

        self.loaded = False

        self.create_widgets()

    def create_widgets(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addStretch()

        self.filepath_label = QtWidgets.QLabel(f"File selected: {self.filename}", self)
        self.browse_file_btn = QtWidgets.QPushButton("Select project file", self)
        self.browse_file_btn.clicked.connect(self.browse_file)

        self.ims_dir_label = QtWidgets.QLabel(f"Images folder selected: {self.ims_dir}", self)
        self.browse_ims_dir_btn = QtWidgets.QPushButton("Select images folder", self)
        self.browse_ims_dir_btn.clicked.connect(self.browse_ims_dir)

        self.ok_btn = QtWidgets.QPushButton("Load")
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self.finalize_open)

        main_layout.addWidget(self.filepath_label)
        main_layout.addWidget(self.browse_file_btn)
        main_layout.addWidget(self.ims_dir_label)
        main_layout.addWidget(self.browse_ims_dir_btn)
        main_layout.addWidget(self.ok_btn, alignment=QtCore.Qt.AlignRight)
        main_layout.addStretch()
        
    def browse_file(self):
        f = QtWidgets.QFileDialog.getOpenFileName(
                                    self, 
                                    "Select project file", 
                                    self.csv_dir, 
                                    "Project files (*.csv)",
                                    options=QtWidgets.QFileDialog.DontUseNativeDialog
                                    )
        if not f:
            return
        self.filepath = f[0]
        print(f"You have selected {f}")
        self.csv_dir = os.path.dirname(self.filepath)
        self.filename = os.path.basename(self.filepath)

        self.filepath_label.setText(f"File selected: {self.filename}")
    
    def browse_ims_dir(self):
        f = QtWidgets.QFileDialog.getExistingDirectory(
                                    self,
                                    "Select images folder",
                                    self.ims_dir,
                                    options=QtWidgets.QFileDialog.DontUseNativeDialog
                                    )
        if not f:
            return
        self.ims_dir = f
        print(f"You have selected {f}")
        self.ims_dir_label.setText(f"Images folder selected: {self.ims_dir}")
    
    def finalize_open(self):
        print("Finalizing open")
        if self.filepath == "":
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("No project file selected")
            msg.setInformativeText("Please select a project file")
            msg.setWindowTitle("Error")
            msg.exec_()
            return
        if self.ims_dir == "":
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("No images folder selected")
            msg.setInformativeText("Please select an images folder")
            msg.setWindowTitle("Error")
            msg.exec_()
            return
        self.parent._update_project_state(loaded=True, 
                                          filepath=self.filepath, 
                                          ims_dir=self.ims_dir
                                          )
        msg = QtWidgets.QMessageBox(text=f"Project loaded successfully from {self.filepath}")
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.exec_()
        self.close()
        

