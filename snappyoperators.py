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
