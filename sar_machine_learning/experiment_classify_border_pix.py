"""
This file is to experiment on which filters and thresholding technique is best to classify land and water pixels
"""
import os

import rasterio
from matplotlib import pyplot as plt
from rasterio import mask, warp, crs
from shapely.geometry import mapping
from shapely.wkt import loads
from skimage.exposure import exposure
from skimage.filters import threshold_mean, gaussian, try_all_threshold
from skimage.morphology import area_closing, erosion, area_opening, diameter_closing, diameter_opening
from sklearn.preprocessing import normalize

input_dir = 'E:\\GRD\\Processing\\LC\\S1A_IW_GRDH_1SDV_20190119T112034_20190119T112059_025546_02D56B_08CA_glcm_VV.data'
BORDER_POLYGON = "POLYGON ((102.27346516739794 14.414524921768258, 102.2788804257423 14.414165920229811, 102.27848579816344 14.408511023266113, 102.27307066616757 14.408869878073046, 102.27346516739794 14.414524921768258))"


def convert_wkt_to_polygon(wkt_in):
    wkt = mapping(loads(wkt_in))
    crs_src = crs.CRS.from_epsg(4326)
    crs_dest = crs.CRS.from_epsg(32645)
    geom = warp.transform_geom(crs_src, crs_dest, wkt)
    return geom
    # return warp.transform_geom(crs_src, crs_dest, wkt)


border_polygon = convert_wkt_to_polygon(BORDER_POLYGON)
for file in os.listdir(input_dir):
    if file.endswith('.img') and 'Mean' in file:
        p = rasterio.open(input_dir + "\\" + file)
        print(file)
        [border_arr], border_xy = mask.mask(dataset=p, shapes=[border_polygon], all_touched=True, crop=True)
        fig, axes = plt.subplots(nrows=3, figsize=(7, 8))
        ax0, ax1, ax2 = axes
        plt.gray()
        border_arr = normalize(border_arr)
        # print(border_arr)
        ax0.imshow(border_arr)
        ax0.set_title(f'Original ({file})')
        g_img = area_closing(border_arr, area_threshold=512)
        # g_img = gaussian(border_arr, sigma=3)
        g_img = erosion(g_img)
        g_img = erosion(g_img)
        g_img = erosion(g_img)
        # g_img = exposure.equalize_hist(border_arr)
        thres = threshold_mean(g_img)
        ax1.imshow(g_img)
        ax1.set_title('After 1x area_closing and 3x erosion')
        thres = threshold_mean(g_img)
        thres_img = g_img > thres
        ax2.imshow(thres_img)
        ax2.set_title('Final binarization result')
        # fig, ax = try_all_threshold(g_img, figsize=(10, 8), verbose=False)
        plt.tight_layout()
        plt.imshow([[0], [1]])
        plt.show()
        print(thres_img[0][0])
        thres_img = thres_img.astype('uint8')
        print(thres_img[0][0])
