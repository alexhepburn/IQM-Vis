import os
import glob
import numpy as np
import torch
import IQM_VIS
from DISTS_pytorch import DISTS

from PIL import Image
from PIL.TiffTags import TAGS


'''DISTS metric'''
class dists_wrapper:
    def __init__(self):
        self.metric = DISTS()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.metric.to(self.device)
        self.preproccess_function = IQM_VIS.metrics.preprocess_numpy_image

    def __call__(self, im_ref, im_comp, **kwargs):
        IQM_VIS.metrics.check_shapes(im_ref, im_comp)
        im_ref = self.preproccess_function(im_ref).to(device=self.device, dtype=torch.float)
        im_comp = self.preproccess_function(im_comp).to(device=self.device, dtype=torch.float)
        _score = self.metric(im_ref, im_comp)
        score = _score.cpu().detach().numpy()
        return score

'''Textures calibrated image loader'''
def load_and_calibrate_image(file, max_luminance=200, size=256):
    # Calculate max luminance value in the whole dataset
    img = Image.open(file)
    meta_dict = {TAGS[key] : img.tag[key] for key in img.tag_v2}
    img = np.array(img).astype(np.float64)
    lms = correct(img, meta_dict)

    # Get each point in rgb space to visualise the colour in RGB
    # XYZ -> LMS
    Mxyzlms = np.array([ # Bradford LMS transform
        [0.8951000, 0.2664000, -0.1614000],
        [-0.7502000, 1.7135000, 0.0367000],
        [0.0389000, -0.0685000, 1.0296000]])
    # LMS -> XYZ
    Mlmsxyz = np.linalg.inv(Mxyzlms)

    # RGB -> XYZ
    Mng2xyz = np.array([[69.1661, 52.4902, 46.6052],
                        [39.0454, 115.8404, 16.3118],
                        [3.3467, 12.6700, 170.1090]])
    #XYZ -> RGB
    Mxyz2ng = np.linalg.inv(Mng2xyz)

    # Convert LMS -> XYZ and scale values for max luminance default: 200 cd/m^2
    xyz_corrected = (lms @ Mlmsxyz.T)/np.max(lms[:, 0]) * max_luminance

    # Convert XYZ -> RGB
    rgb_corrected = np.clip(xyz_corrected @ Mxyz2ng.T, 0.0, 1.0)
    rgb_small = IQM_VIS.utils.resize_to_longest_side(rgb_corrected, side=size)
    return rgb_small

''' util for calibrating images'''
# camera correction and coversation into LMS colourspace
def correct(img, meta_dict, greycale=True):
    if 'merry' in meta_dict['ImageDescription'][0]:
        T = np.array([
            [0.428443253, 0.495562896, 0.075993851],
            [0.243026144, 0.614128681, 0.142845175],
            [0.155766424, 0.132343175, 0.711890401]])
        a_R = 7.320565961
        a_G = 12.0579051
        a_B = 10.6112984
        b = 1.008634316
    elif 'pippi' in meta_dict['ImageDescription'][0]:
        T = np.array([
            [0.431088433, 0.494438389, 0.074473178],
            [0.245488691, 0.614786761, 0.139724548],
            [0.166472303, 0.124487321, 0.709040376]])
        a_R = 5.562441185
        a_G = 8.876002262
        a_B = 7.233814813
        b = 1.009696031
    II = np.zeros_like(img)
    II[:, :, 0] = a_R*(b**img[:, :, 0]-1)
    II[:, :, 1] = a_G*(b**img[:, :, 1]-1)
    II[:, :, 2] = a_B*(b**img[:, :, 2]-1)
    exposure_time = meta_dict['ImageDescription'][0].split('-')[-1]
    try:
        exposure_time = np.float64(exposure_time)
    except:
        return None
    II = II / np.float64(exposure_time)
    II = np.reshape(np.reshape(II, (np.prod(II.shape[0:2]), 3), order='F')@T.T, (II.shape), order='F')
    return II

def run():
    # metrics functions must return a single value
    metric = {'DISTS': dists_wrapper(),
              'MAE': IQM_VIS.metrics.MAE,
              '1-SSIM': IQM_VIS.metrics.ssim()}

    # metrics images return a numpy image - dont include any for this example
    metric_images = {}

    # make dataset list of images
    files = glob.glob('/home/matt/datasets/Textures/*')
    data = IQM_VIS.dataset_holder(files,
                                  load_and_calibrate_image,
                                  metric,
                                  metric_images)

    # define the transformations
    transformations = {
               'rotation':{'min':-180, 'max':180, 'function':IQM_VIS.transforms.rotation},    # normal input
               'blur':{'min':1, 'max':41, 'normalise':'odd', 'function':IQM_VIS.transforms.blur},  # only odd ints
               'brightness':{'min':-1.0, 'max':1.0, 'function':IQM_VIS.transforms.brightness},   # normal but with float
               # 'threshold':{'min':-40, 'max':40, 'function':IQM_VIS.transforms.binary_threshold},
               # 'jpeg compression':{'init_value':100, 'min':1, 'max':100, 'function':IQM_VIS.transforms.jpeg_compression},
               }
    # define any parameters that the metrics need (names shared across both metrics and metric_images)
    ssim_params = {'sigma': {'min':0.25, 'max':5.25, 'init_value': 1.5},  # for the guassian kernel
                   # 'kernel_size': {'min':1, 'max':41, 'normalise':'odd', 'init_value': 11},  # ignored if guassian kernel used
                   'k1': {'min':0.01, 'max':0.21, 'init_value': 0.01},
                   'k2': {'min':0.01, 'max':0.21, 'init_value': 0.03}}

    # use the API to create the UI
    IQM_VIS.make_UI(data,
                transformations,
                metrics_avg_graph=True,
                metric_params=ssim_params)


if __name__ == '__main__':
    run()
