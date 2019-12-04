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

BLACK = 0
WHITE = 255
DAM_COLOR = 100

parent_dir = "E:\\GRD\\"
input_dir = parent_dir + "Original\\"
processing_dir = parent_dir + "Processing\\"
mask_dir = parent_dir + "Mask\\"
# input_dir = parent_dir + "Test\\"
# output_dir = parent_dir + "TestProc\\"
classified_LC_dir = processing_dir + "LC_classification\\"


polarizations = 'VH'

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
    # print("area is {}".format(curr_area))
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


sample_spacing = 30
area_threshold = 0.95 * sample_spacing * sample_spacing
mask_json = {}
loop_dir = classified_LC_dir
for folder in os.listdir(loop_dir):
    if folder.endswith(".tif") and f'land_water_mask_rf' in folder:
        logger.info(folder)
        img = rasterio.open(loop_dir + folder)
        print(img.crs)
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
        for x in range(0, height, sample_spacing):
            for y in range(0, width, sample_spacing):
                if binary_img[x][y] == BLACK:
                    if is_area_larger_than(binary_img, x, y, sample_spacing, area_threshold):
                        logger.info("Found the reservoir!")
                        ImageDraw.floodfill(msk, (y, x), DAM_COLOR)
                        done = True
                        break
            if done:
                break
        if not done:
            logger.critical("No reservoir was found.")
            sys.exit("No reservoir was found.")
        # msk.show()
        msk_arr = np.array(msk).astype(np.uint8)
        msk_arr[msk_arr == WHITE] = BLACK
        # print(msk_arr.max())
        # print(msk_arr.min())
        # msk_arr[msk_arr == DAM_COLOR] = BLACK

        # plt.imshow(p_img_arr)
        # plt.show()

        msk_arr = ndimage.binary_fill_holes(msk_arr).astype(np.uint8)
        # print(msk_arr.max())
        # print(msk_arr.min())
        msk_arr[msk_arr == 1] = DAM_COLOR
        # msk = Image.fromarray(msk_arr)
        # msk.show()

        file_name = re.sub("\\..*$", "", folder)
        mask_prdt_path = mask_dir + file_name + '.tif'
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
        # msk.save(mask_dir + file_name[:-7] + '.tif')

        mask = None
        with rasterio.open(mask_prdt_path, 'r') as src:
            image = src.read(1, masked=True)  # first band
            results = (
                {'properties': {'raster_val': v}, 'geometry': s}
                for i, (s, v) in enumerate(shapes(image, mask=mask, transform=src.transform)))
        geoms = list(results)
        shp = shape(geoms[0]['geometry'])
        mask_json[file_name] = str(shp)
with open(mask_dir + 'data.json', 'w', encoding='utf-8') as f:
    json.dump(mask_json, f, ensure_ascii=False, indent=4)
        # a, b = shp.exterior.xy
        # plt.plot(a, b)
        # plt.show()
logger.info("Completed")
