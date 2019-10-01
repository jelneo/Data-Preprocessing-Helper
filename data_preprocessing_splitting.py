import datetime
import platform

import os, gc

from snappy import ProductIO
from snappy import GPF

import filemanager
import snappyoperators as sp

polarizations = "VV"

GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

toRun = input("Run program? (Y/N)")
if toRun == "Y" or toRun == "y":
    pass
else:
    print("Exiting...")
    exit(0)

gc.enable()
now = datetime.datetime.now()
print("Start data preprocessing at " + now.strftime("%Y-%m-%d %H:%M:%S"))
print()

"""
Does the following preprocessing steps for chosen prdt type (IW SLC level 1 prdt):

To reduce the area to AOI:
1. Read
2. TOPSAR-Split (different for S1A and S1B)
3. Apply-orbit file
4. Write (.dim)

* Note: Cannot subset or deburst before doing back-geocoding
* Subset always the last step else the areas cropped out will not be the same due to processing e.g. terrain correction
Preprocessing order depends on product type(slc, grd, raw) and product level(0,1,2) 
"""

input_dir, output_dir = filemanager.get_file_paths_based_on_os(platform.system())
for folder in os.listdir(input_dir):
    if ".SAFE" not in folder:
        continue
    # if "S1A_IW_GRDH_1SDV_20190324T230053_20190324T230118_026486_02F776_6EB6.SAFE" != folder \
    #         and "S1B_IW_GRDH_1SDV_20190821T230023_20190821T230048_017690_021483_098C.SAFE" != folder:
    #     continue

    input_file_name = input_dir + folder
    file_name = folder[:-5]
    timestamp = folder.split("_")[4]
    date = timestamp[:8]

    print("Current folder: " + folder)
    # Read in the Sentinel-1 data product:
    sentinel_1 = ProductIO.readProduct(input_file_name + filemanager.manifest_extension)
    print(sentinel_1)

    # TOPSAR SPLIT
    if "S1B" in input_file_name:
        split_prdt = sp.top_sar_split(sentinel_1, "IW2", 6, 8, polarizations)
    else:
        split_prdt = sp.top_sar_split(sentinel_1, "IW2", 8, 9, polarizations)

    # APPLY-ORBIT FILE
    apply_orbit_prdt = sp.apply_orbit_file(split_prdt)
    apply_orbit_path = output_dir + file_name + "_orbit"
    ProductIO.writeProduct(apply_orbit_prdt, apply_orbit_path, "BEAM-DIMAP")


now = datetime.datetime.now()
print("Finished at " + now.strftime("%Y-%m-%d %H:%M:%S"))
if platform.system() == "Windows":
    import winsound

    duration = 1000  # milliseconds
    freq = 1000  # Hz
    winsound.Beep(freq, duration)
    winsound.Beep(freq, duration)
