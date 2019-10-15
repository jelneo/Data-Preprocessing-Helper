import datetime
import platform

import os, gc

from snappy import ProductIO
from snappy import GPF

from snappy_tools import snappyconfigs

AOI_WKT = \
    "POLYGON((102.070752316744 14.565580568454624,102.36824148300377 14.565580568454624,102.36824148300377 14.322211910367955,102.070752316744 14.322211910367955,102.070752316744 14.565580568454624))"
polarizations = "VV"

GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

usr_system = platform.system()
if usr_system == "Windows":
    parent_dir = "D:\\FYP_IW\\"
    # input_dir = parent_dir + "Original\\"
    # output_dir = parent_dir + "Processing\\"
    input_dir = parent_dir + "Test\\"
    output_dir = parent_dir + "TestProc\\"
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
Does the following preprocessing steps for chosen prdt type (IW SLC level 1 prdt):

To reduce the area to AOI:
1. Read
2. TOPSAR-Split (different for S1A and S1B)
3. Apply-orbit file
4. Write (.dim)

* Note: Cannot subset or deburst before doing back-geocoding
* Subset always the last step else the areas cropped out will not be the same due to processing e.g. terrain correction

To get DInSAR:
Co-registration:
1. Read 1 (master) and 2 (slaves change to multiple)
2. Back-geocoding (inputs: 1 and 2)
3. Enhanced-spectral-diversity
Interferometric processing:
4. Interferogram
5. TOPSAR-Deburst
<<< Mosaic results of IW2 and IW1
<<< Subset
<<< cont from below so don't have to read from disk. ensure results at this pt is correct

Remove topographic induced phase from debursted interferogram:
6. Read
7. TopoPhaseRemoval
8. Multilook
9. GoldsteinPhaseFiltering
10. Write and SNAPHU (for phase unwrapping)

