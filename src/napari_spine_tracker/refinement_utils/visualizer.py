import os, glob
import numpy as np

class TrackletVisualizer:
    def __init__(self, napari_viewer, manager, img_dir):
        print("TrackletVisualizer created")
        self.viewer = napari_viewer
        self.img_dir = img_dir
        self.manager = manager
        
        self._curr_frame = 0
        self.curr_frame = 0

        self.filenames = manager.filenames
        self.objects = manager.objects
        self.data = manager.data

        self.stack_names = np.unique([f.split('_layer')[0] for f in self.filenames])
        all_filenames = []
        for sn in self.stack_names:
            all_filenames += list(glob.glob(os.path.join(self.img_dir, f"{sn}_layer*.png")))
        self.all_filenames = sorted([os.path.basename(f) for f in all_filenames])

        if len(self.all_filenames) > 0:
            self.curr_stack = self.all_filenames[0].split('_layer')[0]
        else:
            return

        # napari multi-viewer
        # on one side, show imgs with '_t1_' in filename
        # on the other side, show imgs with '_t2_' in filename
        # self.viewer1 = self.viewer.window.add_viewer()
        # self.viewer2 = self.viewer.window.add_viewer()

        # add images as stack
