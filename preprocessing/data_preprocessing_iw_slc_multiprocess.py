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
import gc
import os
import platform
import re
import subprocess
import sys
from multiprocessing import Process

from snappy import GPF
from snappy import ProductIO

from snappy_tools import snappyconfigs, snappyoperators as sp
from basicconfig import LC_WKT, POLARIZATIONS, SNAPHU_PATH, COMMON_FILES_NAME
import filemanager
import basicconfig as config

default_pixel_spacing = 5.0
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

usr_system = platform.system()
input_dir, output_dir = filemanager.get_file_paths_based_on_os(usr_system, filemanager.Product.slc)
# interferogram_dir = output_dir
interferogram_dir = output_dir + config.INTERFEROGRAM_PATH
gc.enable()


def call_snaphu_command(snaphu_path):
    try:
        with open(snaphu_path + "snaphu.conf") as f:
            snaphu_config_file = f.readlines()
            snaphu_cmd = ""
            for line in snaphu_config_file:
                if "snaphu -f" in line:
                    snaphu_cmd = line

        snaphu_cmd = snaphu_cmd.replace("#", "").lstrip()
        logger.info(f'Command to run: {snaphu_cmd}')
    except IOError as e:
        logger.critical(f"Unable to open snaphu files for unwrapping. Check if snaphu export was successful and "
                        f"snaphu files exist at {snaphu_path}")
        exit(1)

    try:
        # navigate to correct dir
        os.chdir(snaphu_path)
        subprocess.run(snaphu_cmd, stdout=subprocess.PIPE)
        logger.info('Snaphu unwrapping success')
    except subprocess.CalledProcessError as e:
        logger.critical("Snaphu error output:\n", e.output)


