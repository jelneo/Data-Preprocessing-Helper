import datetime
import platform

import os, gc

from snappy import ProductIO
from snappy import GPF

import snappyconfigs

AOI_WKT = "POLYGON ((102.12635428857155 14.248290232074497, 102.53781291893677 14.327232114630814, 102.48940057780496 14.575151504929456, 102.0774759551546 14.496314998624996, 102.12635428857155 14.248290232074497))"

polarizations = ["VV"]

GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

usr_system = platform.system()
if usr_system == "Windows":
    parent_dir = "D:\\ESA Tutorial\\"
    # input_dir = parent_dir + "Original\\"
    # output_dir = parent_dir + "Processing\\"
    input_dir = parent_dir + "Test\\"
    output_dir = parent_dir + "TestProc\\"
elif usr_system == "Linux":
    # For hpc
    parent_dir = ".\\"
    input_dir = parent_dir + "Original\\"
    output_dir = input_dir + "Processing\\"
else:
    print("Unrecognized system, no directory set.\nProgram exiting...")
    exit(1)

toRun = input("Run program? (Y/N)")
if toRun == "Y" or toRun == "y":
    exit(0)
    pass
else:
    print("Exiting...")

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

    if ".SAFE" not in folder:
        continue
    # if "S1B_IW_GRDH_1SDV_20190829T112005_20190829T112030_017800_0217F9_F111.SAFE" != folder:
    #     continue

    input_file_name = input_dir + folder
    file_name = folder[:-5]
    timestamp = folder.split("_")[4]
    date = timestamp[:8]

    print("Current folder: " + folder)
    # Read in the Sentinel-1 data product:
    sentinel_1 = ProductIO.readProduct(input_file_name + "\\manifest.safe")
    print(sentinel_1)

    # If polarization bands are available, split up your code to process VH and VV intensity data separately.
    # The first step is the calibration procedure by transforming the DN values to Sigma Naught respectively.
    # You can specify the parameters to input_file_name the Image in Decibels as well.

    for p in polarizations:
        polarization = p
        ### THERMAL NOISE REMOVAL
        parameters = snappyconfigs.get_thermal_noise_removal_config()
        noise_removal_path = output_dir + file_name + "_" + date + "_noise_removal_" + polarization
        noise_rem_prdt = GPF.createProduct("ThermalNoiseRemoval", parameters, sentinel_1)
        ProductIO.writeProduct(noise_rem_prdt, noise_removal_path, "BEAM-DIMAP")
        print("Thermal noise removal done")

        ### APPLY-ORBIT FILE
        parameters = snappyconfigs.get_thermal_noise_removal_config()
        apply_orbit_path = output_dir + file_name + "_" + date + "_orbit_" + polarization
        apply_orbit_prdt = GPF.createProduct("Apply-Orbit-File", parameters, noise_rem_prdt)
        ProductIO.writeProduct(apply_orbit_prdt, apply_orbit_path, "BEAM-DIMAP")
        print("Apply-orbit file done")

        ### CALIBRATION
        parameters = snappyconfigs.get_calibration_config(polarization)
        calib_path = output_dir + file_name + "_" + date + "_calibrate_" + polarization
        calibrated_prdt = GPF.createProduct("Calibration", parameters, apply_orbit_prdt)
        ProductIO.writeProduct(calibrated_prdt, calib_path, "BEAM-DIMAP")
        print("Calibration done")

        ### SUBSET
        parameters = snappyconfigs.get_subset_config(AOI_WKT)
        subset_path = output_dir + file_name + "_" + date + "_subset_" + polarization
        subset_prdt = GPF.createProduct("Subset", parameters, calibrated_prdt)
        ProductIO.writeProduct(subset_prdt, subset_path, "BEAM-DIMAP")
        print("Subset done")

        ### SPECKLE FILTER
        parameters = snappyconfigs.get_speckle_filter_config()
        speckle_path = output_dir + file_name + "_" + date + "_speckle_" + polarization
        speckle_prdt = GPF.createProduct("Speckle-Filter", parameters, subset_prdt)
        ProductIO.writeProduct(speckle_prdt, speckle_path, "BEAM-DIMAP")
        print("Speckle filter done")

        ### TERRAIN CORRECTION
        parameters = snappyconfigs.get_terrain_correction_config()
        terrain = output_dir + file_name + "_" + date + "_corrected_" + polarization
        terrain_corrected_prdt = GPF.createProduct("Terrain-Correction", parameters, speckle_prdt)
        ProductIO.writeProduct(terrain_corrected_prdt, terrain, "GeoTIFF")
        # ProductIO.writeProduct(terrain_corrected_prdt, terrain + "_big", "GeoTIFF-BigTIFF")
        print("Terrain correction done")

        print("Done with " + polarization + " for " + folder)
        print()

now = datetime.datetime.now()
print("Finished at " + now.strftime("%Y-%m-%d %H:%M:%S"))
if usr_system == "Windows":
    import winsound
    duration = 1000  # milliseconds
    freq = 1000  # Hz
    winsound.Beep(freq, duration)
    winsound.Beep(freq, duration)