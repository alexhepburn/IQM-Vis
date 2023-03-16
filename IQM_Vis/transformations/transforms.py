'''
Sample image transformations to get the user started with
'''
# Author: Matt Clifford <matt.clifford@bristol.ac.uk>
from skimage.transform import resize, rotate
from skimage.util import img_as_ubyte
import cv2
import numpy as np


def rotation(image, angle=0):
    '''Rotate an image around its centre. Uses skimage.transform.rotate. Areas
    that are rotated beyond the image are filled in with black pixel values

    Args:
        image (np.array): image to be rotated
        angle (float): amount of rotation in degrees (Defaults to 0)

    Returns:
        image (np.array): rotated image
    '''
    return rotate(image, angle)

def blur(image, kernel_size=7):
    '''Gaussian Blur on an image

    Args:
        image (np.array): image to be rotated
        kernel_size (int): size of the convolutional kernel, will be converted
                           to an odd number. (Defaults to 7)

    Returns:
        image (np.array): rotated image
    '''
    if kernel_size == 1:
        return image
    elif kernel_size > 0:
        blur_odd = (int(kernel_size/2)*2) + 1    # need to make kernel size odd
        image = cv2.GaussianBlur(image,(blur_odd, blur_odd), cv2.BORDER_DEFAULT)
        if len(image.shape) == 2:
            image = np.expand_dims(image, axis=2)
    return image
#
def _zoom(image, param):
    return zoom_image(image, param)

def x_shift(image, x_shift=0):
    '''Translate image horizontally

    Args:
        image (np.array): image to be shifted
        x_shift (float): shift proportion of the image in the range (-1, 1).
                         (Defaults to 0)

    Returns:
        image (np.array): shifted image
    '''
    return _translate_image(image, x_shift, 0)

def y_shift(image, y_shift=0):
    '''Translate image vertically

    Args:
        image (np.array): image to be shifted
        y_shift (float): shift proportion of the image in the range (-1, 1).
                         (Defaults to 0)

    Returns:
        image (np.array): shifted image
    '''
    return _translate_image(image, 0, y_shift)

def brightness(image, value=0):
    '''Adjust image brightness. Image is clipped to the range (0, 1)

    Args:
        image (np.array): image to have its brightness adjusted
        value (float): value to adjust all pixels by in the range (-1, 1).
                         (Defaults to 0)

    Returns:
        image (np.array): adjusted image
    '''
    return np.clip(image + value, 0, 1)

def _translate_image(image, x_shift, y_shift):
    ''' x and y shift in range (-1, 1)'''
    if x_shift == 0 and y_shift == 0:
        return image
    original_size = image.shape
    canvas = np.zeros(original_size, dtype=image.dtype)
    prop_x = int(original_size[1]*abs(x_shift))
    prop_y = int(original_size[0]*abs(y_shift))
    if original_size[1] - prop_x < 1 or original_size[0] - prop_y < 1: # make sure we dont go off the canvas
        return canvas
    if y_shift >= 0 and x_shift >= 0:
        canvas[prop_y:,prop_x:,:] = image[:original_size[0]-prop_y,:original_size[1]-prop_x,:]
    elif y_shift < 0 and x_shift >= 0:
        canvas[:original_size[0]-prop_y,prop_x:,:] = image[prop_y-original_size[0]:,:original_size[1]-prop_x,:]
    elif y_shift >= 0 and x_shift < 0:
        canvas[prop_y:,:original_size[1]-prop_x,:] = image[:original_size[0]-prop_y,prop_x-original_size[1]:,:]
    elif y_shift < 0 and x_shift < 0:
        canvas[:original_size[0]-prop_y:,:original_size[1]-prop_x,:] = image[prop_y-original_size[0]:,prop_x-original_size[1]:,:]
    return canvas

def zoom_image(image, scale_factor=1):
    '''digital zoom of image

    Args:
        image (np.array): image to be zoomed
        scale_factor (float): the percentage to zoom in by (for square zoom only).
                              0.5  = 2x zoom out
                              1 = normal size
                              2 = 2x zoom in
                              (Defaults to 1)

    Returns:
        image (np.array): zoomed image
    '''
    original_size = image.shape
    new_size_x = int(original_size[0]/scale_factor)
    new_size_y = int(original_size[1]/scale_factor)
    if scale_factor > 1:
        start_point_x = int((original_size[0] - new_size_x)/2)
        start_point_y = int((original_size[1] - new_size_y)/2)
        image = image[start_point_x:start_point_x+new_size_x,
                      start_point_y:start_point_y+new_size_y,
                      :]
    elif scale_factor < 1:
        new_size = (new_size_x, new_size_y, original_size[2]) if len(original_size) == 3 else (new_size_x, new_size_y)
        start_point_x = int((new_size_x - original_size[0])/2)
        start_point_y = int((new_size_y - original_size[1])/2)
        zoomed_out = np.zeros(new_size, dtype=image.dtype)
        zoomed_out[start_point_x:start_point_x+original_size[0],
                   start_point_y:start_point_y+original_size[1],
                   :] = image
        image = zoomed_out

    return resize(image, original_size)

def binary_threshold(image, threshold=100):
    '''conver image to binary at a given threshold

    Args:
        image (np.array): image to be thresholded
        threshold (int): threshold value in the range (1, 255)
                     (Defaults to 100)

    Returns:
        image (np.array): thresholded image (float32 in range 0, 1)
    '''
    image = img_as_ubyte(image)
    if len(image.shape) > 2:
        if image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, int(threshold))
    if len(image.shape) == 2:
        image = image[..., np.newaxis]
    return image.astype(np.float32) / 255.0

def jpeg_compression(image, compression=90):
    '''encode image using jpeg then decode

    Args:
        image (np.array): image to be compressed
        compression (int): amount of jpeg compression. 100 returns identity image.
                     (Defaults to 90)

    Returns:
        image (np.array): jpeg compressed image
    '''
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), int(compression)]
    encoder = '.jpg'
    return _encode_compression(image, encoder, encode_param)

def png_compression(image, compression=9):
    '''encode image using png then decode (note png is lossless compression)

    Args:
        image (np.array): image to be compressed
        compression (int): amount of png compression (Defaults to 9)

    Returns:
        image (np.array): png compressed image
    '''
    encode_param = [int(cv2.IMWRITE_PNG_COMPRESSION), int(compression)]
    encoder = '.png'
    return _encode_compression(image, encoder, encode_param)

def _encode_compression(image, encoder, encode_param, uint=True):
    '''
        generic image encoder for jpeg, png etc
        using https://docs.opencv.org/3.4/d4/da8/group__imgcodecs.html to encode/decode
        for encode types: https://docs.opencv.org/3.4/d6/d87/imgcodecs_8hpp.html
    '''
    original_size = image.shape
    if uint == True:
        # jpeg/png encoder needs uint images not float
        image = img_as_ubyte(image)
    # encode image
    result, encoded_image = cv2.imencode(encoder, image, encode_param)
    # decode image
    decoded_image = cv2.imdecode(encoded_image, 1)
    if uint == True:
        # return to float type
        image = decoded_image.astype(np.float32) / 255.0
    # have to resize as jpeg can sometimes change the size of an image
    if image.shape != original_size:
        image = resize(image, original_size)
    return image
