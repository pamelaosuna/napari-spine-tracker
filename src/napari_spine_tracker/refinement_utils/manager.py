import os
import numpy as np
import pandas as pd

from qtpy.QtWidgets import (
    QPushButton,
    QHBoxLayout
)

class TrackletManager:
    def __init__(self,
                 root_widget):
        print("TrackletManager created")
        self.filepath = None
        self.root_widget = root_widget
        # self.filename = None
        self.data = None
        self.objects = None
        self._objects = None
        self.filenames = None
        self.n_frames = None

        self._create_initial_widgets()

    def _create_initial_widgets(self):
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save)

        self.root_widget.layout.addWidget(self.save_btn)

    
    def _load_tracklets(self, df_tracklets):
        objs = df_tracklets[['xmin', 
                            'ymin', 
                            'xmax', 
                            'ymax', 
                            'score',
                            'id',
                            'filename',
                            ]].values
        layers = [int(f.split('_layer')[1].split('.')[0]) for f in objs[:, -1]]
        objs = np.concatenate([objs, np.expand_dims(layers, axis=1)], axis=1)
        objs[:, -2] = [os.path.basename(f) for f in objs[:, -2]]
        self.filenames = np.unique(objs[:, -2])
        self.objects = objs
        self.n_frames = len(np.unique(self.filenames))
        print(objs.shape)

    def load_tracklets_from_csv(self, datafile):
        self.filepath = datafile
        self.data = pd.read_csv(datafile)
        self._load_tracklets(self.data)
        self._objects = self.objects.copy()
    
    def save(self, output_name="", *args):
        df_tracklets = self.data
        if not output_name:
            output_name = self.filepath
        df_tracklets.to_csv(output_name, index=False)
        print(f"Saved tracklets to {output_name}")


        
        