import datetime
import platform

import os, gc

from snappy import ProductIO
from snappy import GPF

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
    print("Unrecognized system, no directory set.\nProgram exiting...")
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
    parameters = snappyconfigs.get_thermal_noise_removal_config()
    noise_removal_path = output_dir + file_name + "_" + "_noise_removal"
    noise_rem_prdt = GPF.createProduct("ThermalNoiseRemoval", parameters, sentinel_1)
    ProductIO.writeProduct(noise_rem_prdt, noise_removal_path, "BEAM-DIMAP")
    print("Thermal noise removal done")

    ### APPLY-ORBIT FILE
    parameters = snappyconfigs.get_thermal_noise_removal_config()
    apply_orbit_path = output_dir + file_name + "_" + "_orbit"
    apply_orbit_prdt = GPF.createProduct("Apply-Orbit-File", parameters, noise_rem_prdt)
    ProductIO.writeProduct(apply_orbit_prdt, apply_orbit_path, "BEAM-DIMAP")
    print("Apply-orbit file done")

    ### CALIBRATION
    parameters = snappyconfigs.get_calibration_config(polarizations)
    calib_path = output_dir + file_name + "_" + "_calibrate"
    calibrated_prdt = GPF.createProduct("Calibration", parameters, apply_orbit_prdt)
    ProductIO.writeProduct(calibrated_prdt, calib_path, "BEAM-DIMAP")
    print("Calibration done")

    ### SUBSET
    parameters = snappyconfigs.get_subset_config(AOI_WKT)
    subset_path = output_dir + file_name + "_" + "_subset"
    subset_prdt = GPF.createProduct("Subset", parameters, calibrated_prdt)
    ProductIO.writeProduct(subset_prdt, subset_path, "BEAM-DIMAP")
    print("Subset done")

    ### SPECKLE FILTER
    parameters = snappyconfigs.get_speckle_filter_config()
    speckle_path = output_dir + file_name + "_" + "_speckle"
    speckle_prdt = GPF.createProduct("Speckle-Filter", parameters, subset_prdt)
    ProductIO.writeProduct(speckle_prdt, speckle_path, "BEAM-DIMAP")
    print("Speckle filter done")

    ### TERRAIN CORRECTION
    parameters = snappyconfigs.get_terrain_correction_config()
    terrain = output_dir + file_name + "_" + "_corrected"
    terrain_corrected_prdt = GPF.createProduct("Terrain-Correction", parameters, speckle_prdt)
    ProductIO.writeProduct(terrain_corrected_prdt, terrain, "GeoTIFF")
    # ProductIO.writeProduct(terrain_corrected_prdt, terrain + "_big", "GeoTIFF-BigTIFF")
    print("Terrain correction done")
    print()

now = datetime.datetime.now()
print("Finished at " + now.strftime("%Y-%m-%d %H:%M:%S"))
if usr_system == "Windows":
    import winsound
    duration = 1000  # milliseconds
    freq = 1000  # Hz
    winsound.Beep(freq, duration)
    winsound.Beep(freq, duration)