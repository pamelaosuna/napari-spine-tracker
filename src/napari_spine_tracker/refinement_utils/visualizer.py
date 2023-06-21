import os, glob
import numpy as np
from skimage import io
from qtpy.QtWidgets import QSplitter, QVBoxLayout
from qtpy.QtWidgets import QSplitter, QTabWidget
from qtpy.QtCore import Qt, QEvent, QObject, QItemSelection
from qtpy.QtWidgets import (
    QPushButton,
    QSlider,
    QWidget,
    QLabel,
    QCheckBox,
    QDialog,
    QLineEdit,
    QMessageBox,
    )
from qtpy.QtGui import QIcon, QIntValidator


from napari.layers import Image, Shapes
from napari.layers.shapes._shapes_constants import Mode
from napari.components.viewer_model import ViewerModel
from napari_spine_tracker.tabs.multi_view import  QtViewerWrap
from superqt import QRangeSlider

class FrameReader(QWidget):
    """
    Dummy widget showcasing how to place additional widgets to the right
    of the additional viewers.
    """
    def __init__(self, viz, viewer_model, img_dir, filenames):
        super().__init__()
        self.viz = viz
        self.viewer_model = viewer_model
        self.img_dir = img_dir
        self.filenames = filenames

        self.synchronize = False
        self.show_bboxes = False
        self.selected_rect = None

        self._prepare_reader()

    def _prepare_reader(self):
        init_frame_val = 0

        self.frame_num = init_frame_val
        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.setMinimum(0)
        self.frame_slider.setMaximum(len(self.filenames)-1)
        self.frame_slider.setValue(init_frame_val)
        self.frame_slider.valueChanged.connect(self.set_frame)

        self.frame_text = QLabel(f'Frame number: {self.frame_num}')
        self.frame_text.setAlignment(Qt.AlignCenter)
        self.fname_text = QLabel(self.filenames[self.frame_num])
        self.fname_text.setAlignment(Qt.AlignLeft)
        self.fname_text.setStyleSheet("font: 10pt")

        self.show_bboxes_checkbox = QCheckBox('Show Bounding Boxes')
        self.show_bboxes_checkbox.setChecked(self.show_bboxes)
        self.show_bboxes_checkbox.stateChanged.connect(self.show_bboxes_in_frame)

        self.contrast_range_slider = QRangeSlider(Qt.Orientation.Horizontal, self)
        self.contrast_range_slider.valueChanged.connect(self._set_contrast_limits)

        layout = QVBoxLayout()
        for w in [self.fname_text, self.frame_text, self.frame_slider, self.show_bboxes_checkbox, self.contrast_range_slider]:
            layout.addWidget(w)
        layout.addStretch(1)
        self.setLayout(layout)

        self._add_init_images()
        self.viewer_model.layers[init_frame_val].visible = True

        # self._add_mouse_callbacks(self.viewer_model)

    def set_frame(self, frame):
        for layer in self.viewer_model.layers:
            layer.visible = False
        self.viewer_model.layers[frame].visible = True
        self.frame_slider.setValue(frame)
        self.frame_text.setText(f'Frame number: {frame}')
        self.fname_text.setText(self.filenames[frame])
        self.frame_num = frame
        self.show_bboxes_in_frame()
        self._set_contrast_limits(self.contrast_range_slider.value())
        self.viz._make_unselectable(self.viewer_model)
        if self.viz.selection_mode.isChecked():
            self.viz.selection_mode.setChecked(False)
        # if self.selected_rect is not None:
        #     self.deselect_rect(self.selected_rect)

    def _add_init_images(self):
        print(f'Adding {len(self.filenames)} images to viewer')
        imgs = []
        for fn in self.filenames:
            img = io.imread(os.path.join(self.img_dir, fn))
            imgs.append(img)
            self.viewer_model.add_image(img, name=fn)
            self.viewer_model.layers[fn].visible = False

        imgs = np.array(imgs)
        max_val = np.max(imgs)
        max_val_bin = bin(max_val)[2:]
        max_val_bin_len = len(max_val_bin)

        # set contrast limits to be 0 and 2^max_val_bin_len
        self.contrast_range_slider.setRange(0, 2**max_val_bin_len)
        self.contrast_range_slider.setValue([0, 2**max_val_bin_len])

    def update_synchronize(self):
        self.synchronize = not(self.synchronize)

    def _set_contrast_limits(self, values):
        cmin, cmax = values
        self.viewer_model.layers[self.filenames[self.frame_num]].contrast_limits = (cmin, cmax)

    def show_bboxes_in_frame(self):
        if self.show_bboxes_checkbox.isChecked():
            # make invisible all bboxes except for the ones in the current frame
            for layer in self.viewer_model.layers:
                if 'bbox_' in layer.name:
                    if layer.name.split('_')[1].split('_')[0] == str(self.frame_num):
                        layer.visible = True
                    else:
                        layer.visible = False
        else:
            for layer in self.viewer_model.layers:
                if 'bbox_' in layer.name:
                    layer.visible = False
    
    def deselect_rect(self, rect_name):
        self.viewer_model.layers[rect_name].mode = Mode.PAN_ZOOM
        # self.viewer_model.layers[rect_name].selected = False
        # self.viewer_model.layers[rect_name].edge_width = 1
        self.selected_rect = None
    
    def select_rect(self, rect_name):
        self.viewer_model.layers[rect_name].mode = Mode.SELECT
        # self.viewer_model.layers[rect_name].selected = True
        # self.viewer_model.layers[rect_name].edge_width = 3
        self.selected_rect = rect_name
    
    def _add_mouse_callbacks(self, viewer):
        @viewer.mouse_drag_callbacks.append
        def toggle_select(viewer, event):
            if not self.show_bboxes_checkbox.isChecked() or self.viz.selection_mode.isChecked():
                return
            if event.button == 1 and self.viz.selection_mode.isChecked():
                print('mouse callback')
                # if self.selected_rect is None:
                #     # get visible layers and check if mouse is in any of them
                #     visible_rects = [layer for layer in viewer.layers if layer.visible and 'bbox_' in layer.name]
                #     y_mouse, x_mouse = event.position
                #     for layer in visible_rects:
                #         # layer.data example: [array([[345., 231.],[345., 249.],[363., 249.],[363., 231.]])]
                #         ymin, xmin = layer.data[0][0]
                #         ymax, xmax = layer.data[0][2]
                #         if x_mouse > xmin and x_mouse < xmax and y_mouse > ymin and y_mouse < ymax:
                #             print('mouse in bbox, yay!')
                #             self.select_rect(layer.name)
                #             break
                # else:
                #     self.deselect_rect(self.selected_rect)

                self.viz.update_selected_rect(self.selected_rect)


