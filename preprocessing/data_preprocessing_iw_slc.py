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
preprocessing order depends on product type(slc,grd,raw) and product level(0,1,2)
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
import subprocess

from snappy import GPF
from snappy import ProductIO

from snappy_tools import snappyconfigs, snappyoperators as sp
from basicconfig import LC_WKT, POLARIZATIONS, SNAPHU_PATH
import filemanager

AOI_WKT = \
    "POLYGON((102.070752316744 14.565580568454624,102.36824148300377 14.565580568454624,102.36824148300377 14.322211910367955,102.070752316744 14.322211910367955,102.070752316744 14.565580568454624))"


GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

usr_system = platform.system()
input_dir, output_dir = filemanager.get_file_paths_based_on_os(platform.system(), filemanager.Product.slc)

toRun = input("Run program? (Y/N)")
if toRun == "Y" or toRun == "y":
    pass
else:
    print("Exiting...")
    exit(0)

gc.enable()


def call_snaphu_command(snaphu_path):
    try:
        with open(snaphu_path + "snaphu.conf") as f:
            snaphu_config_file = f.readlines()
            snaphu_cmd = ""
            for line in snaphu_config_file:
                if "snaphu -f" in line:
                    snaphu_cmd = line
                # elif "LOGFILE" in line:
                #     line = "#" + line
            # print(''.join(snaphu_config_file))
            # f.write(''.join(snaphu_config_file))

        snaphu_cmd = snaphu_cmd.replace("#", "").lstrip()
        logger.info(f'Command to run: {snaphu_cmd}')
    except IOError as e:
        logger.critical(f"Unable to open snaphu files for unwrapping. Check if snaphu export was successful and "
                        f"snaphu files exist at {snaphu_path}")
        exit(1)

    try:
        # navigate to correct dir
        os.chdir(snaphu_path)
        result = subprocess.run(snaphu_cmd, stdout=subprocess.PIPE)
        # logger.info(result)
        logger.info('Snaphu unwrapping success')
    except subprocess.CalledProcessError as e:
        logger.critical("Snaphu error output:\n", e.output)


# Testing using one master and one slave pair
# (make sure that the data is already unzipped)

# if ".SAFE" not in folder:
#     continue
# if "S1A_IW_SLC__1SDV_20190107T112033_20190107T112100_025371_02CF15_1237__subset.tif" != folder \
#         and "S1B_IW_SLC__1SDV_20190101T111958_20190101T112025_014300_01A9AA_5FE6__subset.tif" != folder:
#     continue

######################## COREGISTRATION ########################
logger.info("Start data preprocessing for iw slc")
master_file = "S1B_IW_SLC__1SDV_20190101T111958_20190101T112025_014300_01A9AA_5FE6.SAFE"
slave_file = "S1A_IW_SLC__1SDV_20190107T112033_20190107T112100_025371_02CF15_1237.SAFE"

input_file_name1 = input_dir + master_file
file_name1 = re.sub("\\..*$", "", master_file)
timestamp1 = master_file.split("_")[5]
date1 = timestamp1[:8]

input_file_name2 = input_dir + slave_file
file_name2 = re.sub("\\..*$", "", slave_file)
timestamp2 = slave_file.split("_")[5]
date2 = timestamp2[:8]

combined_name = timestamp1 + "_" + timestamp2

# Read in the Sentinel-1 data product:
sentinel_1_m = ProductIO.readProduct(output_dir + file_name1 + f"_top_sar_split_{POLARIZATIONS}.dim")
sentinel_1_s = ProductIO.readProduct(output_dir + file_name2 + f"_top_sar_split_{POLARIZATIONS}.dim")
logger.info("Read")

### BACK-GEOCODING
back_geocoded_prdt = sp.back_geocoding([sentinel_1_s, sentinel_1_m])

# ### ENHANCED SPECTRAL DIVERSITY
esd_prdt = sp.enhanced_spectral_diversity(back_geocoded_prdt)

######################## INTERFEROGRAM PROCESSING TO GET DINSAR ########################
### INTERFEROGRAM
interferogram_prdt = sp.interferogram(esd_prdt)

