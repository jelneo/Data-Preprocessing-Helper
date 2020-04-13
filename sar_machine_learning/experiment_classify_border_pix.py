"""
This file is to experiment on which filters and thresholding technique is best to classify land and water pixels
"""
import os

import numpy as np
import rasterio
from matplotlib import pyplot as plt
from rasterio import mask
from shapely.wkt import loads
from skimage.filters import try_all_threshold
from skimage.morphology import opening
from sklearn.preprocessing import normalize

import basicconfig as config

input_dir = 'D:\\Texana\\Processing\\LC\\'
# input_dir = 'D:\\GRD\\Processing\\LC\\'


def convert_wkt_to_polygon(wkt_in):
    return loads(wkt_in)


border_polygon = convert_wkt_to_polygon(config.BORDER_POLYGON_TEXANA)
# border_polygon = convert_wkt_to_polygon(config.BORDER_POLYGON)
count = 0
size = 3
for folder in os.listdir(input_dir):
    if folder.endswith('.data'):
        for file in os.listdir(input_dir + folder):
            if file.endswith('.img'):
                p = rasterio.open(input_dir + folder + "\\" + file)
                print(folder + "\\" + file)
                [border_arr], border_xy = mask.mask(dataset=p, shapes=[border_polygon], all_touched=True, crop=True)
                fig, axes = plt.subplots(nrows=2, figsize=(7, 8))
                ax0, ax1 = axes
                plt.gray()
                border_arr = normalize(border_arr)
                ax0.imshow(border_arr)
                ax0.set_title(f'Original ({file})')
                kernel = np.ones((size, size)).astype("uint8")
                g_img = opening(border_arr, kernel)
                ax1.imshow(g_img)
                ax1.set_title(f'After morpohological opening ({size}x{size})')
                fig_temp, ax = try_all_threshold(g_img, verbose=False)
                plt.tight_layout()
                plt.show()
        count += 1
        input()
        if count == 5:
            exit()
