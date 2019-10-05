import datetime
import platform

import os, gc

from snappy import ProductIO
from snappy import GPF
import snappyoperators as sp

import snappyconfigs

AOI_WKT = \
"POLYGON((102.070752316744 14.565580568454624,102.36824148300377 14.565580568454624,102.36824148300377 14.322211910367955,102.070752316744 14.322211910367955,102.070752316744 14.565580568454624))"
polarizations = "VV,VH"

GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

usr_system = platform.system()
if usr_system == "Windows":
    parent_dir = "D:\\ESA Tutorial\\"
    input_dir = parent_dir + "Original\\"
    output_dir = parent_dir + "Processing\\"
    # input_dir = parent_dir + "Test\\"
    # output_dir = parent_dir + "TestProc\\"
    manifest_extension = "\\manifest.safe"
elif usr_system == "Linux":
    # For hpc
    parent_dir = "/hpctmp2/a0158174/"
    input_dir = parent_dir + "Original/"
    output_dir = input_dir + "Processing/"
    manifest_extension = "/manifest.safe"
else:
    print("No directory set.\nProgram exiting...")
    exit(1)

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
Does the following preprocessing steps for chosen prdt type (IW GRND level 1 prdt):
0. read
1. thermal noise removal
2. apply-orbit file
3. calibration
4. subset
5. speckle filter
6. terrain correction
7. write
add GLCM???
preprocessing order depends on product type(slc,grnd,raw) and product level(0,1,2) 
"""

# Loop through all Sentinel-1 data sub folders that are located within a super folder
# (make sure that the data is already unzipped)
for folder in os.listdir(input_dir):

    # if ".SAFE" not in folder:
    #     continue
    if "S1A_IW_GRDH_1SDV_20190324T230053_20190324T230118_026486_02F776_6EB6.SAFE" != folder \
            and "S1B_IW_GRDH_1SDV_20190821T230023_20190821T230048_017690_021483_098C.SAFE" != folder:
        continue

    input_file_name = input_dir + folder
    file_name = folder[:-5]
    timestamp = folder.split("_")[4]
    date = timestamp[:8]

    print("Current folder: " + folder)
    # Read in the Sentinel-1 data product:
    sentinel_1 = ProductIO.readProduct(input_file_name + manifest_extension)
    print(sentinel_1)

    ### THERMAL NOISE REMOVAL
    noise_rem_prdt = sp.thermal_noise_removal(sentinel_1)
    noise_removal_path = output_dir + file_name + "_" + "_noise_removal"
    ProductIO.writeProduct(noise_rem_prdt, noise_removal_path, "BEAM-DIMAP")

    ### APPLY-ORBIT FILE
    apply_orbit_prdt = sp.apply_orbit_file(noise_rem_prdt)
    apply_orbit_path = output_dir + file_name + "_" + "_orbit"
    ProductIO.writeProduct(apply_orbit_prdt, apply_orbit_path, "BEAM-DIMAP")

    ### CALIBRATION
    calibrated_prdt = sp.calibration(apply_orbit_prdt, polarizations)
    calib_path = output_dir + file_name + "_" + "_calibrate"
    ProductIO.writeProduct(calibrated_prdt, calib_path, "BEAM-DIMAP")

    ### SPECKLE FILTER
    speckle_prdt = sp.speckle_filter(calibrated_prdt)
    speckle_path = output_dir + file_name + "_" + "_speckle"
    ProductIO.writeProduct(speckle_prdt, speckle_path, "BEAM-DIMAP")

    ### TERRAIN CORRECTION
    terrain_corrected_prdt = sp.terrain_correction(speckle_prdt, snappyconfigs.UTM_WGS84_AUTO, 10.0)
    terrain = output_dir + file_name + "_" + "_corrected"
    ProductIO.writeProduct(terrain_corrected_prdt, terrain, "GeoTIFF")
    # ProductIO.writeProduct(terrain_corrected_prdt, terrain + "_big", "GeoTIFF-BigTIFF")

    ### SUBSET
    subset_prdt = sp.subset(calibrated_prdt, AOI_WKT)
    subset_path = output_dir + file_name + "_" + "_subset"
    ProductIO.writeProduct(subset_prdt, subset_path, "BEAM-DIMAP")
    print()

now = datetime.datetime.now()
print("Finished at " + now.strftime("%Y-%m-%d %H:%M:%S"))
if usr_system == "Windows":
    import winsound
    duration = 1000  # milliseconds
    freq = 1000  # Hz
    winsound.Beep(freq, duration)
    winsound.Beep(freq, duration)