class IdChanger(QDialog):
    def __init__(self, parent=None, viz=None):
        super(IdChanger, self).__init__(parent, viz)
        self.setWindowTitle("Change ID")
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(200, 100)

        self._prepare_dialog()

    def _prepare_dialog(self):
        main_layout = QVBoxLayout()
        self.text_id = QLineEdit()
        self.text_id.setPlaceholderText("Enter new ID")
        self.text_id.setValidator(QIntValidator())
        self.text_id.returnPressed.connect(self._change_id)
        # use Esc to cancel
        self.text_id.keyPressEvent = lambda event: self.close() if event.key() == Qt.Key_Escape else None
        main_layout.addWidget(self.text_id)
        self.setLayout(main_layout)
    
    def _change_id(self):
        new_id = self.text_id.text()
        print(f'Changing ID to {new_id}')
        # self.viz.update_id_selected_rect(new_id)
        self.close()


class TrackletVisualizer:
    def __init__(self, 
                 root_plugin_widget, 
                 manager, 
                 img_dir,
                 filter_t1=None,
                 filter_t2=None
                 ):
        print("TrackletVisualizer created")
        self.root_widget = root_plugin_widget
        self.img_dir = img_dir
        self.manager = manager
        
        self.synchronize = False # synchronize frame slider across viewers

        self.unq_filenames = manager.unq_filenames
        # self.objects = manager.objects
        self.data = manager.data
        self.selected_rect = None

        self.stack_names = np.unique([f.split('_layer')[0] for f in self.unq_filenames])
        all_filenames = []
        for sn in self.stack_names:
            all_filenames += list(glob.glob(os.path.join(self.img_dir, f"{sn}_layer*.png")))
        self.all_filenames = sorted([os.path.basename(f) for f in all_filenames])
        self.filenames_t1 = [f for f in self.all_filenames if filter_t1 in f]
        self.filenames_t2 = [f for f in self.all_filenames if filter_t2 in f]
        # self.filenames_t1 = ["aidv853_date220321_tp1_stack0_sub11_layer076.png"] # TODO: remove after testing
        # self.filenames_t2 = ["aidv853_date220321_tp2_stack0_sub11_layer076.png"] # TODO: remove after testing

        if len(self.all_filenames) > 0:
            self.curr_stack = self.all_filenames[0].split('_layer')[0]
        else:
            return
        
        self._prepare_visualizer()
        self._add_init_bboxes()

        # bind key press 'i' to _change_id()
        for vm in [self.viewer_model1, self.viewer_model2]:
            vm.bind_key('i', self._change_id)

    def _prepare_visualizer(self):
        self.viewer_model1 = ViewerModel(title="model1")
        self.viewer_model2 = ViewerModel(title="model2")
        self.qt_viewer1 = QtViewerWrap(self.root_widget.viewer, self.viewer_model1)
        self.qt_viewer2 = QtViewerWrap(self.root_widget.viewer, self.viewer_model2)
        self.frame_reader1 = FrameReader(self, self.viewer_model1, self.img_dir, self.filenames_t1)
        self.frame_reader2 = FrameReader(self, self.viewer_model2, self.img_dir, self.filenames_t2)
        
        toolbar_splitter = QSplitter()
        toolbar_splitter.setOrientation(Qt.Horizontal)
        toolbar_splitter.addWidget(self.frame_reader1)
        toolbar_splitter.addWidget(self.frame_reader2)
        toolbar_splitter.setContentsMargins(0, 0, 0, 0)
        
        viewer_splitter = QSplitter()
        viewer_splitter.setOrientation(Qt.Horizontal)
        viewer_splitter.addWidget(self.qt_viewer1)
        viewer_splitter.addWidget(self.qt_viewer2)
        viewer_splitter.setContentsMargins(0, 0, 0, 0)

        self.sync_checkbox = QCheckBox("Synchronize frame number")
        self.sync_checkbox.stateChanged.connect(self._toggle_synchronize)
        self.sync_checkbox.setChecked(False)

        self.selection_mode = QCheckBox("Selection mode")
        self.selection_mode.stateChanged.connect(self._toggle_selection_mode)
        self.selection_mode.setChecked(False)

        self.root_widget.layout.addWidget(viewer_splitter)
        self.root_widget.layout.setSpacing(0)
        self.root_widget.layout.addWidget(self.sync_checkbox, alignment=Qt.AlignCenter)
        self.root_widget.layout.addWidget(self.selection_mode, alignment=Qt.AlignCenter)
        self.root_widget.layout.addWidget(toolbar_splitter)
    
    def _toggle_synchronize(self, state):
        self.synchronize = not(self.synchronize)
        self.frame_reader1.update_synchronize()
        self.frame_reader2.update_synchronize()
        if state == Qt.Checked:
            self.frame_reader1.frame_slider.valueChanged.connect(self.frame_reader2.set_frame)
            self.frame_reader2.frame_slider.valueChanged.connect(self.frame_reader1.set_frame)
        else:
            self.frame_reader1.frame_slider.valueChanged.disconnect(self.frame_reader2.set_frame)
            self.frame_reader2.frame_slider.valueChanged.disconnect(self.frame_reader1.set_frame)
    
    def _toggle_selection_mode(self, state):
        if state == Qt.Checked:
            for vm, fr in zip([self.viewer_model1, self.viewer_model2], [self.frame_reader1, self.frame_reader2]):
                if fr.show_bboxes_checkbox.isChecked():
                    # make all bboxes in the current frame selectable
                    self._make_selectable(vm)
        else:
            for vm in [self.viewer_model1, self.viewer_model2]:
                self._make_unselectable(vm)
        
    def _make_selectable(self, viewer_model):
        layer_names = [layer.name for layer in viewer_model.layers if layer.visible and 'bbox' in layer.name]
        for ln in layer_names:
            bbox = viewer_model.layers[ln]
            bbox.mode = Mode.SELECT
            # bring bbox to front when selectable
            bbox.move_to_front()
            # bbox.selected = False
            # bbox.events.selected.connect(self._on_bbox_selected)
    
    def _make_unselectable(self, viewer_model):
        for layer in viewer_model.layers:
            if 'bbox' in layer.name:
                layer.mode = Mode.PAN_ZOOM

    
    def _on_bbox_selected(self, event):
        if event.source.selected:
            self.selected_rect = event.source
        else:
            self.selected_rect = None

    def _add_init_bboxes(self):
        text_params = {
                    'string': 'id',
                    'size': 8,
                    'color': 'red',
                    'anchor': 'upper_left',
                    'translation': [-1, 1],
                }
        for frame_num in range(len(self.filenames_t1)):
            objs_t1 = self.data[self.data['filename'].str.contains(self.filenames_t1[frame_num])]
            for i, row in objs_t1.iterrows():
                xmin, ymin, xmax, ymax = row[['xmin', 'ymin', 'xmax', 'ymax']]
                bbox_rect = [[ymin, xmin], [ymin, xmax], [ymax, xmax], [ymax, xmin]]
                id = row['id']
                feats = {
                    'id': [str(id)],
                }
                c = 'red' if str(row['class']) == 'spine' else 'green'
                text_params['color'] = c
                self.viewer_model1.add_shapes(bbox_rect,
                                       features=feats,
                                       shape_type='rectangle',
                                       edge_color=c,
                                       face_color='transparent',
                                       name=f'bbox_{frame_num}_{id}_frame1',
                                       visible=False,
                                       text=text_params,
                                       )

            objs_t2 = self.data[self.data['filename'].str.contains(self.filenames_t2[frame_num])]
            for i, row in objs_t2.iterrows():
                xmin, ymin, xmax, ymax = row[['xmin', 'ymin', 'xmax', 'ymax']]
                bbox_rect = [[ymin, xmin], [ymin, xmax], [ymax, xmax], [ymax, xmin]]
                id = row['id']
                feats = {
                    'id': [str(id)],
                }
                c = 'red' if str(row['class']) == 'spine' else 'green'
                text_params['color'] = c
                self.viewer_model2.add_shapes(bbox_rect,
                                       features=feats,
                                       shape_type='rectangle',
                                       edge_color=c,
                                       face_color='transparent',
                                       name=f'bbox_{frame_num}_{id}_frame2',
                                       visible=False,
                                       text=text_params,
                                       )
    
    def update_selected_rect(self, layer_name):
        map_fr = {
            '_frame1': self.frame_reader1,
            '_frame2': self.frame_reader2,
        }
        if self.selected_rect is not None and layer_name is not None:
            frame_selected = self.selected_rect[-7:]
            frame_to_select = layer_name[-7:]

            map_fr[frame_selected].deselect_rect(self.selected_rect)
            # map_fr[frame_to_select].select_rect(layer_name)
            self.selected_rect = layer_name
        else:
            self.selected_rect = layer_name
                
    def _change_id(self):
        if self.selected_rect is None:
            print('No rectangle selected')
            return
        change_id_dialog = IdChanger(viz=self)
        change_id_dialog.show()
        # change id in data
    
    # def update_id_selected_rect(self, new_id):
    #     # find the row to modify in viz.data and set the new id
    #     frame_num, id = self.selected_rect.split('_')[1:3]
    #     frame_reader = self.frame_reader1 if self.selected_rect.endswith('_frame1') else self.frame_reader2
    #     filename = frame_reader.filenames[frame_num]





        


            


        
