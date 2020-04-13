import json
import logging
import math
import os
import platform
import time
from datetime import datetime
from functools import partial

import matplotlib.pyplot as plt
import numpy as np
import pyproj
import rasterio
from rasterio import mask
from scipy import stats
from shapely.ops import transform
from shapely.wkt import loads
from sklearn.metrics import mean_squared_error

import basicconfig as config
from volumedata import volume_data


def convert_wkt_from_dd_to_m_to_polygon(wkt_in):
    projection = partial(pyproj.transform, pyproj.Proj(init="epsg:4326"), pyproj.Proj(init="epsg:32645"))
    wkt = loads(wkt_in)
    return transform(projection, wkt)


def convert_wkt_to_polygon(wkt_in):
    return loads(wkt_in)


def plot_water_height_change(est_height, act_height):
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    ax.scatter(pairs, est_height, c='g', label='estimated')
    ax.scatter(pairs, act_height, c='r', label='actual')
    ax.grid(True)
    plt.ylabel('Change in water level (m)', fontsize=10)
    plt.xlabel('Master-slave pairs', fontsize=10)
    plt.xticks(rotation=90)
    ax.legend()
    plt.title("Change in water level (m) between master slave pairs")
    plt.show()


def plot_water_vol_change(est_vol, act_vol):
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    ax.scatter(pairs, est_vol, c='g', label='estimated')
    ax.scatter(pairs, act_vol, c='r', label='actual')
    ax.grid(True)
    plt.ylabel('Change in water volume (million cubic metres)', fontsize=10)
    plt.xlabel('Master-slave pairs', fontsize=10)
    plt.xticks(rotation=90)
    ax.legend()
    plt.title("Change in water volume (million cubic metres) between master slave pairs")
    plt.show()


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

interferogram_dir = config.SLC_PARENT_DIR + config.PROCESSING_DIR + config.INTERFEROGRAM_PATH
snaphu_dir = interferogram_dir + config.SNAPHU_PATH
mask_dir = config.GRD_PARENT_DIR + config.PROCESSING_DIR + config.GRD_MASK_DIR
data = open(mask_dir + 'data.json', 'r', encoding='utf-8')
mask_wkt_json = json.load(data)
data.close()

time_str = time.strftime("%Y-%m-%d_%H-%M-%S")

est_height = []
act_height = []
est_vol = []
act_vol = []
pairs = []