def process_SLC_product(master, slave):
    # read list of files from common_file.txt in processing dir (already sorted in chronological order)
    ######################## COREGISTRATION ########################
    # master_file = "S1A_IW_SLC__1SDV_20190519T112034_20190519T112101_027296_03140A_CB6F"
    master_file = master[:-1]
    timestamp1 = master_file.split("_")[5]
    date1 = timestamp1[:8]

    # input_file_name2 = input_dir + slave_file
    slave_file = slave[:-1]  # -1 to remove \n at the end
    timestamp2 = slave_file.split("_")[5]
    date2 = timestamp2[:8]

    combined_name = timestamp1 + "_" + timestamp2
    logger.info("Current pair: " + combined_name)
    # Read in the Sentinel-1 data product:
    sentinel_1_m = ProductIO.readProduct(output_dir + master_file + f"_top_sar_split_{POLARIZATIONS}.dim")
    sentinel_1_s = ProductIO.readProduct(output_dir + slave_file + f"_top_sar_split_{POLARIZATIONS}.dim")
    logger.info("Read")

    ### BACK-GEOCODING
    back_geocoded_prdt = sp.back_geocoding([sentinel_1_s, sentinel_1_m])

    ### ENHANCED SPECTRAL DIVERSITY
    esd_prdt = sp.enhanced_spectral_diversity(back_geocoded_prdt)

    ######################## INTERFEROGRAM PROCESSING TO GET DINSAR ########################
    ### INTERFEROGRAM
    interferogram_prdt = sp.interferogram(esd_prdt)

    ### TOPSAR DEBURST
    deburst_prdt = sp.top_sar_deburst(interferogram_prdt, POLARIZATIONS)
    deburst_path = interferogram_dir + combined_name + f'_deburst_{POLARIZATIONS}'
    ProductIO.writeProduct(deburst_prdt, deburst_path, "BEAM-DIMAP")
    logger.info('Write done')

    ### TOPO PHASE REMOVAL
    in_deburst_prdt = ProductIO.readProduct(deburst_path + '.dim')
    tpr_prdt = sp.topo_phase_removal(in_deburst_prdt)

    ### MULTILOOK
    multilook_prdt = sp.multilook(tpr_prdt)

    ### GOLDSTEIN PHASE FILTERING
    goldstein_prdt = sp.goldstein_phase_filtering(multilook_prdt)
    goldstein_path = interferogram_dir + combined_name + f'_goldstein_{POLARIZATIONS}'

    ProductIO.writeProduct(goldstein_prdt, goldstein_path, "BEAM-DIMAP")
    logger.info('Write done')

    # ### GET COHERENCE
    # # terrain correction
    # tc_goldstein_prdt = sp.terrain_correction(goldstein_prdt, snappyconfigs.UTM_WGS84, default_pixel_spacing)
    # is_found = False
    # for src_band in tc_goldstein_prdt.getBands():
    #     band_name = src_band.getName()
    #     if band_name.startswith('coh'):
    #         coh_prdt = sp.subset(tc_goldstein_prdt, None, band_name)
    #         coh_path = interferogram_dir + combined_name + f'_coh_{POLARIZATIONS}'
    #         ProductIO.writeProduct(coh_prdt, coh_path, 'GeoTIFF')
    #         is_found = True
    #         break
    # if not is_found:
    #     logger.critical("No coherence band is found in interferogram product!")

    ####################### PHASE UNWRAPPING ########################
    ### SNAPHU EXPORT
    in_goldstein_prdt = ProductIO.readProduct(goldstein_path + '.dim')
    snaphu_output_path = interferogram_dir + SNAPHU_PATH + combined_name + f'_{POLARIZATIONS}' + '\\'
    snaphu_export_prdt = sp.snaphu_export(in_goldstein_prdt, snaphu_output_path)
    ProductIO.writeProduct(snaphu_export_prdt, snaphu_output_path, "Snaphu")
    logger.info("Snaphu Export done")

    ### Unwrapping
    call_snaphu_command(snaphu_output_path)

    unwrapped_phase_prdt = None
    for file in os.listdir(snaphu_output_path):
        if file.endswith('.hdr') and 'UnwPhase' in file:
            unwrapped_phase_prdt = ProductIO.readProduct(snaphu_output_path + file)
    if unwrapped_phase_prdt is None:
        logger.critical(f'Unwrapped phase product not found in {snaphu_output_path} for phase unwrapping')
        exit(1)

    # ### SNAPHU IMPORT
    snaphu_import_prdt = sp.snaphu_import([unwrapped_phase_prdt, in_goldstein_prdt])
    snaphu_import_path = interferogram_dir + combined_name + f'_snaphu_import_{POLARIZATIONS}'
    ProductIO.writeProduct(snaphu_import_prdt, snaphu_import_path, "BEAM-DIMAP")

    ### BandMaths
    in_snaphu_import_prdt = ProductIO.readProduct(snaphu_import_path + '.dim')
    unwrapped_phase_prdt_name = re.sub("\\..*$", "", unwrapped_phase_prdt.getName())
    unwrapped_phase_prdt_name = unwrapped_phase_prdt_name.replace('UnwPhase', 'Unw_Phase')
    unwrapped_phase_prdt_name = unwrapped_phase_prdt_name.replace('_VV', '')
    vert_disp_prdt = sp.band_math(in_snaphu_import_prdt, 'vert_disp',
                                  f'({unwrapped_phase_prdt_name} * 0.056) / (-4 * PI * cos(rad(incident_angle)))')

    ### GEOCODING / TERRAIN CORRECTION
    terrain_corrected_prdt = sp.terrain_correction(vert_disp_prdt, snappyconfigs.UTM_WGS84)

    ### SUBSET
    subset_prdt = sp.subset(terrain_corrected_prdt, LC_WKT)
    subset_path = interferogram_dir + combined_name + f'_vert_disp_subset_{POLARIZATIONS}'
    ProductIO.writeProduct(subset_prdt, subset_path, "BEAM-DIMAP")


if __name__ == '__main__':
    jobs = []
    with open(output_dir + COMMON_FILES_NAME) as f:
        try:
            files_to_process = f.readlines()
        except IOError:
            print("File read error")
    numCores = 2

    # # choose first image of every month:
    # prevMth = 0
    # monthly = []
    # for k in range(0, len(files_to_process)):
    #     f = files_to_process[k]
    #     ts = f.split("_")[5]
    #     date = ts[:8]
    #     mth = int(date[4:6])
    #     if mth != prevMth:
    #         monthly.append(files_to_process[k])
    #     prevMth = mth

    start = sys.argv[0]
    for j in range(start, start + numCores):
        # p = Process(target=process_SLC_product, args=(monthly[j], monthly[j + 1],))
        p = Process(target=process_SLC_product, args=(files_to_process[j], files_to_process[j + 1],))
        jobs.append(p)
        p.start()

