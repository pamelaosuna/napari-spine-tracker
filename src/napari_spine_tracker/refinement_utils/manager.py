import os
import numpy as np
import pandas as pd

from qtpy.QtWidgets import (
    QPushButton,
    QHBoxLayout,
    QMessageBox
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
    
    def _load_unq_filenames(self):
        self.unq_filenames = np.unique([os.path.basename(f) for f in self.data['filename'].values])
    
    def _load_tracklets(self):
        self._load_unq_filenames()
        self.n_frames = len(np.unique(self.unq_filenames))

    def load_tracklets_from_csv(self, datafile):
        self.filepath = datafile
        self.data = pd.read_csv(datafile)
        if 'layer' in self.data.columns:
            self.data.drop(['layer'], axis=1, inplace=True)
        self._load_tracklets()
    
    def save(self, output_name=""):
        df_tracklets = self.data
        if not output_name:
            output_name = self.filepath
        df_tracklets.to_csv(output_name, index=False)
        print(f"Saved tracklets to {output_name}")
    
    def update_csv(self, updated_data):
        self.data = updated_data
        self.save()
    
    def help(self):
        # open help dialog
        dialog = QMessageBox()
        dialog.setWindowTitle("Help")
        dialog.setFixedWidth(500)
        dialog.setFixedHeight(500)

        help_text = " - To change ID of 2D detection: choose selection mode, select the shape and press 'i'\n" + \
                    " - To remove 2D detection: choose selection mode, select the shape and press 'Backspace'\n" + \
                    " - To move between frames: click on the visualizer and then use arrows 'Left' and 'Right'\n" + \
                    " - To add a new detection: choose selection mode, press 'r' and draw a new shape"
        dialog.setText(help_text)
        dialog.exec_()
    
    def add_new_tracklet(self, row_to_add):
        row_tracklet = pd.DataFrame(row_to_add, index = [0])
        self.data = pd.concat([self.data, row_tracklet], ignore_index=True)
    
    def remove_tracklet(self, row_idxs):
        self.data = self.data.drop(row_idxs)
    
    def change_id(self, idx_row, new_id):
        self.data.loc[idx_row, 'id'] = new_id
    
    def update_coords(self, img_filename, shapes_layer_data, ids):
        data_img = self.data[self.data['filename'].str.contains(img_filename.split('bboxes_')[1])]
        rows_idxs = data_img[data_img['id'].isin(ids.astype(int))].index
        ymins, xmins = np.array(shapes_layer_data).min(axis=1).T
        ymaxs, xmaxs = np.array(shapes_layer_data).max(axis=1).T
        self.data.loc[rows_idxs, 'xmin'] = xmins
        self.data.loc[rows_idxs, 'xmax'] = xmaxs
        self.data.loc[rows_idxs, 'ymin'] = ymins
        self.data.loc[rows_idxs, 'ymax'] = ymaxs

    def get_data(self):
        return self.data

    def get_unq_filenames(self):
        self._load_unq_filenames()
        return self.unq_filenames
        