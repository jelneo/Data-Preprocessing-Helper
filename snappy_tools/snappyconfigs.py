from snappy import HashMap
from snappy import WKTReader
from snappy import jpy

SRTM1SEC = "SRTM 1Sec HGT"

UTM_WGS84_AUTO = "PROJCS[\"UTM Zone 45 / World Geodetic System 1984\",GEOGCS[\"World Geodetic System 1984\",DATUM[\"World " \
                 "Geodetic System 1984\",SPHEROID[\"WGS 84\", 6378137.0, 298.257223563, AUTHORITY[\"EPSG\",\"7030\"]]," \
                 "AUTHORITY[\"EPSG\",\"6326\"]],PRIMEM[\"Greenwich\", 0.0, AUTHORITY[\"EPSG\",\"8901\"]]," \
                 "UNIT[\"degree\", 0.017453292519943295],AXIS[\"Geodetic longitude\", EAST]," \
                 "AXIS[\"Geodetic latitude\", NORTH]],PROJECTION[\"Transverse_Mercator\"]," \
                 "PARAMETER[\"central_meridian\", 87.0],PARAMETER[\"latitude_of_origin\", 0.0]," \
                 "PARAMETER[\"scale_factor\", 0.9996],PARAMETER[\"false_easting\", 500000.0],PARAMETER[\"false_northing\", 0.0]," \
                 "UNIT[\"m\", 1.0],AXIS[\"Easting\", EAST],AXIS[\"Northing\", NORTH]]"

EPSG_32645 = 'EPSG:32645'
UTM_WGS84 = "GEOGCS[\"WGS84(DD)\",DATUM[\"WGS84\",SPHEROID[\"WGS84\", 6378137.0, 298.257223563]]," \
            "PRIMEM[\"Greenwich\", 0.0],UNIT[\"degree\", 0.017453292519943295],AXIS[\"Geodetic longitude\", EAST]," \
            "AXIS[\"Geodetic latitude\", NORTH]] "

"""
This file contains parameter hash maps for snappy"s preprocessing operators
"""


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


def get_calibration_config(polarization: str):
    parameters = HashMap()
    parameters.put("outputSigmaBand", True)
    parameters.put("selectedPolarisations", polarization)
    parameters.put("outputImageScaleInDb", False)
    return parameters


def get_subset_config(wkt):
    geom = WKTReader().read(wkt)
    parameters = HashMap()
    parameters.put("geoRegion", geom)
    parameters.put("copyMetadata", True)
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


def get_terrain_correction_config(map_projection, pixel_spacing_in_meter: float):
    parameters = HashMap()
    parameters.put("demResamplingMethod", "BILINEAR_INTERPOLATION")
    parameters.put("imgResamplingMethod", "BILINEAR_INTERPOLATION")
    parameters.put("externalDEMApplyEGM", True)
    parameters.put("externalDEMNoDataValue", 0.0)
    parameters.put("demName", SRTM1SEC)  # ~25 to 30m
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
    parameters.put("pixelSpacingInMeter", pixel_spacing_in_meter)
    parameters.put("nodataValueAtSea", True)
    parameters.put("outputComplex", False)
    parameters.put("saveSigmaNought", False)
    parameters.put("incidenceAngleForSigma0", "Use projected local incidence angle from DEM")
    parameters.put("mapProjection", map_projection)
    return parameters


def get_topsar_deburst_config(polarizations):
    parameters = HashMap()
    parameters.put("selectedPolarisations", polarizations)
    return parameters


def get_topsar_split_config(subswath: str, first, last, polarizations):
    parameters = HashMap()
    parameters.put("subswath", subswath)
    parameters.put("selectedPolarisations", polarizations)
    parameters.put("firstBurstIndex", first)
    parameters.put("lastBurstIndex", last)
    return parameters


def get_back_geocoding_config():
    parameters = HashMap()
    parameters.put("demName", SRTM1SEC)
    parameters.put("demResamplingMethod", "BICUBIC_INTERPOLATION")
    parameters.put("externalDEMNoDataValue", 0.0)
    parameters.put("resamplingType", "BISINC_5_POINT_INTERPOLATION")
    parameters.put("maskOutAreaWithoutElevation", True)
    parameters.put("outputRangeAzimuthOffset", False)
    parameters.put("outputDerampDemodPhase", True)
    parameters.put("disableReramp", False)
    return parameters


def get_esd_config():
    parameters = HashMap()
    parameters.put("fineWinWidthStr", "512")
    parameters.put("fineWinHeightStr", "512")
    parameters.put("fineWinAccAzimuth", "16")
    parameters.put("fineWinAccRange", "16")
    parameters.put("fineWinOversampling", "128")
    parameters.put("xCorrThreshold", "0.1")
    parameters.put("cohThreshold", "0.15")
    parameters.put("numBlocksPerOverlap", "10")
    parameters.put("useSuppliedRangeShift", False)
    parameters.put("overallRangeShift", "0.0")
    parameters.put("useSuppliedAzimuthShift", False)
    parameters.put("overallAzimuthShift", "0.0")
    return parameters


def get_interferogram_config():
    parameters = HashMap()
    parameters.put("subtractFlatEarthPhase", True)
    parameters.put("srpPolynomialDegree", 5)
    parameters.put("srpNumberPoints", 501)
    parameters.put("orbitDegree", 3)
    parameters.put("includeCoherence", True)
    parameters.put("cohWinAz", 10)
    parameters.put("cohWinRg", 2)
    parameters.put("squarePixel", True)
    parameters.put("subtractTopographicPhase", False)
    parameters.put("demName", SRTM1SEC)
    parameters.put("externalDEMNoDataValue", 0.0)
    parameters.put("externalDEMApplyEGM", True)
    parameters.put("tileExtensionPercent", "100")
    parameters.put("outputElevation", False)
    parameters.put("outputLatLon", False)
    return parameters


