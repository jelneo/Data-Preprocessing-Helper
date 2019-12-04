"""
Functions for generating training data for machine learning
"""
import os

import numpy as np
import rasterio
import pandas as pd
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from rasterio import mask, warp, crs
from shapely.wkt import loads
import pyproj
from functools import partial
from shapely.ops import transform
from skimage.filters.rank import autolevel, mean_bilateral, enhance_contrast_percentile, minimum, maximum
from skimage.morphology import disk, diameter_opening, diameter_closing, area_closing, area_opening, erosion
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler, normalize
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
from sklearn.model_selection import cross_val_score
from sklearn.svm import SVC
from skimage.restoration import (denoise_tv_chambolle, denoise_bilateral,
                                 denoise_wavelet, estimate_sigma)
from skimage.filters import threshold_otsu, threshold_local, gaussian, threshold_multiotsu, rank, sobel, scharr, \
    prewitt, roberts, sobel_h, try_all_threshold, threshold_yen, threshold_mean
from scipy import ndimage as ndi, ndimage
from skimage import exposure, feature
from matplotlib import pyplot as plt
import seaborn as sns
import logging
import basicconfig as config

def convert_wkt_to_polygon(wkt_in):
    return loads(wkt_in)


def create_labels(land_len, water_len):
    land_labels = np.full(land_len, config.LAND)
    water_labels = np.full(water_len, config.WATER)
    target_labels = np.concatenate((land_labels, water_labels))
    return pd.DataFrame(target_labels, columns=['label'])


# Get water and land mask to extract ground truths
def extract_features_from(path):
    features = []
    for file in os.listdir(path):
        if file.endswith('.img'):
            p = rasterio.open(path + '\\' + file)
            prdt_arr = p.read(1)
            df = pd.DataFrame(prdt_arr.flatten(), columns=[p.descriptions[0]])
            features.append(df)
    return pd.concat(features, axis=1, sort=False)


def classify_border(border_array):
    norm_arr = normalize(border_array)
    filtered_arr = area_closing(norm_arr, area_threshold=512)
    filtered_arr = erosion(filtered_arr)
    filtered_arr = erosion(filtered_arr)
    filtered_arr = erosion(filtered_arr)
    thres = threshold_mean(filtered_arr)
    thres_img = filtered_arr > thres
    thres_img = thres_img.astype('uint8')
    land_pix = []
    water_pix = []
    for i in range(len(border_array)):
        for j in range(len(border_array[0])):
            if thres_img[i][j] == 1:  # land
                land_pix.append(border_array[i][j])
            else:  # water
                water_pix.append(border_array[i][j])
    return land_pix, water_pix


def get_labelled_feature_as_df(path):
    df = pd.DataFrame()
    total_land_samples = 0
    total_water_samples = 0
    for f in os.listdir(path):
        if f.endswith('.img'):
            # global land_shape, water_shape
            raster = rasterio.open(path + '\\' + f)
            # print({i: dtype for i, dtype in zip(raster.indexes, raster.dtypes)})
            land_polygon = convert_wkt_to_polygon(config.LAND_POLYGON)
            water_polygon = convert_wkt_to_polygon(config.WATER_POLYGON)
            border_polygon = convert_wkt_to_polygon(config.BORDER_POLYGON)

            [land_arr], land_xy = mask.mask(dataset=raster, shapes=[land_polygon], all_touched=True, crop=True)
            [water_arr], water_xy = mask.mask(dataset=raster, shapes=[water_polygon], all_touched=True, crop=True)
            [border_arr], border_xy = mask.mask(dataset=raster, shapes=[border_polygon], all_touched=True, crop=True)

            # plt.imshow(border_arr, cmap='gray')
            # plt.show()
            # print(land_arr)
            border_land, border_water = classify_border(border_arr)

            # if land_len < 0:
            #     land_len = land_arr.shape[0] * land_arr.shape[1] + len(border_land)
            # if water_len < 0:
            #     water_len = water_arr.shape[0] * water_arr.shape[1] + len(border_water)

            # logger.info(land_arr.shape)
            # logger.info(water_arr.shape)
            # logger.info(raster.crs)
            land_1d = np.concatenate((land_arr.flatten(), border_land))
            water_1d = np.concatenate((water_arr.flatten(), border_water))
            land_1d = land_1d.tolist()
            water_1d = water_1d.tolist()
            # min_num_samples = min(len(land_1d), len(water_1d))
            total_land_samples = len(land_1d)
            total_water_samples = len(water_1d)
            # Ensure balanced data set
            # while len(land_1d) > min_num_samples:
            #     random_index = np.random.randint(0, len(land_1d))
            #     land_1d.pop(random_index)
            # while len(water_1d) > min_num_samples:
            #     random_index = np.random.randint(0, len(water_1d))
            #     water_1d.pop(random_index)
            land_water_arr = land_1d + water_1d
            df = pd.concat([df, pd.DataFrame(land_water_arr, columns=[raster.descriptions[0]])], axis=1, sort=False)
    # print(df)
    label_df = create_labels(total_land_samples, total_water_samples)
    df = pd.concat([df, label_df], axis=1, sort=False)
    # print(df)
    min_num_samples = min(total_water_samples, total_land_samples)
    if total_land_samples > min_num_samples:
        to_remove = np.random.choice(df[df['label'] == config.LAND].index, size=total_land_samples - min_num_samples, replace=False)
    else:
        to_remove = np.random.choice(df[df['label'] == config.WATER].index, size=total_water_samples - min_num_samples, replace=False)
    df.drop(to_remove)
    # print(df.shape)
    return df


def get_labelled_data(path):
    feature_bands = [get_labelled_feature_as_df(path + '\\' + f) for f in os.listdir(path) if f.endswith('.img')]
    # feature_bands.append(create_labels(land_shape, water_shape))
    return pd.concat(feature_bands, axis=1, sort=False)


# parent_dir = "E:\\GRD\\"
# input_dir = parent_dir + "Original\\"
# processing_dir = parent_dir + "Processing\\"
# processing_dir_LC = processing_dir + "LC\\"
# mask_dir = processing_dir + "LC_Mask\\"
# ml_dir = parent_dir + "ML\\LC\\"
# classified_LC_dir = processing_dir + "LC_classification\\"
# print(get_labelled_feature_as_df(processing_dir_LC + "S1B_IW_GRDH_1SDV_20190101T111959_20190101T112024_014300_01A9AA_8AF3_glcm_VV.data"))