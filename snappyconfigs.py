from snappy import HashMap
from snappy import WKTReader

"""
This file contains parameter hash maps for snappy"s preprocessing operators:
1. thermal noise removal
2. apply-orbit file
3. calibration
4. subset
5. speckle filter
6. terrain correction
"""
UTM_WGS84_AUTO = "PROJCS[\"UTM Zone 45 / World Geodetic System 1984\",GEOGCS[\"World Geodetic System 1984\",DATUM[\"World " \
                 "Geodetic System 1984\",SPHEROID[\"WGS 84\", 6378137.0, 298.257223563, AUTHORITY[\"EPSG\",\"7030\"]]," \
                 "AUTHORITY[\"EPSG\",\"6326\"]],PRIMEM[\"Greenwich\", 0.0, AUTHORITY[\"EPSG\",\"8901\"]]," \
                 "UNIT[\"degree\", 0.017453292519943295],AXIS[\"Geodetic longitude\", EAST]," \
                 "AXIS[\"Geodetic latitude\", NORTH]],PROJECTION[\"Transverse_Mercator\"]," \
                 "PARAMETER[\"central_meridian\", 87.0],PARAMETER[\"latitude_of_origin\", 0.0]," \
                 "PARAMETER[\"scale_factor\", 0.9996],PARAMETER[\"false_easting\", 500000.0],PARAMETER[\"false_northing\", 0.0]," \
                 "UNIT[\"m\", 1.0],AXIS[\"Easting\", EAST],AXIS[\"Northing\", NORTH]]"


def get_thermal_noise_removal_config():
    parameters = HashMap()
    parameters.put("removeThermalNoise", True)
    parameters.put("reIntroduceThermalNoise", False)
    return parameters


def get_orbit_config():
    parameters = HashMap()
    parameters.put("orbitType", "Sentinel Precise (Auto Download)")
    parameters.put("polyDegree", 3)
    parameters.put("continueOnFail", True)
    return parameters


def get_calibration_config(polarization):
    parameters = HashMap()
    parameters.put("outputSigmaBand", True)
    parameters.put("selectedPolarisations", polarization)
    parameters.put("outputImageScaleInDb", False)
    return parameters


def get_subset_config(wkt):
    geom = WKTReader().read(wkt)
    parameters = HashMap()
    parameters.put("geoRegion", geom)
    parameters.put("outputImageScaleInDb", False)
    return parameters


def get_speckle_filter_config():
    parameters = HashMap()
    parameters.put("filter", "Lee Sigma")
    parameters.put("filterSizeX", 3)
    parameters.put("filterSizeY", 3)
    parameters.put("dampingFactor", 2)
    parameters.put("estimateENL", True)
    parameters.put("enl", 1.0)
    parameters.put("numLooksStr", "1")
    parameters.put("windowSize", "7x7")
    parameters.put("targetWindowSizeStr", "3x3")
    parameters.put("sigmaStr", "0.9")
    parameters.put("anSize", 50)
    return parameters


def get_terrain_correction_config():
    parameters = HashMap()
    parameters.put("demResamplingMethod", "BILINEAR_INTERPOLATION")
    parameters.put("imgResamplingMethod", "BILINEAR_INTERPOLATION")
    parameters.put("demName", "SRTM 3Sec")
    parameters.put("alignToStandardGrid", False)
    parameters.put("saveDEM", False)
    parameters.put("saveLatLon", False)
    parameters.put("saveIncidenceAngleFromEllipsoid", False)
    parameters.put("saveLocalIncidenceAngle", False)
    parameters.put("saveProjectedLocalIncidenceAngle", False)
    parameters.put("outputComplex", False)
    parameters.put("saveSelectedSourceBand", True)
    parameters.put("standardGridOriginX", 0.0)
    parameters.put("standardGridOriginY", 0.0)
    parameters.put("pixelSpacingInMeter", 10.0)
    parameters.put("nodataValueAtSea", True)
    parameters.put("saveSigmaNought", False)
    parameters.put("incidenceAngleForSigma0", "Use projected local incidence angle from DEM")
    parameters.put("mapProjection", UTM_WGS84_AUTO)
    return parameters
