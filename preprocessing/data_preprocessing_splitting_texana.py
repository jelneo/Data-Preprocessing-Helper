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

from snappy_tools import snappyoperators as sp
from basicconfig import POLARIZATIONS, MANIFEST_EXTENSION

GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()
gc.enable()

logger.info("Start data preprocessing for top sar splitting")

input_dir = "E:\\Texana_SLC\\Original\\"
output_dir = "E:\\Texana_SLC\\Processing\\"
# due to java heap memory space limits, only able to process 15 products at a time
count = 3
existing_files = [f[:-21] for f in os.listdir(output_dir) if '.dim' in f and 'top_sar' in f]

for folder in os.listdir(input_dir):
    if ".SAFE" not in folder:
        continue

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
    split_prdt = sp.top_sar_split(sentinel_1, 'IW1', 5, 6, POLARIZATIONS)

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