def get_topo_phase_removal_config():
    parameters = HashMap()
    parameters.put("demName", SRTM1SEC)
    parameters.put("orbitDegree", 3)
    parameters.put("externalDEMNoDataValue", 0.0)
    parameters.put("tileExtensionPercent", "100")
    parameters.put("outputTopoPhaseBand", True)
    parameters.put("outputElevationBand", False)
    parameters.put("outputLatLonBands", False)
    return parameters


def get_multilook_config():
    parameters = HashMap()
    parameters.put("nRgLooks", 6)
    parameters.put("nAzLooks", 2)
    parameters.put("outputIntensity", False)
    parameters.put("grSquarePixel", True)
    return parameters


def get_goldstein_phase_filtering_config():
    parameters = HashMap()
    parameters.put("alpha", 1.0)
    parameters.put("FFTSizeString", "128")
    parameters.put("windowSizeString", "3")
    parameters.put("useCoherenceMask", False)
    parameters.put("coherenceThreshold", 0.3)
    return parameters


def get_snaphu_export_config(folder):
    parameters = HashMap()
    parameters.put("targetFolder", folder)
    parameters.put("statCostMode", "DEFO")
    parameters.put("initMethod", "MCF")
    parameters.put("numberOfTileRows", 1)
    parameters.put("numberOfTileCols", 1)
    parameters.put("numberOfProcessors", 4)
    parameters.put("rowOverlap", 0)
    parameters.put("colOverlap", 0)
    parameters.put("tileCostThreshold", 500)
    return parameters


def get_snaphu_import_config():
    parameters = HashMap()
    parameters.put("doNotKeepWrapped", True)
    return parameters


def get_create_stack_config():
    parameters = HashMap()
    parameters.put("resamplingType", "NONE")
    parameters.put("masterBands", "Sigma0_VH")
    parameters.put("extent", "Master")
    parameters.put("initialOffsetMethod", "Orbit")
    return parameters


def get_cross_correlation_config():
    parameters = HashMap()
    parameters.put("numGCPtoGenerate", 2000)
    parameters.put("coarseRegistrationWindowWidth", 128)
    parameters.put("coarseRegistrationWindowHeight", 128)
    parameters.put("rowInterpFactor", 4)
    parameters.put("columnInterpFactor", 4)
    parameters.put("maxIteration", 10)
    parameters.put("gcpTolerance", 0.25)
    parameters.put("applyFineRegistration", True)
    parameters.put("inSAROptimized", True)
    parameters.put("fineRegistrationWindowWidth", 32)
    parameters.put("fineRegistrationWindowHeight", 32)
    parameters.put("fineRegistrationWindowAccAzimuth", 16)
    parameters.put("fineRegistrationWindowAccRange", 16)
    parameters.put("fineRegistrationOversampling", 16)
    parameters.put("coherenceWindowSize", 3)
    parameters.put("coherenceThreshold", 0.6)
    parameters.put("useSlidingWindow", False)
    parameters.put("computeOffset", False)
    parameters.put("onlyGCPsOnLand", False)
    return parameters


def get_warp_config():
    parameters = HashMap()
    parameters.put("rmsThreshold", 0.05)
    parameters.put("warpPolynomialOrder", 1)
    parameters.put("interpolationMethod", "Cubic convolution (6 points)")
    parameters.put("demRefinement", False)
    parameters.put("demRefinement", False)
    parameters.put("demName", SRTM1SEC)
    parameters.put("excludeMaster", False)
    parameters.put("openResidualsFile", False)
    return parameters


def get_empty_config():
    return HashMap()


def get_band_math_config(band_name, expression):
    parameters = HashMap()
    band_descriptor = jpy.get_type('org.esa.snap.core.gpf.common.BandMathsOp$BandDescriptor')
    target_band = band_descriptor()
    target_band.name = band_name
    target_band.type = 'float32'
    target_band.expression = expression
    target_bands = jpy.array('org.esa.snap.core.gpf.common.BandMathsOp$BandDescriptor', 1)
    target_bands[0] = target_band
    parameters.put('targetBands', target_bands)
    return parameters


def get_convert_datatype_config():
    parameters = HashMap()
    parameters.put("targetDataType", "float32")
    parameters.put("targetScalingStr", "Logarithmic")
    parameters.put("targetNoDataValue", "NaN")
    return parameters


def get_glcm_config():
    parameters = HashMap()
    parameters.put("windowSizeStr", "11x11")
    parameters.put("angleStr", "ALL")
    parameters.put("quantizerStr", "Probabilistic Quantizer")
    parameters.put("quantizationLevelsStr", "32")
    parameters.put("displacement", 4)
    # features of GLCM
    parameters.put("outputContrast", False)
    parameters.put("outputDissimilarity", False)
    parameters.put("outputHomogeneity", False)
    parameters.put("outputASM", False)
    parameters.put("outputEnergy", False)
    parameters.put("outputMAX", False)
    parameters.put("outputEntropy", False)
    parameters.put("outputMean", True)
    parameters.put("outputVariance", True)
    parameters.put("outputCorrelation", False)
    return parameters
