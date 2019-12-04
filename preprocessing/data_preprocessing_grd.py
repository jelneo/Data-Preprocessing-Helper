"""
Does the following preprocessing steps for chosen prdt type (IW GRD level 1 prdt):
read
apply-orbit file
thermal noise removal
calibration
speckle filter
terrain correction
LinearFromTodB
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
from basicconfig import LC_WKT, POLARIZATIONS


AOI_WKT = \
"POLYGON((102.070752316744 14.565580568454624,102.36824148300377 14.565580568454624,102.36824148300377 14.322211910367955,102.070752316744 14.322211910367955,102.070752316744 14.565580568454624))"

MB_WKT = \
"POLYGON ((102.07791587712885 14.49683683310493, 102.16234336990105 14.49127182118036, 102.1573503766792 14.419364145685869, 102.07294806228553 14.424900383211916, 102.07791587712885 14.49683683310493))"

prdt_names = ["sentinel_1", "subset_prdt", "apply_orbit_prdt", "noise_rem_prdt", "calibrated_prdt", "speckle_prdt", "terrain_corrected_prdt", "db_prdt"]


def free_memory():
    g = globals()
    for var in prdt_names:
        del g[var]


GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

usr_system = platform.system()
input_dir, output_dir = filemanager.get_file_paths_based_on_os(platform.system(), filemanager.Product.grd)
output_dir = output_dir + "LC\\"

toRun = input("Run program? (Y/N)")
if toRun == "Y" or toRun == "y":
    pass
else:
    print("Exiting...")
    exit(0)

logger = logging.getLogger(__name__)
logger.info("Start data preprocessing")
gc.enable()
# Loop through all Sentinel-1 data sub folders that are located within a super folder
# (make sure that the data is already unzipped)

existing_files = [f[:-4] for f in os.listdir(output_dir) if '.tif' in f]

# # For blank images
# existing_files = [line.rstrip('\n') for line in open(output_dir + "outliers.txt")]
# print(existing_files)


count = 6

for folder in os.listdir(input_dir):
# for folder in os.listdir(output_dir):

    if ".SAFE" not in folder:
        continue
    # if ".dim" not in folder:
    #     continue
    if "S1B_IW_GRDH_1SDV_20190101T111959_20190101T112024_014300_01A9AA_8AF3.SAFE" != folder and "S1A_IW_GRDH_1SDV_20190107T112034_20190107T112059_025371_02CF15_BACB.SAFE" != folder:
        continue

    input_file_name = input_dir + folder
    # input_file_name = output_dir + folder
    file_name = re.sub("\\..*$", "", folder)
    timestamp = folder.split("_")[4]
    date = timestamp[:8]

    # if any(file_name in ef for ef in existing_files):
    #     continue

    # # for blank images
    # if not any(ef in file_name for ef in existing_files):
    #     continue

    # if file_name not in "S1B_IW_GRDH_1SDV_20190117T230016_20190117T230041_014540_01B157_80A3":
    #     continue

    logger.info("Current folder: " + folder)
    # Read in the Sentinel-1 data product:
    # sentinel_1 = ProductIO.readProduct(input_file_name + filemanager.manifest_extension)
    sentinel_1 = ProductIO.readProduct(input_file_name)
    logger.debug(sentinel_1)

    ### SUBSET
    # subset_prdt = sp.subset(sentinel_1, LC_WKT)
    # subset_path = output_dir + file_name + "_" + "subset"
    # ProductIO.writeProduct(subset_prdt, subset_path, "BEAM-DIMAP")

    ### APPLY-ORBIT FILE
    apply_orbit_prdt = sp.apply_orbit_file(sentinel_1)
    # apply_orbit_path = output_dir + file_name + "_" + "orbit"
    # ProductIO.writeProduct(apply_orbit_prdt, apply_orbit_path, "BEAM-DIMAP")

    ### THERMAL NOISE REMOVAL
    noise_rem_prdt = sp.thermal_noise_removal(apply_orbit_prdt)
    # noise_removal_path = output_dir + file_name + "_" + "noise_removal"
    # ProductIO.writeProduct(noise_rem_prdt, noise_removal_path, "BEAM-DIMAP")

    ### CALIBRATION
    calibrated_prdt = sp.calibration(apply_orbit_prdt, POLARIZATIONS)
    # calib_path = output_dir + file_name + "_" + "calibrate"
    # ProductIO.writeProduct(calibrated_prdt, calib_path, "BEAM-DIMAP")

    ### SPECKLE FILTER
    speckle_prdt = sp.speckle_filter(calibrated_prdt)
    # speckle_path = output_dir + file_name + "_" + "speckle"
    # ProductIO.writeProduct(speckle_prdt, speckle_path, "BEAM-DIMAP")

    ### TERRAIN CORRECTION
    terrain_corrected_prdt = sp.terrain_correction(calibrated_prdt, snappyconfigs.UTM_WGS84, 5.0)
    # terrain = output_dir + file_name + "_" + "corrected"
    # ProductIO.writeProduct(terrain_corrected_prdt, terrain, "GeoTIFF")
    # ProductIO.writeProduct(terrain_corrected_prdt, terrain + "_big", "GeoTIFF-BigTIFF")

    ### LinearFromTodB
    db_prdt = sp.linear_from_to_db(terrain_corrected_prdt)

    ### SUBSET
    subset_prdt = sp.subset(db_prdt, LC_WKT)
    # subset_path = output_dir + file_name + "_" + "db" + "_wgs84"
    # make sure no data val is NaN ten drop those when reading in for classification

    # ProductIO.writeProduct(subset_prdt, subset_path, "GeoTIFF")

    ### Convert datatype
    cnv_prdt = sp.convert_datatype(subset_prdt)

    ### GLCM
    glcm_prdt = sp.glcm(cnv_prdt)

    # ### Band merge
    merged_prdt = sp.band_merge([cnv_prdt, glcm_prdt])

    processed_path = output_dir + file_name + f'_glcm_{POLARIZATIONS}'
    ProductIO.writeProduct(merged_prdt, processed_path, "BEAM-DIMAP")

    # Due to heap memory constraints, can only process 6 products at a time. Otherwise it will lead to corrupted images
    count -= 1
    if count == 0:
        break
    free_memory()
    gc.collect()


# ### STACK COREGISTRATION - shldn't coregister because unable to use coregistration real-time
# src_prdts = []
# min_date = date.max
# # Find optimum master product
# for folder in os.listdir(output_dir):
#     timestamp = folder.split("_")[4]
#     converted_date = datetime.strptime(timestamp, '%Y%m%dT%H%M%S')
#     min_date = converted_date if converted_date < min_date else min_date
# min_date = min_date.strftime('%Y%m%dT%H%M%S')
#
# for file in os.listdir(output_dir):
#     if 'processed' in file and file.endswith('.dim'):
#         sentinel_1 = ProductIO.readProduct(output_dir + file)
#         # Master product needs to be the first product to be read
#         if min_date in file:
#             src_prdts.insert(0, sentinel_1)
#         else:
#             src_prdts.append(sentinel_1)
# stack_prdt = sp.create_stack(src_prdts)
# cross_correlation_prdt = sp.cross_correlation(stack_prdt)
# warp_prdt = sp.warp(cross_correlation_prdt)
# final_prdt_path = output_dir + "LC_stack"
# ProductIO.writeProduct(warp_prdt, final_prdt_path, "BEAM-DIMAP")

logger.info("Preprocessing completed")
if usr_system == "Windows":
    import winsound
    duration = 1000  # milliseconds
    freq = 1000  # Hz
    winsound.Beep(freq, duration)
    winsound.Beep(freq, duration)