Phase unwrapping:
1. Read 1 and 2
2. SnaphuImport (inputs: 1 and 2)
3. PhaseToDisplacement
4. Geocoding (WGS84(DD))
5. Write
6. To overlay it as a layer in Google Earth: export as KMZ and open in Google Earth Pro
preprocessing order depends on product type(slc,grnd,raw) and product level(0,1,2) 
"""

# Testing using one master and one slave pair
# (make sure that the data is already unzipped)

# if ".SAFE" not in folder:
#     continue
# if "S1A_IW_SLC__1SDV_20190107T112033_20190107T112100_025371_02CF15_1237__subset.tif" != folder \
#         and "S1B_IW_SLC__1SDV_20190101T111958_20190101T112025_014300_01A9AA_5FE6__subset.tif" != folder:
#     continue

######################## COREGISTRATION ########################
master_file = "S1B_IW_SLC__1SDV_20190101T111958_20190101T112025_014300_01A9AA_5FE6.SAFE"
slave_file = "S1A_IW_SLC__1SDV_20190107T112033_20190107T112100_025371_02CF15_1237.SAFE"

input_file_name1 = input_dir + master_file
file_name1 = master_file[:-5]
timestamp1 = master_file.split("_")[4]
date1 = timestamp1[:8]

input_file_name2 = input_dir + slave_file
file_name2 = slave_file[:-5]
timestamp2 = slave_file.split("_")[4]
date2 = timestamp2[:8]

# Read in the Sentinel-1 data product:
sentinel_1_m = ProductIO.readProduct(input_file_name1 + manifest_extension)
sentinel_1_s = ProductIO.readProduct(input_file_name2 + manifest_extension)

### TOPSAR DEBURST
parameters = snappyconfigs.get_topsar_deburst_config("VV")
# deburst_path = output_dir + new_file_name + "_" + "deburst"
deburst_prdt1 = GPF.createProduct("TOPSAR-Deburst", parameters, sentinel_1_m)
# ProductIO.writeProduct(deburst_prdt, deburst_path, "BEAM-DIMAP")
print("TOPSAR-Deburst done")

# deburst_path = output_dir + new_file_name + "_" + "deburst"
deburst_prdt2 = GPF.createProduct("TOPSAR-Deburst", parameters, sentinel_1_s)
# ProductIO.writeProduct(deburst_prdt, deburst_path, "BEAM-DIMAP")
print("TOPSAR-Deburst done")

### APPLY-ORBIT FILE
parameters = snappyconfigs.get_orbit_config()
apply_orbit_path = output_dir + file_name1 + "_" + "orbit"
apply_orbit_prdt1 = GPF.createProduct("Apply-Orbit-File", parameters, deburst_prdt1)
# ProductIO.writeProduct(apply_orbit_prdt1, apply_orbit_path, "BEAM-DIMAP")
print("Apply-orbit file done 1")

apply_orbit_path = output_dir + file_name1 + "_" + "orbit"
apply_orbit_prdt2 = GPF.createProduct("Apply-Orbit-File", parameters, deburst_prdt2)
# ProductIO.writeProduct(apply_orbit_prdt1, apply_orbit_path, "BEAM-DIMAP")
print("Apply-orbit file done 1")

# ## SUBSET
# parameters = snappyconfigs.get_subset_config(AOI_WKT)
# subset_path = output_dir + file_name1 + "_" + "subset"
# subset_prdt1 = GPF.createProduct("Subset", parameters, apply_orbit_prdt1)
# ProductIO.writeProduct(subset_prdt1, subset_path, "BEAM-DIMAP")
# print("Subset done")
#
# subset_path = output_dir + file_name2 + "_" + "subset"
# subset_prdt2 = GPF.createProduct("Subset", parameters, apply_orbit_prdt2)
# ProductIO.writeProduct(subset_prdt2, subset_path, "BEAM-DIMAP")
# print("Subset done")

# ### TOPSAR SPLIT
# parameters = snappyconfigs.get_topsar_split_config("IW2","VV", 6, 8)
# topsar_split_path = output_dir + file_name1 + "_" + "split"
# split_prdt1 = GPF.createProduct("TOPSAR-Split", parameters, sentinel_1_m)
# # ProductIO.writeProduct(apply_orbit_prdt1, apply_orbit_path, "BEAM-DIMAP")
# print("TOPSAR Split done 1")
#
# parameters = snappyconfigs.get_topsar_split_config("IW2","VV", 8, 9)
# topsar_split_path = output_dir + file_name2 + "_" + "split"
# split_prdt2 = GPF.createProduct("TOPSAR-Split", parameters, sentinel_1_s)
# # ProductIO.writeProduct(apply_orbit_prdt1, apply_orbit_path, "BEAM-DIMAP")
# print("TOPSAR Split done 2")

# ### APPLY-ORBIT FILE
# parameters = snappyconfigs.get_orbit_config()
# apply_orbit_path = output_dir + file_name1 + "_" + "orbit"
# apply_orbit_prdt1 = GPF.createProduct("Apply-Orbit-File", parameters, split_prdt1)
# # ProductIO.writeProduct(apply_orbit_prdt1, apply_orbit_path, "BEAM-DIMAP")
# print("Apply-orbit file done 1")
#
# apply_orbit_path = output_dir + file_name2 + "_" + "orbit"
# apply_orbit_prdt2 = GPF.createProduct("Apply-Orbit-File", parameters, split_prdt2)
# # ProductIO.writeProduct(apply_orbit_prdt2, apply_orbit_path, "BEAM-DIMAP")
# print("Apply-orbit file done 2")

### BACK-GEOCODING
subset_prdt1 = ProductIO.readProduct(output_dir + file_name1 + "_" + "subset.dim")
subset_prdt2 = ProductIO.readProduct(output_dir + file_name2 + "_" + "subset.dim")
new_file_name = "pair"
parameters = snappyconfigs.get_back_geocoding_config()
back_geocoded_path = output_dir + new_file_name + "_" + "back_geocoding"
back_geocoded_prdt = GPF.createProduct("Back-Geocoding", parameters, [apply_orbit_prdt1, apply_orbit_prdt2])
# ProductIO.writeProduct(back_geocoded_prdt, back_geocoded_path, "BEAM-DIMAP")
print("Back-Geocoding done")

# ### ENHANCED SPECTRAL DIVERSITY
# parameters = snappyconfigs.get_esd_config()
# esd_path = output_dir + new_file_name + "_" + "esd"
# esd_prdt = GPF.createProduct("Enhanced-Spectral-Diversity", parameters, back_geocoded_prdt)
# # ProductIO.writeProduct(esd_prdt, esd_path, "BEAM-DIMAP")
# print("ESD done")
#
######################## INTERFEROGRAM PROCESSING TO GET DINSAR ########################
# ### INTERFEROGRAM
# parameters = snappyconfigs.get_interferogram_config()
# interferogram_path = output_dir + new_file_name + "_" + "interferogram"
# interferogram_prdt = GPF.createProduct("Interferogram", parameters, esd_prdt)
# # ProductIO.writeProduct(interferogram_prdt, interferogram_path, "BEAM-DIMAP")
# print("Interferogram done")
#
# ### TOPSAR DEBURST
# parameters = snappyconfigs.get_topsar_deburst_config("VV")
# deburst_path = output_dir + new_file_name + "_" + "deburst"
# deburst_prdt = GPF.createProduct("TOPSAR-Deburst", parameters, interferogram_prdt)
# ProductIO.writeProduct(deburst_prdt, deburst_path, "BEAM-DIMAP")
# print("TOPSAR-Deburst done")

### remove this portion later
# burst_file_name = "pair_deburst"
# burst_file = ProductIO.readProduct(output_dir + burst_file_name + ".dim")

# ### TOPO PHASE REMOVAL
# parameters = snappyconfigs.get_topo_phase_removal_config()
# tpr_path = output_dir + burst_file_name + "_" + "tpr"
# tpr_prdt = GPF.createProduct("TopoPhaseRemoval", parameters, burst_file)
# # ProductIO.writeProduct(tpr_prdt, tpr_path, "BEAM-DIMAP")
# print("TopoPhaseRemoval done")
#
# ### MULTILOOK
# parameters = snappyconfigs.get_multilook_config()
# multilook_path = output_dir + burst_file_name + "_" + "multilook"
# multilook_prdt = GPF.createProduct("Multilook", parameters, tpr_prdt)
# # ProductIO.writeProduct(multilook_prdt, multilook_path, "BEAM-DIMAP")
# print("Multilook done")
#
# ### GOLDSTEIN PHASE FILTERING
# parameters = snappyconfigs.get_goldstein_phase_filtering_config()
# goldstein_path = output_dir + burst_file_name + "_" + "goldstein"


# goldstein_prdt = GPF.createProduct("GoldsteinPhaseFiltering", parameters, multilook_prdt)
# ProductIO.writeProduct(goldstein_prdt, goldstein_path, "BEAM-DIMAP")
# print("Goldstein phase filtering done")

### SNAPHU EXPORT
def call_snaphu_command(snaphu_output_path):
    with open(snaphu_output_path + "\\snaphu.conf") as f:
        snaphu_config_file = f.readlines()
        snaphu_cmd = ""
        for line in snaphu_config_file:
            if "snaphu -f" in line:
                snaphu_cmd = line
            elif "LOGFILE" in line:
                line = "#" + line
        print(snaphu_config_file)
        f.write(snaphu_config_file.join())

    snaphu_cmd = snaphu_cmd.replace("#", "").lstrip()
    # navigate to correct dir
    cd_cmd = "cd " + snaphu_output_path
    # execute a command and then continue
    os.system('cmd /k "{}"'.format(cd_cmd))
    # execute a command and then terminate
    os.system('cmd /c "{}"'.format(snaphu_cmd))


# TODO: define better names for output products, have a gd naming convention
######################## PHASE UNWRAPPING ########################
# snaphu_output_path = output_dir + "Snaphu\\S1A_IW_SLC__1SDV_20190107T112033_20190107T112100_025371_02CF15_1237"
# call_snaphu_command(snaphu_output_path)
#
# input_1 = ProductIO.readProduct(goldstein_path + ".dim")  # goldstein path
# input_2 = ProductIO.readProduct(snaphu_output_path + "\\UnwPhase_ifg_VV_07Jan2019_01Jan2019.snaphu.hdr")
#
# ### SNAPHU IMPORT
# parameters = snappyconfigs.get_snaphu_import_config()
# snaphu_import_prdt = GPF.createProduct("SnaphuImport", parameters, [input_1, input_2])
# print("SnaphuImport done")
#
# ### PHASE TO DISPLACEMENT
# parameters = snappyconfigs.get_empty_config()
# ptd_prdt_path = output_dir + burst_file_name + "_" + "disp"
# ptd_prdt = GPF.createProduct("PhaseToDisplacement", parameters, snaphu_import_prdt)
# print("Phase to displacement done")
#
# ### GEOCODING / TERRAIN CORRECTION
# parameters = snappyconfigs.get_terrain_correction_config(snappyconfigs.UTM_WGS84, 10.0)
# terrain_corrected_path = output_dir + burst_file_name + "_" + "corrected"
# terrain_corrected_prdt = GPF.createProduct("Terrain-Correction", parameters, ptd_prdt)
# ProductIO.writeProduct(terrain_corrected_prdt, terrain_corrected_path, "BEAM-DIMAP")
# print("Terrain correction done")

now = datetime.datetime.now()
print("Finished at " + now.strftime("%Y-%m-%d %H:%M:%S"))
if usr_system == "Windows":
    import winsound

    duration = 1000  # milliseconds
    freq = 1000  # Hz
    winsound.Beep(freq, duration)
    winsound.Beep(freq, duration)
