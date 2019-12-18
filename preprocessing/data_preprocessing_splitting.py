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

import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)
import gc
import os
import platform
import re

from snappy import GPF
from snappy import ProductIO

import filemanager
from snappy_tools import snappyoperators as sp
from basicconfig import POLARIZATIONS, MANIFEST_EXTENSION

GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

toRun = input("Run program? (Y/N)")
if toRun == "Y" or toRun == "y":
    pass
else:
    print("Exiting...")
    exit(0)

gc.enable()

logger.info("Start data preprocessing for top sar splitting")

input_dir, output_dir = filemanager.get_file_paths_based_on_os(platform.system(), filemanager.Product.slc)
# input_dir = "E://SLC//Original//"
# due to java heap memory space limits, only able to process 15 products at a time
count = 15
existing_files = [f[:-21] for f in os.listdir(output_dir) if '.dim' in f and 'top_sar' in f]

for folder in os.listdir(input_dir):
    if ".SAFE" not in folder:
        continue
    # if "S1B_IW_SLC__1SDV_20190101T111958_20190101T112025_014300_01A9AA_5FE6.SAFE" != folder \
    #         and "S1A_IW_SLC__1SDV_20190119T112033_20190119T112100_025546_02D56B_2E7C.SAFE" != folder:
    #     continue
    # if 'S1B_IW_SLC__1SDV_20190206T111957_20190206T112024_014825_01BAA2_194F.SAFE' != folder:
    #     continue

    input_file_name = input_dir + folder
    file_name = re.sub("\\..*$", "", folder)
    timestamp = folder.split("_")[5]
    date = timestamp[:8]

    if any(file_name in ef for ef in existing_files):
        continue

    logger.info('Current folder: ' + folder)
    # Read in the Sentinel-1 data product:
    sentinel_1 = ProductIO.readProduct(input_file_name + MANIFEST_EXTENSION)
    logger.info(sentinel_1)

    # TOPSAR SPLIT
    if 'S1B' in input_file_name:
        split_prdt = sp.top_sar_split(sentinel_1, 'IW2', 5, 6, POLARIZATIONS)
    else:
        split_prdt = sp.top_sar_split(sentinel_1, 'IW2', 7, 8, POLARIZATIONS)

    # APPLY-ORBIT FILE
    apply_orbit_prdt = sp.apply_orbit_file(split_prdt)

    split_path = output_dir + file_name + f'_top_sar_split_{POLARIZATIONS}'
    ProductIO.writeProduct(apply_orbit_prdt, split_path, 'BEAM-DIMAP')
    logger.info('Write done')
    count -= 1
    if count == 0:
        break

logger.info("Completed")
if platform.system() == "Windows":
    import winsound
    duration = 1000  # milliseconds
    freq = 1000  # Hz
    winsound.Beep(freq, duration)
    winsound.Beep(freq, duration)