files = os.listdir(snaphu_dir)
files.sort()
lines_to_write = []
for file in files:
    logger.info("Current folder: " + file)
    pairs.append(file)
    name_split = file.split('_')
    master_timestamp = name_split[0][:8]
    slave_timestamp = name_split[1][:8]
    master_name = f'{master_timestamp}_VV'
    slave_name = f'{slave_timestamp}_VV'

    master_date = datetime.strptime(master_timestamp, "%Y%m%d").date()
    slave_date = datetime.strptime(slave_timestamp, "%Y%m%d").date()

    # get area mask
    lc_polygon_m = convert_wkt_to_polygon(mask_wkt_json[master_name])
    lc_polygon_s = convert_wkt_to_polygon(mask_wkt_json[slave_name])
    file_prefix = file[:-3]
    # get area
    area_m = convert_wkt_from_dd_to_m_to_polygon(mask_wkt_json[master_name]).area
    area_s = convert_wkt_from_dd_to_m_to_polygon(mask_wkt_json[slave_name]).area
    # get coherence mask and consider only pixels that have coherence > 0.3
    try:
        coh_raster = rasterio.open(interferogram_dir + file_prefix + f'_coh_{config.POLARIZATIONS}.tif')
        disp_raster = rasterio.open(
            interferogram_dir + f"{file_prefix}_vert_disp_subset_{config.POLARIZATIONS}.data\\vert_disp_VV.img")
        if area_s < area_m:
            [coh_arr], coh_xy = mask.mask(dataset=coh_raster, shapes=[lc_polygon_s], nodata=np.nan, crop=True)
            [lc_arr], lc_xy = mask.mask(dataset=disp_raster, shapes=[lc_polygon_s], nodata=np.nan, crop=True)
        else:
            [coh_arr], coh_xy = mask.mask(dataset=coh_raster, shapes=[lc_polygon_m], nodata=np.nan, crop=True)
            [lc_arr], lc_xy = mask.mask(dataset=disp_raster, shapes=[lc_polygon_m], nodata=np.nan, crop=True)
        lc_arr = lc_arr.flatten()
        coh_arr = coh_arr.flatten()
        if len(lc_arr) != len(coh_arr):
            logger.critical(f"Length of displacement array and coherence array is different! disp len: {len(lc_arr)}, "
                            f"coh len: {len(coh_arr)}")
            exit(1)
        lc_arr_filtered = []
        for i in range(len(lc_arr)):
            if not np.isnan(lc_arr[i]) and coh_arr[i] > config.COH_THRESHOLD:
                lc_arr_filtered.append(lc_arr[i])
        logger.info(len(lc_arr_filtered))
    except rasterio.errors.RasterioIOError:
        disp_raster = rasterio.open(
            interferogram_dir + f"{file_prefix}_vert_disp_subset_{config.POLARIZATIONS}.data\\vert_disp_VV.img")
        if area_s < area_m:
            [lc_arr], lc_xy = mask.mask(dataset=disp_raster, shapes=[lc_polygon_s], nodata=np.nan, crop=True)
        else:
            [lc_arr], lc_xy = mask.mask(dataset=disp_raster, shapes=[lc_polygon_m], nodata=np.nan, crop=True)
        lc_arr = lc_arr.flatten()
        lc_arr_filtered = lc_arr[~np.isnan(lc_arr)]

    # get reference point to minus off error
    lc_gca_polygon = convert_wkt_to_polygon(config.GCA_POLYGON)
    [lc_gca_arr], lc_gca_xy = mask.mask(dataset=disp_raster, shapes=[lc_gca_polygon], all_touched=True, crop=True)
    disp_error = np.nanmean(lc_gca_arr)

    lines_to_write.append(f'master: {master_name}\n')
    lines_to_write.append(f'slave: {slave_name}\n')
    lines_to_write.append(f'resolution (m): {disp_raster.res}\n')

    lines_to_write.append(f'displacement error: {disp_error} m\n')
    lines_to_write.append(f'max displacement: {np.nanmax(lc_arr_filtered) - disp_error} m\n')
    lines_to_write.append(f'min displacement: {np.nanmin(lc_arr_filtered) - disp_error} m\n')

    mean_vert_disp = np.nanmean(lc_arr_filtered) - disp_error
    lines_to_write.append(f'mean displacement: {mean_vert_disp} m\n')
    est_height.append(mean_vert_disp)
    vol_changed = mean_vert_disp / 3 * (area_m + area_s + math.sqrt(area_m * area_s)) / 1000000
    est_vol.append(vol_changed)

    lines_to_write.append(f'area of master: {area_m} m^2\n')
    lines_to_write.append(f'area of slave: {area_s} m^2\n')
    # water level change wrt master image
    actual_vol_changed = volume_data.get_change_in_water_level(master_date, slave_date)

    lines_to_write.append(f'est vol changed: {vol_changed} million cubic metres\n')
    lines_to_write.append(f'act vol changed: {actual_vol_changed} million cubic metres\n')
    act_vol.append(actual_vol_changed)
    actual_h = actual_vol_changed * 3 / (area_m + area_s + math.sqrt(area_m * area_s)) * 1000000
    lines_to_write.append(f'Actual height change: {actual_h} m\n\n')
    act_height.append(actual_h)
    lines_to_write.append('')

out_file = open(config.RESULTS_DIR + "next_" + time_str + '.txt', 'w')
out_file.writelines(lines_to_write)
out_file.close()
plot_water_vol_change(est_vol, act_vol)
print(f'rmse: {math.sqrt(mean_squared_error(act_vol, est_vol))}')
print(f'correlation (vol): {stats.pearsonr(est_vol, act_vol)[0]}')

plot_water_height_change(est_height, act_height)
print(f'correlation (height): {stats.pearsonr(est_height, act_height)[0]}')

logger.info("Completed")
if platform.system() == "Windows":
    import winsound

    duration = 1000  # milliseconds
    freq = 1000  # Hz
    winsound.Beep(freq, duration)
    winsound.Beep(freq, duration)