### TOPSAR DEBURST
deburst_prdt = sp.top_sar_deburst(interferogram_prdt, POLARIZATIONS)
deburst_path = output_dir + combined_name + f'_deburst_{POLARIZATIONS}'
ProductIO.writeProduct(deburst_prdt, deburst_path, "BEAM-DIMAP")
logger.info('Write done')

### TOPO PHASE REMOVAL
in_deburst_prdt = ProductIO.readProduct(deburst_path + '.dim')
tpr_prdt = sp.topo_phase_removal(in_deburst_prdt)

### MULTILOOK
multilook_prdt = sp.multilook(tpr_prdt)

# ### GOLDSTEIN PHASE FILTERING
goldstein_prdt = sp.goldstein_phase_filtering(multilook_prdt)
goldstein_path = output_dir + combined_name + f'_goldstein_{POLARIZATIONS}'

ProductIO.writeProduct(goldstein_prdt, goldstein_path, "BEAM-DIMAP")
logger.info('Write done')

####################### PHASE UNWRAPPING ########################
### SNAPHU EXPORT
in_goldstein_prdt = ProductIO.readProduct(goldstein_path + '.dim')
snaphu_output_path = SNAPHU_PATH + combined_name + f'_{POLARIZATIONS}' + '\\'
snaphu_export_prdt = sp.snaphu_export(in_goldstein_prdt, snaphu_output_path)
ProductIO.writeProduct(snaphu_export_prdt, snaphu_output_path, "Snaphu")
logger.info("Snaphu Export write done")

### Unwrapping
call_snaphu_command(snaphu_output_path)

unwrapped_phase_prdt = None
for file in os.listdir(snaphu_output_path):
    if file.endswith('.hdr') and 'UnwPhase_ifg' in file:
        unwrapped_phase_prdt = ProductIO.readProduct(snaphu_output_path + file)
if unwrapped_phase_prdt is None:
    logger.critical(f'Unwrapped phase product not found in {snaphu_output_path} for phase unwrapping')
    exit(1)

# ### SNAPHU IMPORT
snaphu_import_prdt = sp.snaphu_import([unwrapped_phase_prdt, in_goldstein_prdt])
snaphu_import_path = output_dir + combined_name + f'_snaphu_import_{POLARIZATIONS}'
ProductIO.writeProduct(snaphu_import_prdt, snaphu_import_path, "BEAM-DIMAP")

# ### PHASE TO DISPLACEMENT
# snaphu_import_prdt = ProductIO.readProduct(snaphu_import_path + '.dim')
# ptd_prdt = sp.phase_to_disp(snaphu_import_prdt)
# ptd_path = output_dir + combined_name + f'_ptd_{polarizations}'
# ProductIO.writeProduct(ptd_prdt, ptd_path, "BEAM-DIMAP")

### BandMaths
in_snaphu_import_prdt = ProductIO.readProduct(snaphu_import_path + '.dim')
unwrapped_phase_prdt_name = re.sub("\\..*$", "", unwrapped_phase_prdt.getName())
unwrapped_phase_prdt_name = unwrapped_phase_prdt_name.replace('UnwPhase', 'Unw_Phase')
unwrapped_phase_prdt_name = unwrapped_phase_prdt_name.replace('_VV', '')
vert_disp_prdt = sp.band_math(in_snaphu_import_prdt, 'vert_disp', f'({unwrapped_phase_prdt_name} * 0.056) / (-4 * PI * cos(rad(incident_angle)))')
# vert_disp_path = output_dir + combined_name + f'_vert_disp_subset_{polarizations}'
# ProductIO.writeProduct(vert_disp_prdt, vert_disp_path, "BEAM-DIMAP")

### GEOCODING / TERRAIN CORRECTION
terrain_corrected_prdt = sp.terrain_correction(vert_disp_prdt, snappyconfigs.UTM_WGS84, 5.0)

### SUBSET
subset_prdt = sp.subset(terrain_corrected_prdt, LC_WKT) # TODO: replace wkt with cropped one, have to change to read wkt from file next time
subset_path = output_dir + combined_name + f'_vert_disp_subset_{POLARIZATIONS}'
ProductIO.writeProduct(subset_prdt, subset_path, "BEAM-DIMAP")

logger.info("Completed")
if usr_system == "Windows":
    import winsound
    duration = 1000  # milliseconds
    freq = 1000  # Hz
    winsound.Beep(freq, duration)
    winsound.Beep(freq, duration)
