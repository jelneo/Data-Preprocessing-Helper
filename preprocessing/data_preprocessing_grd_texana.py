"""
Does the following preprocessing steps for chosen prdt type (IW GRD level 1 prdt):
read
apply-orbit file
thermal noise removal
calibration
speckle filter
terrain correction
Convert datatype
GLCM
subset
write
preprocessing order depends on product type(slc,grd,raw) and product level(0,1,2)
"""

import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
import gc
import os
import platform

from snappy import GPF
from snappy import ProductIO
import re

import filemanager
from snappy_tools import snappyconfigs, snappyoperators as sp
import basicconfig as config

GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

usr_system = platform.system()
input_dir, output_dir = filemanager.get_file_paths_based_on_os(platform.system(), filemanager.Product.grd)
input_dir = "D:\\Texana\\" + "Original_2018\\"
output_dir = "D:\\Texana\\" + "Processing_pre_2019\\" + config.LC_PATH

logger = logging.getLogger(__name__)
logger.info("Start data preprocessing")
gc.enable()
# Loop through all Sentinel-1 data sub folders that are located within a super folder
# (make sure that the data is already unzipped)

existing_files = [f[:-7] for f in os.listdir(output_dir) if '.dim' in f]
count = 5

for folder in os.listdir(input_dir):

    if ".SAFE" not in folder:
        continue

    input_file_name = input_dir + folder
    file_name = re.sub("\\..*$", "", folder)
    timestamp = folder.split("_")[4]
    date = timestamp[:8]

    if any(file_name in ef for ef in existing_files):
        continue

    logger.info("Current folder: " + folder)
    # Read in the Sentinel-1 data product:
    sentinel_1 = ProductIO.readProduct(input_file_name)
    logger.debug(sentinel_1)

    ### APPLY-ORBIT FILE
    apply_orbit_prdt = sp.apply_orbit_file(sentinel_1)

    ### THERMAL NOISE REMOVAL
    noise_rem_prdt = sp.thermal_noise_removal(apply_orbit_prdt)

    ### CALIBRATION
    calibrated_prdt = sp.calibration(apply_orbit_prdt, config.POLARIZATIONS)

    ### SPECKLE FILTER
    speckle_prdt = sp.speckle_filter(calibrated_prdt)

    ### TERRAIN CORRECTION
    terrain_corrected_prdt = sp.terrain_correction(calibrated_prdt, snappyconfigs.UTM_WGS84)

    ### SUBSET
    subset_prdt = sp.subset(terrain_corrected_prdt, config.TEXANA_WKT)

    ### Convert datatype
    cnv_prdt = sp.convert_datatype(subset_prdt, "int8")

    ### GLCM
    glcm_prdt = sp.glcm(cnv_prdt)

    ### LinearFromTodB
    db_prdt = sp.linear_from_to_db(subset_prdt)

    ### Band merge
    merged_prdt = sp.band_merge([db_prdt, glcm_prdt])

    processed_path = output_dir + file_name + f'_glcm_{config.POLARIZATIONS}'
    ProductIO.writeProduct(merged_prdt, processed_path, "BEAM-DIMAP")
    logger.info("Write done")

    # Due to heap memory constraints, can only process 6 products at a time. Otherwise it will lead to corrupted images
    count -= 1
    if count == 0:
        break
    gc.collect()


logger.info("Preprocessing completed")
if usr_system == "Windows":
    import winsound
    duration = 1000  # milliseconds
    freq = 1000  # Hz
    winsound.Beep(freq, duration)
    winsound.Beep(freq, duration)
