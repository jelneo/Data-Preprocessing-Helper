import os
from snappy import ProductIO, ProductUtils
from snappy import GPF

import snappyconfigs


# Extract all operator funcs here for easy reuse. do it for ogp!
def top_sar_split(src, subswath, first_idx, last_idx, polarizations):
    parameters = snappyconfigs.get_topsar_split_config(subswath, first_idx, last_idx, polarizations)
    split_prdt = GPF.createProduct("TOPSAR-Split", parameters, src)
    print("TOPSAR Split done")
    return split_prdt


def apply_orbit_file(src):
    parameters = snappyconfigs.get_orbit_config()
    apply_orbit_prdt = GPF.createProduct("Apply-Orbit-File", parameters, src)
    print("Apply-orbit file done")
    return apply_orbit_prdt


def thermal_noise_removal(src):
    parameters = snappyconfigs.get_thermal_noise_removal_config()
    noise_rem_prdt = GPF.createProduct("ThermalNoiseRemoval", parameters, src)
    print("Thermal noise removal done")
    return noise_rem_prdt


def calibration(src, polarizations):
    parameters = snappyconfigs.get_calibration_config(polarizations)
    calibrated_prdt = GPF.createProduct("Calibration", parameters, src)
    print("Calibration done")
    return calibrated_prdt


def subset(src, wkt):
    parameters = snappyconfigs.get_subset_config(wkt)
    subset_prdt = GPF.createProduct("Subset", parameters, src)
    print("Subset done")
    return subset_prdt


def speckle_filter(src):
    parameters = snappyconfigs.get_speckle_filter_config()
    speckle_prdt = GPF.createProduct("Speckle-Filter", parameters, src)
    print("Speckle filter done")
    return speckle_prdt


def terrain_correction(src, projection, pixel_spacing):
    parameters = snappyconfigs.get_terrain_correction_config(projection, pixel_spacing)
    terrain_corrected_prdt = GPF.createProduct("Terrain-Correction", parameters, src)
    print("Terrain correction done")
    return terrain_corrected_prdt


def create_stack(src: list):
    parameters = snappyconfigs.get_speckle_filter_config()
    stack_prdt = GPF.createProduct("CreateStack", parameters, src)
    print("Create stack done")
    return stack_prdt


def cross_correlation(src):
    parameters = snappyconfigs.get_cross_correlation_config()
    cross_corr_prdt = GPF.createProduct("Cross-Correlation", parameters, src)
    print("Cross correlation done")
    return cross_corr_prdt


def warp(src):
    parameters = snappyconfigs.get_warp_config()
    warp_prdt = GPF.createProduct("Warp", parameters, src)
    print("Warp done")
    return warp_prdt


def linear_from_to_db(src):
    parameters = snappyconfigs.get_empty_config()
    db_prdt = GPF.createProduct("LinearToFromdB", parameters, src)
    print("Linear To From dB done")
    return db_prdt


def band_math(src):
    parameters = snappyconfigs.get_band_math_configs()
    msk_prdt = GPF.createProduct("BandMaths", parameters, src)
    print("BandMaths done")
    return msk_prdt
