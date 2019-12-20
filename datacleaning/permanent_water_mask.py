import os
import re
import logging
import sys

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

from PIL import Image, ImageDraw
import rasterio
import numpy as np
import json
from scipy import ndimage
import matplotlib.pyplot as plt
from rasterio.features import shapes
from shapely.geometry import shape
import filemanager
import platform
from basicconfig import BLACK, WHITE, DAM_COLOR, GRD_MASK_DIR, LC_CLASSIFIED_DIR, POLARIZATIONS


input_dir, output_dir = filemanager.get_file_paths_based_on_os(platform.system(), filemanager.Product.grd)
mask_dir = output_dir + GRD_MASK_DIR
classified_LC_dir = output_dir + LC_CLASSIFIED_DIR
""" 
Some notes:
for binary images, 0 (white) is water 1 (black) is land
for mask, 255 is land (white) and 0 is water (black)
"""


def draw_area_larger_than(area_threshold, i, j, iterations, image):
    curr_area = 0
    for p_x in range(i, min(i + iterations, height)):
        for p_y in range(j, min(j + iterations, width)):
            if image[p_x][p_y] == 0:
                curr_area += 1
    if curr_area > area_threshold:
        for p_x in range(i, min(i + iterations, height)):
            for p_y in range(j, min(j + iterations, width)):
                if image[p_x][p_y] == 0:
                    ImageDraw.Draw(msk).point((p_y, p_x), fill=BLACK)


def is_area_larger_than(image, i, j, iterations, thres):
    curr_area = 0
    for p_x in range(i, min(i + iterations, height)):
        for p_y in range(j, min(j + iterations, width)):
            if image[p_x][p_y] == 0:
                curr_area += 1
    logger.debug("area is {}".format(curr_area))
    if curr_area > thres:
        return True
    return False


sample_spacing = 70
area_threshold = 0.96 * sample_spacing * sample_spacing
mask_json = {}
loop_dir = classified_LC_dir
for folder in os.listdir(loop_dir):
    logger.info(folder)
    img = rasterio.open(loop_dir + folder)
    msk = Image.open(loop_dir + folder)
    width = img.width
    height = img.height
    binary_img = img.read(1)
    # print(binary_img)
    logger.info(binary_img.shape)
    # print(binary_img[162][41])#0
    # print(binary_img[41][162])
    done = False
    # To reduce unnecessary checking, we starting search for the reservoir at an arbitrary point
    for x in range(0, height, sample_spacing // 2):
        for y in range(0, width, sample_spacing // 2):
            if binary_img[x][y] == BLACK:
                if is_area_larger_than(binary_img, x, y, sample_spacing, area_threshold) and is_area_larger_than(binary_img, x + sample_spacing // 2, y, sample_spacing, area_threshold):
                    logger.info("Found the reservoir!")
                    ImageDraw.floodfill(msk, (y, x), DAM_COLOR)
                    done = True
                    break
        if done:
            break
    if not done:
        logger.critical("No reservoir was found.")
        sys.exit("No reservoir was found.")
    msk_arr = np.array(msk).astype(np.uint8)
    msk_arr[msk_arr == WHITE] = BLACK
    msk_arr = ndimage.binary_fill_holes(msk_arr).astype(np.uint8)
    msk_arr[msk_arr == 1] = DAM_COLOR
    # msk = Image.fromarray(msk_arr)
    # msk.show()

    file_name = re.sub("\\..*$", "", folder)
    date = file_name.split('_')[-2][:8]
    mask_prdt_path = mask_dir + date + f'_{POLARIZATIONS}' + '.tif'
    with rasterio.open(
        mask_prdt_path,
        'w',
        driver='GTiff',
        height=img.height,
        width=img.width,
        count=1,
        dtype=np.uint8,
        nodata=BLACK,
        crs=img.crs,
        transform=img.transform,
    ) as dst:
        dst.write(msk_arr, 1)

    mask = None
    with rasterio.open(mask_prdt_path, 'r') as src:
        image = src.read(1, masked=True)  # first band
        results = (
            {'properties': {'raster_val': v}, 'geometry': s}
            for i, (s, v) in enumerate(shapes(image, mask=mask, transform=src.transform)))
    geoms = list(results)
    shp = shape(geoms[0]['geometry'])
    mask_json[date + f'_{POLARIZATIONS}'] = str(shp)
with open(mask_dir + 'data.json', 'w', encoding='utf-8') as f:
    json.dump(mask_json, f, ensure_ascii=False, indent=4)
logger.info("Completed")

if platform.system() == "Windows":
    import winsound
    duration = 1000  # milliseconds
    freq = 1000  # Hz
    winsound.Beep(freq, duration)
    winsound.Beep(freq, duration)