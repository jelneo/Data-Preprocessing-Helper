import os
import re

from PIL import Image, ImageDraw
import rasterio

BLACK = 0
WHITE = 255

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


def draw_area_larger_than(area_threshold, i, j, iterations, image):
    curr_area = 0
    for x in range(i, min(i + iterations, height)):
        for y in range(j, min(j + iterations, width)):
            if image[x][y] == 0:
                curr_area += 1
    # print("area is {}".format(curr_area))
    if curr_area > area_threshold:
        for x in range(i, min(i + iterations, height)):
            for y in range(j, min(j + iterations, width)):
                if image[x][y] == 0:
                    ImageDraw.Draw(msk).point((y, x), fill=BLACK)


sample_spacing = 8
area_threshold = 22
# creates an img with land-water masks
for folder in os.listdir(output_dir):
    if folder.endswith(".tif"):
        img = rasterio.open(output_dir + folder)
        # print(img.indexes)
        # print(img.descriptions)
        # print(img.width)
        # print(img.height)
        # size = img.size
        width = img.width
        height = img.height
        binary_img = img.read(1)
        msk = Image.new('L', (width, height), WHITE)

        for x in range(0, height, sample_spacing):
            for y in range(0, width, sample_spacing):
                draw_area_larger_than(22, x, y, sample_spacing, binary_img)
                # for spacing 10: 38 - ok, 40 - reasonable, 42 - a little boxy around the edges
                # for spacing 9: 35 - pretty good, 38 boxy around the edges, 30, 32 - scruffy edges along the st line
                # for spacing 8: 22 - best
        # msk.show()
        file_name = re.sub("\\..*$", "", folder)
        msk.save(mask_dir + file_name[:-7] + '.tif')
