import os
import platform
from functools import partial

import pyproj
from shapely.geometry import mapping
from shapely.ops import transform
from shapely.wkt import loads
import json
from rasterio import mask, crs, warp
import rasterio
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import math
import time
from volumedata import get_volume_data
import basicconfig as config
import logging


def convert_wkt_from_dd_to_m_to_polygon(wkt_in):
    projection = partial(pyproj.transform, pyproj.Proj(init="epsg:4326"), pyproj.Proj(init="epsg:32645"))
    wkt = loads(wkt_in)
    return transform(projection, wkt)


def convert_wkt_to_polygon(wkt_in):
    return loads(wkt_in)


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

interferogram_dir = config.SLC_PARENT_DIR + config.PROCESSING_DIR
snaphu_dir = config.SLC_PARENT_DIR + config.PROCESSING_DIR + config.SNAPHU_PATH
mask_dir = config.GRD_PARENT_DIR + config.PROCESSING_DIR + config.GRD_MASK_DIR
data = open(mask_dir + 'data.json', 'r', encoding='utf-8')
mask_wkt_json = json.load(data)
data.close()

time_str = time.strftime("%Y-%m-%d_%H-%M-%S")
out_file = open(config.RESULTS_DIR + time_str + '.txt', 'w')

est_height = []
act_height = []

for file in os.listdir(snaphu_dir):
    logger.info("Current folder: " + file)
    name_split = file.split('_')
    master_timestamp = name_split[0][:8]
    slave_timestamp = name_split[1][:8]
    master_name = f'{master_timestamp}_VV'
    slave_name = f'{slave_timestamp}_VV'

    master_date = datetime.strptime(master_timestamp, "%Y%m%d").date()
    slave_date = datetime.strptime(slave_timestamp, "%Y%m%d").date()

    lc_polygon_m = convert_wkt_to_polygon(mask_wkt_json[master_name])
    lc_polygon_s = convert_wkt_to_polygon(mask_wkt_json[slave_name])
    lc_gca_polygon = convert_wkt_to_polygon(config.GCA_POLYGON)
    raster = rasterio.open(interferogram_dir + f"{file[:-3]}_vert_disp_subset_{config.POLARIZATIONS}.data\\vert_disp_VV.img")
    [lc_gca_arr], lc_gca_xy = mask.mask(dataset=raster, shapes=[lc_gca_polygon], all_touched=True, crop=True)

    disp_error = np.nanmean(lc_gca_arr)
    [lc_arr], lc_xy = mask.mask(dataset=raster, shapes=[lc_polygon_s], nodata=np.nan, crop=True)
    # plt.imshow(lc_arr)
    # plt.imshow(lc_gca_arr)
    # plt.gray()
    # plt.show()
    # plt.imshow(lc_arr)
    # plt.show()

    lc_arr = lc_arr.flatten()
    lc_arr = lc_arr[~np.isnan(lc_arr)]

    area_m = convert_wkt_from_dd_to_m_to_polygon(mask_wkt_json[master_name]).area
    area_s = convert_wkt_from_dd_to_m_to_polygon(mask_wkt_json[slave_name]).area

    out_file.writelines(f'master: {master_name}\n')
    out_file.write(f'slave: {slave_name}\n')
    out_file.write(f'resolution (m): {raster.res}\n')

    out_file.write(f'displacement error: {disp_error} m\n')
    out_file.write(f'max displacement: {np.nanmax(lc_arr) - disp_error} m\n')
    out_file.write(f'min displacement: {np.nanmin(lc_arr) - disp_error} m\n')
    mean_vert_disp = np.nanmean(lc_arr) - disp_error
    out_file.write(f'mean displacement: {mean_vert_disp} m\n')
    est_height.append(mean_vert_disp)

    vol_changed = mean_vert_disp / 3 * (area_m + area_s + math.sqrt(area_m * area_s))
    out_file.write(f'vol changed: {vol_changed} m^3\n')
    out_file.write(f'area of master: {area_m} m^2\n')
    out_file.write(f'area of slave: {area_s} m^2\n')
    actual_vol_changed = get_volume_data.get_change_in_water_level(master_date, slave_date)
    actual_h = actual_vol_changed * 3 / (area_m + area_s + math.sqrt(area_m * area_s)) * 1000000
    out_file.write(f'Actual height change: {actual_h} m\n\n')
    act_height.append(actual_h)

logger.info("Completed")
out_file.close()
fig, ax = plt.subplots()
x = [i for i in range(len(act_height))]
ax.scatter(x, est_height, c='g', label='est')
ax.scatter(x, act_height, c='r', label='actual')
plt.title("Change in water level (m)")
plt.show()
if platform.system() == "Windows":
    import winsound
    duration = 1000  # milliseconds
    freq = 1000  # Hz
    winsound.Beep(freq, duration)
    winsound.Beep(freq, duration)
