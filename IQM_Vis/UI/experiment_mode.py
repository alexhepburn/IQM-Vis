'''
create experiment window
'''
# Author: Matt Clifford <matt.clifford@bristol.ac.uk>
import os

import numpy as np
from PyQt6.QtWidgets import QPushButton, QLabel, QSlider, QCheckBox, QComboBox, QLineEdit, QMessageBox
from PyQt6.QtWidgets import (QWidget,
                             QMainWindow,
                             QGridLayout,
                             QHBoxLayout,
                             QVBoxLayout,
                             QStackedLayout,
                             QTabWidget,
                             QWidget,
                             QApplication)

from PyQt6.QtGui import QIntValidator
from PyQt6.QtCore import Qt

import IQM_Vis
from IQM_Vis.UI.custom_widgets import ClickLabel
from IQM_Vis.UI import utils
from IQM_Vis.utils import gui_utils, plot_utils, image_utils


class make_experiment(QMainWindow):
    def __init__(self, checked_transformations, data_store, image_display_size):
        super().__init__()
        self.checked_transformations = checked_transformations
        self.data_store = data_store
        self.image_display_size = image_display_size
        self._init_experiment_window_widgets()
        self.experiment_layout()
        self.setCentralWidget(self.experiments_tab)
        # move to centre of the screen
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


    def closeEvent(self, event):
        # Ask for confirmation
        answer = QMessageBox.question(self,
        "Confirm Exit...",
        "Are you sure you want to exit?\nAll unsaved data will be lost.",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        event.ignore()
        if answer == QMessageBox.StandardButton.Yes:
            if hasattr(self, 'range_worker'):
                self.range_worker.stop()
            event.accept()

    def quit(self):
        self.close()

    def _init_experiment_window_widgets(self):
        self.widget_experiments = {'exp': {}, 'preamble': {}}
        ''' pre experiments screen '''
        self.widget_experiments['preamble']['text'] = QLabel(self)
        self.widget_experiments['preamble']['text'].setText(''' For this experiment you will be shown a reference image and two similar images.

        You need to click on the image (A or B) which you believe to be most similar to the reference image.


        When you are ready, click the Start button to begin the experiment ''')
        self.widget_experiments['preamble']['start_button'] = QPushButton('Start', self)
        self.running_experiment = False
        self.widget_experiments['preamble']['start_button'].clicked.connect(self.toggle_experiment)

        self.widget_experiments['exp']['quit_button'] = QPushButton('Quit', self)
        self.widget_experiments['exp']['quit_button'].clicked.connect(self.quit)

        ''' images '''
        for image in ['Reference', 'A', 'B']:
            self.widget_experiments['exp'][image] = {}
            self.widget_experiments['exp'][image]['data'] = ClickLabel(image)
            self.widget_experiments['exp'][image]['data'].setAlignment(Qt.AlignmentFlag.AlignCenter)
            # image label
            self.widget_experiments['exp'][image]['label'] = QLabel(image, self)
            self.widget_experiments['exp'][image]['label'].setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.widget_experiments['exp']['A']['data'].clicked.connect(self.clicked_image)
        self.widget_experiments['exp']['B']['data'].clicked.connect(self.clicked_image)

    def toggle_experiment(self):
        if self.running_experiment:
            self.reset_experiment()
            self.experiments_tab.setTabEnabled(0, True)
            self.running_experiment = False
            self.widget_experiments['preamble']['start_button'].setText('Start')

        else:
            self.start_experiment()
            self.experiments_tab.setTabEnabled(0, False)
            self.widget_experiments['preamble']['start_button'].setText('Reset')
            self.running_experiment = True

    def reset_experiment(self):
        self.init_style('light')

    def start_experiment(self):
        self.init_style('dark')
        self.experiments_tab.setCurrentIndex(1)
        experiment_transforms = plot_utils.get_all_single_transform_params(self.checked_transformations)

        ''' quick proto type to display some images '''
        ref = self.data_store.get_reference_image()
        gui_utils.change_im(self.widget_experiments['exp']['Reference']['data'], ref, resize=self.image_display_size)

        # get MSE for experiments to get a rough sorting
        mses = []
        mse = IQM_Vis.IQMs.MSE()
        for trans in experiment_transforms:
            mses.append(mse(ref, self.get_single_transform_im(trans)))
        # sort experiment transforms based on MSE
        self.experiment_transforms = sort_list(experiment_transforms, mses)
        self.current_pivot = self.experiment_transforms.pop(len(self.experiment_transforms)//2)
        self.current_sort_check = self.experiment_transforms[0]
        print(f'{self.current_pivot=}')

        self.change_experiment_images(A_trans=self.current_pivot, B_trans=self.current_sort_check)

    def get_single_transform_im(self, single_trans_dict):
        trans_name = list(single_trans_dict)[0]
        return image_utils.get_transform_image(self.data_store,
                                        {trans_name: self.checked_transformations[trans_name]},
                                        single_trans_dict)

    def change_experiment_images(self, A_trans, B_trans):
        A = self.get_single_transform_im(A_trans)
        B = self.get_single_transform_im(B_trans)

        gui_utils.change_im(self.widget_experiments['exp']['A']['data'], A, resize=self.image_display_size)
        self.widget_experiments['exp']['A']['data'].setObjectName(f'{self.data_store.get_reference_image_name()}-{A_trans}')
        gui_utils.change_im(self.widget_experiments['exp']['B']['data'], B, resize=self.image_display_size)
        self.widget_experiments['exp']['B']['data'].setObjectName(f'{self.data_store.get_reference_image_name()}-{B_trans}')

    def clicked_image(self, image_name, widget_name):
        print(f'clicked {widget_name}, name: {image_name}')
        trans_str = image_name[len(self.data_store.get_reference_image_name())+1:]
        if trans_str == str(self.current_sort_check): # lower value
            pass
            # now impliment

        print(trans)
        self.exp_im_ind[widget_name] += 1
        if self.exp_im_ind[widget_name] == len(self.experiment_transforms):
            self.exp_im_ind[widget_name] -= 1
        # self.change_experiment_images(A_ind=self.exp_im_ind['A'], B_ind=self.exp_im_ind['B'])

    def init_style(self, style='light', css_file=None):
        if css_file == None:
            dir = os.path.dirname(os.path.abspath(__file__))
            # css_file = os.path.join(dir, 'style-light.css')
            css_file = os.path.join(dir, f'style-{style}.css')
        if os.path.isfile(css_file):
            with open(css_file, 'r') as file:
                self.setStyleSheet(file.read())
        else:
            warnings.warn('Cannot load css style sheet - file not found')

    def experiment_layout(self):

        # info
        experiment_mode_info = QVBoxLayout()
        experiment_mode_info.addWidget(self.widget_experiments['preamble']['text'])
        experiment_mode_info.addWidget(self.widget_experiments['preamble']['start_button'])
        experiment_mode_info.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # experiment
        reference = QVBoxLayout()
        for name, widget in self.widget_experiments['exp']['Reference'].items():
            reference.addWidget(widget)
        reference.setAlignment(Qt.AlignmentFlag.AlignBottom)
        A = QVBoxLayout()
        for name, widget in self.widget_experiments['exp']['A'].items():
            A.addWidget(widget)
        A.setAlignment(Qt.AlignmentFlag.AlignTop)
        B = QVBoxLayout()
        for name, widget in self.widget_experiments['exp']['B'].items():
            B.addWidget(widget)
        B.setAlignment(Qt.AlignmentFlag.AlignTop)

        distorted_images = QHBoxLayout()
        distorted_images.addLayout(A)
        distorted_images.addLayout(B)
        distorted_images.setAlignment(Qt.AlignmentFlag.AlignTop)

        experiment_mode_images = QVBoxLayout()
        experiment_mode_images.addLayout(reference)
        experiment_mode_images.addLayout(distorted_images)
        experiment_mode_images.setAlignment(Qt.AlignmentFlag.AlignCenter)

        all_experiment = QVBoxLayout()
        all_experiment.addLayout(experiment_mode_images)
        all_experiment.addWidget(self.widget_experiments['exp']['quit_button'])
        all_experiment.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.experiments_tab = QTabWidget()
        for tab_layout, tab_name in zip([experiment_mode_info, all_experiment],
                                        ['info', 'run']):
            utils.add_layout_to_tab(self.experiments_tab, tab_layout, tab_name)
        # experiment_mode_layout = QVBoxLayout()
        # experiment_mode_layout.addWidget(self.experiments_tab)
        # return experiment_mode_layout

def sort_list(list1, list2):
    # sort list1 based on list2
    inds = np.argsort(list2)
    sorted_list1 = []
    for i in inds:
        sorted_list1.append(list1[i])
    return sorted_list1
