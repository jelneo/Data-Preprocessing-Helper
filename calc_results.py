from shapely.wkt import loads
import json
from rasterio import mask, crs, warp
from functools import partial
from shapely.ops import transform
import pyproj
import rasterio
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import math
import time
from volumedata import get_volume_data
from basicconfig import POLARIZATIONS, RESULTS_DIR, GCA_POLYGON, GRD_PARENT_DIR, GRD_MASK_DIR


def convert_wkt_to_polygon(wkt_in):
    return loads(wkt_in)


def convert_wkt_from_dd_to_m_to_polygon(wkt_in):
    projection = partial(pyproj.transform, pyproj.Proj(init="epsg:4326"), pyproj.Proj(init="epsg:32645"))
    wkt = loads(wkt_in)
    return transform(projection, wkt)


# for each pair:
## read wkt for master slave
## read interferogram
## calc
## write to log

mask_dir = GRD_PARENT_DIR + GRD_MASK_DIR
data = open(mask_dir + 'data.json', 'r', encoding='utf-8')
mask_wkt_json = json.load(data)
data.close()

time_str = time.strftime("%Y-%m-%d_%H-%M-%S")
out_file = open(RESULTS_DIR + time_str + '.txt', 'w')

master_name = f'land_water_mask_rf_20190101T111959_VV'
slave_name = f'land_water_mask_rf_20190206T111958_VV'
master_timestamp = master_name.split('_')[-2][:8]
slave_timestamp = slave_name.split('_')[-2][:8]

master_date = datetime.strptime(master_timestamp, "%Y%m%d").date()
slave_date = datetime.strptime(slave_timestamp, "%Y%m%d").date()

lc_polygon_m = convert_wkt_to_polygon(mask_wkt_json[master_name])
lc_polygon_s = convert_wkt_to_polygon(mask_wkt_json[slave_name])
lc_gca_polygon = convert_wkt_to_polygon(GCA_POLYGON)
raster = rasterio.open(f"D:\\FYP_IW\\Processing\\20190101T111958_20190206T111957_vert_disp_subset_{POLARIZATIONS}.data\\vert_disp_VV.img")
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

area_m = lc_polygon_m.area
area_s = lc_polygon_s.area

out_file.writelines(f'master: {master_name}\n')
out_file.write(f'slave: {slave_name}\n')
out_file.write(f'resolution (m): {raster.res}\n')

out_file.write(f'displacement error: {disp_error} m\n')
out_file.write(f'max displacement: {np.nanmax(lc_arr) - disp_error} m\n')
out_file.write(f'min displacement: {np.nanmin(lc_arr) - disp_error} m\n')
mean_vert_disp = np.nanmean(lc_arr) - disp_error
out_file.write(f'mean displacement: {mean_vert_disp} m\n')

vol_changed = mean_vert_disp / 3 * (area_m + area_s + math.sqrt(area_m * area_s))
out_file.write(f'vol changed: {vol_changed} m^3\n')
out_file.write(f'area of master: {area_m} m^2\n')
out_file.write(f'area of slave: {area_s} m^2\n')
actual_vol_changed = get_volume_data.get_change_in_water_level(master_date, slave_date)
actual_h = actual_vol_changed * 3 / (area_m + area_s + math.sqrt(area_m * area_s)) * 1000000
out_file.write(f'Actual water level change: {actual_h} m\n\n')

out_file.close()
