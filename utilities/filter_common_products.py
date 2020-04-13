"""
Filter products with common dates for GRD and SLC products
"""

import os
import re
import zipfile

import basicconfig as config

slc_path = config.SLC_PARENT_DIR + config.ORIG_DIR
grd_path = config.GRD_PARENT_DIR + config.ORIG_DIR
slc_output_dir = config.SLC_PARENT_DIR + config.PROCESSING_DIR
grd_output_dir = config.GRD_PARENT_DIR + config.PROCESSING_DIR

grd_files = [f for f in os.listdir(grd_path) if '.zip' in f]
slc_files = [f for f in os.listdir(slc_path) if '.zip' in f]
common_grd = []
common_slc = []

# go thru the two lists and if same date add to common files
count = 0
slc_out = open(slc_output_dir + config.COMMON_FILES_NAME, "w+")
grd_out = open(grd_output_dir + config.COMMON_FILES_NAME, "w+")
for grd_file in grd_files:
    for slc_file in slc_files:
        grd_time = grd_file.split("_")[4][:8]
        slc_time = slc_file.split("_")[5][:8]
        if grd_time == slc_time:
            slc_name = re.sub("\\..*$", "", slc_file)
            grd_name = re.sub("\\..*$", "", grd_file)
            common_slc.append(str(slc_name) + "\n")
            common_grd.append(str(grd_name) + "\n")
            count += 1
common_grd.sort(key=lambda s: s.split("_")[4][:8])
common_slc.sort(key=lambda s: s.split("_")[5][:8])
print(f"Total number of common files for GRD and SLC: {count}")
slc_out.writelines(common_slc)
grd_out.writelines(common_grd)
slc_out.close()
grd_out.close()
