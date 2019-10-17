import os
import re

from PIL import Image, ImageDraw
import rasterio
import numpy as np
import logging
import matplotlib.pyplot as plt
from rasterio.features import shapes
from shapely.geometry import shape

BLACK = 0
WHITE = 255
DAM_COLOR = 100

parent_dir = "E:\\GRD\\"
input_dir = parent_dir + "Original\\"
output_dir = parent_dir + "Processing\\"
mask_dir = parent_dir + "Mask\\"
# input_dir = parent_dir + "Test\\"
# output_dir = parent_dir + "TestProc\\"

""" 
Some notes:
for binary images, 0 (white) is water 1 (black) is land
for mask, 255 is land (white) and 0 is water (black)
"""

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


# def draw_area_larger_than(area_threshold, i, j, iterations, image):
#     curr_area = 0
#     for p_x in range(i, min(i + iterations, height)):
#         for p_y in range(j, min(j + iterations, width)):
#             if image[p_x][p_y] == 0:
#                 curr_area += 1
#     # print("area is {}".format(curr_area))
#     if curr_area > area_threshold:
#         for p_x in range(i, min(i + iterations, height)):
#             for p_y in range(j, min(j + iterations, width)):
#                 if image[p_x][p_y] == 0:
#                     ImageDraw.Draw(msk).point((p_y, p_x), fill=BLACK)
#
#
# sample_spacing = 20
# area_threshold = 0.15 * sample_spacing * sample_spacing
# creates an img with land-water masks
# for folder in os.listdir(parent_dir):
#     if folder.endswith(".tif") and 'land_water_mask' in folder:
#         img = rasterio.open(parent_dir + folder)
#         # print(img.indexes)
#         # print(img.descriptions)
#         # print(img.width)
#         # print(img.height)
#         # size = img.size
#         width = img.width
#         height = img.height
#         binary_img = img.read(1)
#         msk = Image.new('L', (width, height), WHITE)
#
#         for x in range(0, height, sample_spacing):
#             for y in range(0, width, sample_spacing):
#                 draw_area_larger_than(area_threshold, x, y, sample_spacing, binary_img)
#                 # for spacing 10: 38 - ok, 40 - reasonable, 42 - a little boxy around the edges
#                 # for spacing 9: 35 - pretty good, 38 boxy around the edges, 30, 32 - scruffy edges along the st line
#                 # for spacing 8: 22 - best
#         msk.show()
#         # file_name = re.sub("\\..*$", "", folder)
#         # msk.save(mask_dir + file_name[:-7] + '.tif')


def is_area_larger_than(image, i, j, iterations, thres):
    curr_area = 0
    for p_x in range(i, min(i + iterations, height)):
        for p_y in range(j, min(j + iterations, width)):
            if image[p_x][p_y] == 0:
                curr_area += 1
    # logger.info("area is {}".format(curr_area))
    if curr_area > thres:
        return True
    return False


sample_spacing = 20
area_threshold = 0.5 * sample_spacing * sample_spacing
for folder in os.listdir(parent_dir):
    if folder.endswith(".tif") and 'land_water_mask' in folder:
        logger.info("opened")
        img = rasterio.open(parent_dir + folder)
        print(img.crs)
        msk = Image.open(parent_dir + folder)
        width = img.width
        height = img.height
        binary_img = img.read(1)
        logger.info(binary_img.shape)
        print(binary_img[162][41])#0
        print(binary_img[41][162])
        done = False
        # To reduce unnecessary checking, we starting search for the dam at an arbitrary point
        for x in range(0, height, sample_spacing):
            for y in range(0, width, sample_spacing):
                if binary_img[x][y] == BLACK:
                    if is_area_larger_than(binary_img, x, y, sample_spacing, area_threshold):
                        logger.info("Found the dam!")
                        ImageDraw.floodfill(msk, (y, x), DAM_COLOR)
                        done = True
                        break
            if done:
                break
        # msk.show()
        msk_arr = np.array(msk)
        # msk_arr[msk_arr == BLACK] = BLACK
        msk_arr[msk_arr == WHITE] = BLACK
        # msk_arr[msk_arr == DAM_COLOR] = BLACK

        # msk = Image.fromarray(msk_arr)
        # msk.show()
        # plt.imshow(p_img_arr)
        # plt.show()
        file_name = re.sub("\\..*$", "", folder)
        mask_prdt_path = mask_dir + file_name[:-7] + '.tif'
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
            print(image)
            results = (
                {'properties': {'raster_val': v}, 'geometry': s}
                for i, (s, v) in enumerate(shapes(image, mask=mask, transform=src.transform)))
        geoms = list(results)
        shp = shape(geoms[0]['geometry'])
        print(shp)
        a, b = shp.exterior.xy
        plt.plot(a, b)
        plt.show()
logger.info("Completed")
