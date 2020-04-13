import logging
import os
import re
import sys

from skimage.morphology import remove_small_holes

from trainingdata import convert_wkt_to_polygon

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

from PIL import Image, ImageDraw
import rasterio
import numpy as np
import json
from rasterio import mask
from rasterio.features import shapes
from shapely.geometry import shape
import filemanager
import platform
import basicconfig as config


input_dir, output_dir = filemanager.get_file_paths_based_on_os(platform.system(), filemanager.Product.grd)
mask_dir = "D:\\Texana\\Processing\\" + config.GRD_MASK_DIR
classified_LC_dir = "D:\\Texana\\Processing\\" + config.LC_CLASSIFIED_DIR


def is_area_larger_than(image, i, j, iterations, thres):
    curr_area = 0
    for p_x in range(i, min(i + iterations, height)):
        for p_y in range(j, min(j + iterations, width)):
            if image[p_x][p_y] == config.BLACK:
                curr_area += 1
    logger.debug("area is {}".format(curr_area))
    if curr_area > thres:
        return True
    return False


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
    msk = Image.fromarray(prdt_arr)
    msk.show()

    width, height = prdt_arr.shape[1], prdt_arr.shape[0]
    binary_img = prdt_arr
    logger.info(binary_img.shape)
    sample_spacing = 70
    area_threshold = 0.96 * sample_spacing * sample_spacing
    done = False

    # To reduce unnecessary checking, we starting search for the reservoir at an arbitrary point
    for x in range(0, height, sample_spacing // 2):
        for y in range(0, width, sample_spacing // 2):
            if binary_img[x][y] == config.BLACK:
                if is_area_larger_than(binary_img, x, y, sample_spacing, area_threshold) and is_area_larger_than(
                        binary_img, x + sample_spacing // 2, y, sample_spacing, area_threshold):
                    logger.info("Found the reservoir!")
                    ImageDraw.floodfill(msk, (y, x), config.RESERVOIR_COLOR)
                    done = True
                    break
        if done:
            break
    if not done:
        logger.critical("No reservoir was found.")
        sys.exit("No reservoir was found.")

    msk_arr = np.array(msk).astype(np.uint8)
    msk_arr[msk_arr == config.NO_DATA] = config.LAND
    msk_arr[msk_arr == config.WHITE] = config.LAND
    msk_arr = remove_small_holes(msk_arr, area_threshold=2048).astype(np.uint8)
    msk_arr[msk_arr == config.WATER] = config.RESERVOIR_COLOR

    mask_prdt_path = mask_dir + date + f'_{config.POLARIZATIONS}' + '.tif'
    with rasterio.open(
        mask_prdt_path,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=np.uint8,
        nodata=config.BLACK,
        crs=img.crs,
        transform=img.transform,
    ) as dst:
        dst.write(msk_arr, 1)

    with rasterio.open(mask_prdt_path, 'r') as src:
        image = src.read(1, masked=True)  # first band
        results = (
            {'properties': {'raster_val': v}, 'geometry': s}
            for i, (s, v) in enumerate(shapes(image, mask=None, transform=src.transform)))
    geoms = list(results)
    shp = shape(geoms[0]['geometry'])
    mask_json[date + f'_{config.POLARIZATIONS}'] = str(shp)

with open(mask_dir + 'data.json', 'w', encoding='utf-8') as f:
    json.dump(mask_json, f, ensure_ascii=False, indent=4)
logger.info("Completed")

if platform.system() == "Windows":
    import winsound
    duration = 1000  # milliseconds
    freq = 1000  # Hz
    winsound.Beep(freq, duration)
    winsound.Beep(freq, duration)