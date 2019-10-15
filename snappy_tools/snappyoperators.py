import logging
from snappy import GPF

from snappy_tools import snappyconfigs

logger = logging.getLogger(__name__)


# Extract all operator funcs here for easy reuse. do it for ogp!
def top_sar_split(src, subswath, first_idx, last_idx, polarizations):
    parameters = snappyconfigs.get_topsar_split_config(subswath, first_idx, last_idx, polarizations)
    split_prdt = GPF.createProduct("TOPSAR-Split", parameters, src)
    logger.info("TOPSAR Split done")
    return split_prdt


def apply_orbit_file(src):
    parameters = snappyconfigs.get_orbit_config()
    apply_orbit_prdt = GPF.createProduct("Apply-Orbit-File", parameters, src)
    logger.info("Apply-orbit file done")
    return apply_orbit_prdt


def thermal_noise_removal(src):
    parameters = snappyconfigs.get_thermal_noise_removal_config()
    noise_rem_prdt = GPF.createProduct("ThermalNoiseRemoval", parameters, src)
    logger.info("Thermal noise removal done")
    return noise_rem_prdt


def calibration(src, polarizations):
    parameters = snappyconfigs.get_calibration_config(polarizations)
    calibrated_prdt = GPF.createProduct("Calibration", parameters, src)
    logger.info("Calibration done")
    return calibrated_prdt


def subset(src, wkt):
    parameters = snappyconfigs.get_subset_config(wkt)
    subset_prdt = GPF.createProduct("Subset", parameters, src)
    logger.info("Subset done")
    return subset_prdt


def speckle_filter(src):
    parameters = snappyconfigs.get_speckle_filter_config()
    speckle_prdt = GPF.createProduct("Speckle-Filter", parameters, src)
    logger.info("Speckle filter done")
    return speckle_prdt


def terrain_correction(src, projection, pixel_spacing):
    parameters = snappyconfigs.get_terrain_correction_config(projection, pixel_spacing)
    terrain_corrected_prdt = GPF.createProduct("Terrain-Correction", parameters, src)
    logger.info("Terrain correction done")
    return terrain_corrected_prdt


def create_stack(src: list):
    parameters = snappyconfigs.get_speckle_filter_config()
    stack_prdt = GPF.createProduct("CreateStack", parameters, src)
    logger.info("Create stack done")
    return stack_prdt


def cross_correlation(src):
    parameters = snappyconfigs.get_cross_correlation_config()
    cross_corr_prdt = GPF.createProduct("Cross-Correlation", parameters, src)
    logger.info("Cross correlation done")
    return cross_corr_prdt


def warp(src):
    parameters = snappyconfigs.get_warp_config()
    warp_prdt = GPF.createProduct("Warp", parameters, src)
    logger.info("Warp done")
    return warp_prdt


def linear_from_to_db(src):
    parameters = snappyconfigs.get_empty_config()
    db_prdt = GPF.createProduct("LinearToFromdB", parameters, src)
    logger.info("Linear To From dB done")
    return db_prdt


def band_math(src):
    parameters = snappyconfigs.get_band_math_config()
    msk_prdt = GPF.createProduct("BandMaths", parameters, src)
    logger.info("BandMaths done")
    return msk_prdt


def convert_datatype(src):
    parameters = snappyconfigs.get_convert_datatype_config()
    cnv_prdt = GPF.createProduct("Convert-Datatype", parameters, src)
    logger.info("Convert-Datatype done")
    return cnv_prdt


def glcm(src):
    parameters = snappyconfigs.get_glcm_config()
    glcm_prdt = GPF.createProduct("GLCM", parameters, src)
    logger.info("GLCM done")
    return glcm_prdt


def band_merge(src):
    parameters = snappyconfigs.get_empty_config()
    band_merge_prdt = GPF.createProduct("BandMerge", parameters, src)
    logger.info("BandMerge done")
    return band_merge_prdt
