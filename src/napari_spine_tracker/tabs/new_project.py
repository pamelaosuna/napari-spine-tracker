import os
from qtpy import QtWidgets, QtGui, QtCore
import pandas as pd

class NewProject(QtWidgets.QDialog):
    def __init__(self, parent):
        super(NewProject, self).__init__(parent)
        self.parent = parent
        self.setWindowTitle("Create New Project")

        self.img_dir = self.parent.img_dir_default
        self.csv_dir = self.parent.csv_dir_default

        self.filepath = ''
        self.filename = ''
        self.loaded = False

        self.create_widgets()
    
    def create_widgets(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addStretch()

        # self.filepath_label = QtWidgets.QLabel(f"Files selected: {self.filename}", self)
        self.filepath_list = QtWidgets.QListWidget(self)
        self.filepath_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.browse_file_btn = QtWidgets.QPushButton("Select project files", self)
        self.browse_file_btn.clicked.connect(self.browse_file)

        self.img_dir_label = QtWidgets.QLabel(f"Images folder selected: {self.img_dir}", self)
        self.browse_img_dir_btn = QtWidgets.QPushButton("Select images folder", self)
        self.browse_img_dir_btn.clicked.connect(self.browse_img_dir)

        self.project_dir_label = QtWidgets.QLabel(f"Folder to save project: {self.csv_dir}", self)
        self.browse_project_dir_btn = QtWidgets.QPushButton("Select project folder", self)
        self.browse_project_dir_btn.clicked.connect(self.browse_project_dir)

        self.filename_label = QtWidgets.QLabel(f"Project name: {self.filename}", self)
        self.filename_text = QtWidgets.QLineEdit(self, placeholderText="Enter project name")
        self.filename_text.textChanged.connect(self._set_filename)

        self.ok_btn = QtWidgets.QPushButton("Create")
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self.finalize_new)
        # bind enter key to ok_btn
        self.ok_btn.setAutoDefault(True)

        main_layout.addWidget(self.filename_label)
        main_layout.addWidget(self.filename_text)
        main_layout.addWidget(self.filepath_list)
        main_layout.addWidget(self.browse_file_btn)
        main_layout.addWidget(self.img_dir_label)
        main_layout.addWidget(self.browse_img_dir_btn)
        main_layout.addWidget(self.project_dir_label)
        main_layout.addWidget(self.browse_project_dir_btn)
        main_layout.addWidget(self.ok_btn, alignment=QtCore.Qt.AlignRight)
        main_layout.addStretch()
    
    def _set_filename(self):
        self.filename = self.filename_text.text()
        if not self.filename.endswith(".csv"):
            self.filename += ".csv"
        self.filename_label.setText(f"Project name: {self.filename}")
        self.filepath = os.path.join(self.csv_dir, self.filename)

    def browse_project_dir(self):
        f = QtWidgets.QFileDialog.getExistingDirectory(
                                    self,
                                    "Select project folder",
                                    self.csv_dir,
                                    options=QtWidgets.QFileDialog.DontUseNativeDialog
                                    )
        if not f:
            return
        self.csv_dir = f
        self.filepath = os.path.join(self.csv_dir, self.filename)
        print(f"You have selected {f}")
        self.project_dir_label.setText(f"Folder to save project: {self.csv_dir}")

    def browse_file(self):
        f_ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Select project files",
            self.csv_dir,
            "Project files (*.csv)",
            options=QtWidgets.QFileDialog.DontUseNativeDialog
        )
        if not f_:
            return
        self.filepath_list.addItems(f_[0])
        for i in range(self.filepath_list.count()):
            self.filepath_list.item(i).setSelected(True)
    
    def browse_img_dir(self):
        f = QtWidgets.QFileDialog.getExistingDirectory(
                                    self,
                                    "Select images folder",
                                    self.img_dir,
                                    options=QtWidgets.QFileDialog.DontUseNativeDialog
                                    )
        if not f:
            return
        self.img_dir = f
        print(f"You have selected {f}")
        self.img_dir_label.setText(f"Images folder selected: {self.img_dir}")
    
    def merge_csv(self):
        filepaths_csv = [os.path.join(f.text()) for f in self.filepath_list.selectedItems()]
        merged_df = pd.concat([pd.read_csv(f) for f in filepaths_csv])
        merged_df.to_csv(os.path.join(self.csv_dir, self.filename), index=False)

    def finalize_new(self):
        print("Finalizing new project")
        f_ = self.filepath_list.selectedItems()
        if len(f_) == 0:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("Please select at least one project file")
            msg.setWindowTitle("Error")
            msg.exec_()
            return
        if self.filename == "" or self.img_dir == "":
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("Please enter a project name and an images folder")
            msg.setWindowTitle("Error")
            msg.exec_()
            return
    
        self.merge_csv()
        self.parent._update_loaded_state(loaded=True,
                                        filepath=self.filepath,
                                        img_dir=self.img_dir
                                        )
        msg = QtWidgets.QMessageBox(text=f"Project created successfully at {self.filepath}")
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.exec_()
        self.close()

        
        