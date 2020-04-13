"""
Functions for generating training data for machine learning
"""
import json
import os
from datetime import datetime
from functools import partial

import numpy as np
import pandas as pd
import pyproj
import rasterio
from rasterio import mask
from shapely.ops import transform
from shapely.wkt import loads
from skimage.filters import threshold_mean, threshold_triangle
from skimage.morphology import opening
from sklearn.preprocessing import normalize

import basicconfig as config
from volumedata import volume_data


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
    kernel = np.ones((3, 3)).astype("uint8")
    filtered_arr = opening(norm_arr, kernel)
    # thres = threshold_triangle(filtered_arr)
    thres = threshold_mean(filtered_arr)
    thres_img = filtered_arr > thres
    thres_img = thres_img.astype('uint8')
    return thres_img


def get_labelled_features_as_df(path):
    df = pd.DataFrame()
    total_land_samples = 0
    total_water_samples = 0
    for f in os.listdir(path):
        if f.endswith('.img'):
            raster = rasterio.open(path + '\\' + f)
            land_arr = np.empty(0)
            water_arr = np.empty(0)
            # obtain threshold mask
            mean_raster = rasterio.open(path + '\\Sigma0_VV_GLCMMean.img')
            border_polygon = convert_wkt_to_polygon(config.BORDER_POLYGON_TEXANA)
            # border_polygon = convert_wkt_to_polygon(config.BORDER_POLYGON)
            [border_arr], border_xy = mask.mask(dataset=mean_raster, shapes=[border_polygon], all_touched=True, crop=True)
            thres_mask = classify_border(border_arr)
            for land_wkt, water_wkt in zip(config.LAND_POLYGON_TEXANA, config.WATER_POLYGON_TEXANA):
            # for land_wkt, water_wkt in zip(config.LAND_POLYGON, config.WATER_POLYGON):
                land_polygon = convert_wkt_to_polygon(land_wkt)
                water_polygon = convert_wkt_to_polygon(water_wkt)

                [land_raster], land_xy = mask.mask(dataset=raster, shapes=[land_polygon], all_touched=True, crop=True)
                [water_raster], water_xy = mask.mask(dataset=raster, shapes=[water_polygon], all_touched=True, crop=True)
                land_arr = np.concatenate((land_arr, land_raster.flatten()))
                water_arr = np.concatenate((water_arr, water_raster.flatten()))
            border_polygon = convert_wkt_to_polygon(config.BORDER_POLYGON_TEXANA)
            # border_polygon = convert_wkt_to_polygon(config.BORDER_POLYGON)
            [border_arr], border_xy = mask.mask(dataset=raster, shapes=[border_polygon], all_touched=True, crop=True)

            border_land = []
            border_water = []
            for i in range(len(border_arr)):
                for j in range(len(border_arr[0])):
                    if thres_mask[i][j] == 1:  # land
                        border_land.append(border_arr[i][j])
                    else:  # water
                        border_water.append(border_arr[i][j])
            land_1d = np.concatenate((land_arr.flatten(), border_land))
            water_1d = np.concatenate((water_arr.flatten(), border_water))
            land_1d = land_1d.tolist()
            water_1d = water_1d.tolist()

            total_land_samples = len(land_1d)
            total_water_samples = len(water_1d)
            land_water_arr = land_1d + water_1d
            df = pd.concat([df, pd.DataFrame(land_water_arr, columns=[raster.descriptions[0]])], axis=1, sort=False)
    label_df = create_labels(total_land_samples, total_water_samples)
    df = pd.concat([df, label_df], axis=1, sort=False)
    min_num_samples = min(total_water_samples, total_land_samples)
    if total_land_samples > min_num_samples:
        to_remove = np.random.choice(df[df['label'] == config.LAND].index, size=total_land_samples - min_num_samples, replace=False)
    else:
        to_remove = np.random.choice(df[df['label'] == config.WATER].index, size=total_water_samples - min_num_samples, replace=False)
    df.drop(to_remove)
    return df


def get_labelled_data(path):
    feature_bands = [get_labelled_features_as_df(path + '\\' + f) for f in os.listdir(path) if f.endswith('.img')]
    return pd.concat(feature_bands, axis=1, sort=False)


def convert_wkt_from_dd_to_m_to_polygon(wkt_in):
    projection = partial(pyproj.transform, pyproj.Proj(init="epsg:4326"), pyproj.Proj(init="epsg:32645"))
    wkt = loads(wkt_in)
    return transform(projection, wkt)


def get_area_vol_as_df(mask_path):
    data = open(mask_path, 'r', encoding='utf-8')
    mask_dict = json.load(data)
    data.close()

    data = []
    sorted_files = sorted(mask_dict.keys())
    for file_name in sorted_files:
        area = convert_wkt_from_dd_to_m_to_polygon(mask_dict[file_name]).area
        date = datetime.strptime(file_name.split('_')[0], config.DATE_FORMAT).date()
        vol = volume_data.get_volume_for_date(date)
        data.append([date, area, vol])

    df = pd.DataFrame(data, columns=['date', 'area', 'volume'])
    return df


def get_drought_df(mask_path):
    data = open(mask_path, 'r', encoding='utf-8')
    mask_dict = json.load(data)
    data.close()

    # data = []
    sorted_files = sorted(mask_dict.keys())
    date_list = []
    area_list = []

    for file_name in sorted_files:
        area = convert_wkt_from_dd_to_m_to_polygon(mask_dict[file_name]).area
        date = datetime.strptime(file_name.split('_')[0], config.DATE_FORMAT).date()
        date_list.append(date)
        area_list.append(area)

    # inflows = volume_data.get_inflow_for_dates(date_list[0].year, date_list)
    # temperatures = volume_data.get_temp_for_dates(date_list)
    volumes = volume_data.get_volume_for_dates(date_list[0].year, date_list)
    data = zip(date_list, volumes, area_list)
    # data = zip(date_list, volumes, area_list, inflows, temperatures)

    df = pd.DataFrame(data, columns=['date', 'volume', 'area'])
    # df = pd.DataFrame(data, columns=['date', 'volume', 'area', 'inflow', 'temp'])
    df.dropna(inplace=True)
    return df
