import os
import numpy as np
import pandas as pd

from qtpy.QtWidgets import (
    QPushButton,
    QHBoxLayout
)
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

        save_btn.setFixedHeight(50)
        save_btn.setFixedWidth(200)
        save_btn.setStyleSheet("font-size: 20px;")
        self.root_widget.layout.addWidget(save_btn, alignment=Qt.AlignCenter)
        self.root_widget.layout.addSpacing(20)
    
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
    
    def save(self, output_name="", *args):
        df_tracklets = self.data
        if not output_name:
            output_name = self.filepath
        df_tracklets.to_csv(output_name, index=False)
        print(f"Saved tracklets to {output_name}")
    
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

        
        