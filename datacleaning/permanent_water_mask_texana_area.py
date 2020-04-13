import logging
import os
import re
from functools import partial

import pyproj
from shapely.ops import transform
from skimage.morphology import remove_small_holes, remove_small_objects

from trainingdata import convert_wkt_to_polygon

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

import rasterio
import numpy as np
import json
from rasterio import mask
from shapely.wkt import loads
import filemanager
import platform
import basicconfig as config


input_dir, output_dir = filemanager.get_file_paths_based_on_os(platform.system(), filemanager.Product.grd)
area_dir = "D:\\Texana\\Processing\\Area\\"
classified_LC_dir = "D:\\Texana\\Processing\\" + config.LC_CLASSIFIED_DIR


def convert_wkt_from_dd_to_m_to_polygon(wkt_in):
    projection = partial(pyproj.transform, pyproj.Proj(init="epsg:4326"), pyproj.Proj(init="epsg:32629"))
    wkt = loads(wkt_in)
    return transform(projection, wkt)


areas_json = {}
mask_json = {}
loop_dir = classified_LC_dir
sorted_files = sorted(os.listdir(loop_dir))
for folder in sorted_files:
    logger.info(folder)
    img = rasterio.open(loop_dir + folder)
    file_name = re.sub("\\..*$", "", folder)
    date = file_name.split('_')[-2][:8]
    LC_polygon = convert_wkt_to_polygon(config.TEXANA_WKT_REDUCED)
    [prdt_arr], prdt_xy = mask.mask(dataset=img, shapes=[LC_polygon], nodata=config.NO_DATA, all_touched=True, crop=True)

    height, width = prdt_arr.shape
    binary_img = prdt_arr
    logger.info(binary_img.shape)
    msk_arr = prdt_arr.astype(np.uint8)
    msk_arr[msk_arr == config.BLACK] = config.WATER
    msk_arr[msk_arr == config.NO_DATA] = config.LAND
    msk_arr[msk_arr == config.WHITE] = config.LAND
    bool_msk = msk_arr > 0
    msk_arr = remove_small_holes(bool_msk, area_threshold=2048).astype(np.uint8)

    bool_msk = msk_arr > 0
    msk_arr = remove_small_objects(bool_msk, min_size=1024).astype(np.uint8)
    msk_arr[msk_arr == config.WATER] = config.RESERVOIR_COLOR
    msk_arr_flatten = msk_arr.flatten()
    unique, counts = np.unique(msk_arr_flatten, return_counts=True)

    count_dict = dict(zip(unique, counts))
    num_water_pixels = count_dict[config.RESERVOIR_COLOR]
    area = num_water_pixels * 100

    mask_prdt_path = area_dir + date + f'_{config.POLARIZATIONS}' + '.tif'
    with rasterio.open(
        mask_prdt_path,
        'w',
        driver='GTiff',
        height=img.height,
        width=img.width,
        count=1,
        dtype=np.uint8,
        nodata=config.BLACK,
        crs=img.crs,
        transform=img.transform,
    ) as dst:
        dst.write(msk_arr, 1)

    areas_json[date + f'_{config.POLARIZATIONS}'] = int(area)

with open(area_dir + 'area.json', 'w', encoding='utf-8') as f:
    json.dump(areas_json, f, ensure_ascii=False, indent=4)
logger.info("Completed")

if platform.system() == "Windows":
    import winsound
    duration = 1000  # milliseconds
    freq = 1000  # Hz
    winsound.Beep(freq, duration)
    winsound.Beep(freq, duration)