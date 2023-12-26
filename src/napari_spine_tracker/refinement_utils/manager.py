import os
import numpy as np
import pandas as pd

from qtpy.QtWidgets import (
    QPushButton,
    QHBoxLayout,
    QMessageBox
)
from qtpy import QtWidgets
from qtpy.QtCore import Qt

class TrackletManager:
    def __init__(self,
                 root_widget):
        # print("TrackletManager created")
        self.filepath = None
        self.root_widget = root_widget
        self.data = None
        self.unq_filenames = None
        self.n_frames = None

        self._create_initial_widgets()

    def _create_initial_widgets(self):
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save)
        help_btn = QPushButton("Help")
        help_btn.clicked.connect(self.help)

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
        # self.root_widget.layout.addSpacing(10)
    
    def _load_tracklets(self, df_tracklets):
        layers = [int(f.split('_layer')[1].split('.')[0]) for f in df_tracklets['filename'].values]
        df_tracklets['filename'] = [os.path.basename(f) for f in df_tracklets['filename'].values]
        self.unq_filenames = np.unique(df_tracklets['filename'].values)
        self.n_frames = len(np.unique(self.unq_filenames))
        # print(df_tracklets.shape)

    def load_tracklets_from_csv(self, datafile):
        self.filepath = datafile
        self.data = pd.read_csv(datafile)
        # self.data = self.data[self.data['filename'].str.contains('layer076') | self.data['filename'].str.contains('layer077')] # TODO: remove after testing
        self._load_tracklets(self.data)
    
    def save(self, output_name=""):
        df_tracklets = self.data
        if not output_name:
            output_name = self.filepath
        df_tracklets.to_csv(output_name, index=False)
        print(f"Saved tracklets to {output_name}")
    
    def help(self):
        # open help dialog
        dialog = QMessageBox()
        dialog.setWindowTitle("Help")
        dialog.setFixedWidth(500)
        dialog.setFixedHeight(500)

        help_text = " To change ID of 2D detection, choose selection mode, select the shape and press 'i'\n" + \
                    " To remove 2D detection, choose selection mode, select the shape and press 'backspace'\n" + \
                    " To move between frames, click on the visualizer and then use arrows left and right\n" + \
                    " To add a new detection, ... "
        dialog.setText(help_text)
        dialog.exec_()
    
    def add_new_tracklet(self, row_to_add):
        row_tracklet = pd.DataFrame(row_to_add, columns=self.data.columns)
        self.data = pd.concat([self.data, row_tracklet], ignore_index=True)
        self._load_tracklets(self.data)
    
    def remove_tracklet(self, row_to_remove):
        idx = self.data[
                (self.data['filename'] == row_to_remove['filename']) &
                (self.data['id'] == row_to_remove['id']) &
                (self.data('xmin') == row_to_remove('xmin')) &
                (self.data('ymin') == row_to_remove('ymin'))
            ].index
        self.data = self.data.drop(idx)
        self._load_tracklets(self.data)
    
    def change_id(self, row_to_change, new_id):
        idx = self.data[
                (self.data['filename'] == row_to_change['filename']) &
                (self.data['id'] == row_to_change['id']) &
                (self.data('xmin') == row_to_change('xmin')) &
                (self.data('ymin') == row_to_change('ymin'))
            ].index
        self.data.loc[idx, 'id'] = new_id

        
        