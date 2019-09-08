import snappy
import datetime
# For hpc
import sys
# sys.path.append('/home/svu/e0036687/.snap/snap-python')

from snappy import ProductIO, WKTReader
from snappy import HashMap

import os, gc
from snappy import GPF

UTM_WGS84_AUTO = 'PROJCS["UTM Zone 45 / World Geodetic System 1984",GEOGCS["World Geodetic System 1984",DATUM["World Geodetic System 1984",SPHEROID["WGS 84", 6378137.0, 298.257223563, AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich", 0.0, AUTHORITY["EPSG","8901"]],UNIT["degree", 0.017453292519943295],AXIS["Geodetic longitude", EAST],AXIS["Geodetic latitude", NORTH]],PROJECTION["Transverse_Mercator"],PARAMETER["central_meridian", 87.0],PARAMETER["latitude_of_origin", 0.0],PARAMETER["scale_factor", 0.9996],PARAMETER["false_easting", 500000.0],PARAMETER["false_northing", 0.0],UNIT["m", 1.0],AXIS["Easting", EAST],AXIS["Northing", NORTH]]'

GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()
# HashMap = snappy.jpy.get_type('java.util.HashMap')

# Now loop through all Sentinel-1 data sub folders that are located within a super folder
# (of course, make sure, that the data is already unzipped):

# For hpc
# parent_dir = '.\\'
# input_dir = parent_dir + 'original\\'
# output_dir = input_dir + 'processing\\'

parent_dir = 'D:\\ESA Tutorial\\'
# input_dir = parent_dir + 'Original\\'
# output_dir = parent_dir + 'Processing\\'

input_dir = parent_dir + 'Test\\'
output_dir = parent_dir + 'TestProc\\'

pols = ['VV']

toRun = raw_input('Run program? (Y/N)')
if toRun == 'Y' or toRun == 'y':
    pass
else:
    print('Exiting...')
    exit(0)

now = datetime.datetime.now()
print('Start data preprocessing at ' + now.strftime("%Y-%m-%d %H:%M:%S"))
print
'''
Does the following preprocessing steps for chosen prdt type (IW GRND level 1 prdt):
1. thermal noise removal
2. apply-orbit file
3. calibration
4. subset
5. speckle filter
6. terrain correction
7. write

preprocessing order depends on product type(slc,grnd,raw) and product level(0,1,2) 
'''

for folder in os.listdir(input_dir):
    gc.enable()

    # if '.SAFE' not in folder:
    #     continue
    if 'S1B_IW_GRDH_1SDV_20190302T111957_20190302T112022_015175_01C61A_9D6D.SAFE' != folder:
        continue

    input_file_name = input_dir + folder
    file_name = folder[:-5]
    timestamp = folder.split("_")[4]
    date = timestamp[:8]

    print('Current folder: ' + folder)
    # Read in the Sentinel-1 data product:
    sentinel_1 = ProductIO.readProduct(input_file_name + "\\manifest.safe")
    print(sentinel_1)

    # If polarization bands are available, split up your code to process VH and VV intensity data separately.
    # The first step is the calibration procedure by transforming the DN values to Sigma Naught respectively.
    # You can specify the parameters to input_file_name the Image in Decibels as well.

    for p in pols:
        polarization = p
        ### THERMAL NOISE REMOVAL
        # subset_sentinel_1 = ProductIO.readProduct(subset_path + '.dim')
        parameters = HashMap()
        parameters.put('removeThermalNoise', True)
        parameters.put('reIntroduceThermalNoise', False)

        noise_removal_path = output_dir + file_name + '_' + date + "_noise_removal_" + polarization
        noise_rem_prdt = GPF.createProduct("ThermalNoiseRemoval", parameters, sentinel_1)
        ProductIO.writeProduct(noise_rem_prdt, noise_removal_path, 'BEAM-DIMAP')
        print 'Thermal noise removal done'

        ### APPLY-ORBIT FILE
        parameters = HashMap()
        parameters.put('orbitType', 'Sentinel Precise (Auto Download)')
        parameters.put('polyDegree', 3)
        parameters.put('continueOnFail', True)

        apply_orbit_path = output_dir + file_name + '_' + date + "_orbit_" + polarization
        apply_orbit_prdt = GPF.createProduct("Apply-Orbit-File", parameters, noise_rem_prdt)
        ProductIO.writeProduct(apply_orbit_prdt, apply_orbit_path, 'BEAM-DIMAP')
        print 'Apply-orbit file done'

        ### CALIBRATION
        parameters = HashMap()
        parameters.put('outputSigmaBand', True)
        # parameters.put('sourceBands', 'Intensity_' + polarization)
        parameters.put('selectedPolarisations', polarization)
        parameters.put('outputImageScaleInDb', False)

        calib_path = output_dir + file_name + '_' + date + "_calibrate_" + polarization
        # calib_path = output_dir + 'test_' + date + "_calibrate_" + polarization
        calibrated_prdt = GPF.createProduct("Calibration", parameters, apply_orbit_prdt)
        # ProductIO.writeProduct(target_0, calib, 'GeoTIFF')
        ProductIO.writeProduct(calibrated_prdt, calib_path, 'BEAM-DIMAP')
        print 'Calibration done'

        ### SUBSET
        wkt = "POLYGON ((102.12635428857155 14.248290232074497, 102.53781291893677 14.327232114630814, 102.48940057780496 14.575151504929456, 102.0774759551546 14.496314998624996, 102.12635428857155 14.248290232074497))"

        geom = WKTReader().read(wkt)
        parameters = HashMap()
        parameters.put('geoRegion', geom)
        parameters.put('outputImageScaleInDb', False)

        subset_path = output_dir + file_name + '_' + date + "_subset_" + polarization
        # subset_path = output_dir + 'test_' + date + "_subset_" + polarization
        subset_prdt = GPF.createProduct("Subset", parameters, calibrated_prdt)

        # ProductIO.writeProduct(subset_prdt, subset_path, 'GeoTIFF')
        ProductIO.writeProduct(subset_prdt, subset_path, 'BEAM-DIMAP')
        print 'Subset done'

        ### SPECKLE FILTER
        parameters = HashMap()
        parameters.put('filter', 'Lee Sigma')
        parameters.put('filterSizeX', 3)
        parameters.put('filterSizeY', 3)
        parameters.put('dampingFactor', 2)
        parameters.put('estimateENL', True)
        parameters.put('enl', 1.0)
        parameters.put('numLooksStr', '1')
        parameters.put('windowSize', '7x7')
        parameters.put('targetWindowSizeStr', '3x3')
        parameters.put('sigmaStr', '0.9')
        parameters.put('anSize', 50)

        speckle_path = output_dir + file_name + '_' + date + "_speckle_" + polarization
        speckle_prdt = GPF.createProduct("Speckle-Filter", parameters, subset_prdt)
        ProductIO.writeProduct(speckle_prdt, speckle_path, 'BEAM-DIMAP')
        print 'Speckle filter done'

        ### TERRAIN CORRECTION
        parameters = HashMap()
        parameters.put('demResamplingMethod', 'BILINEAR_INTERPOLATION')
        parameters.put('imgResamplingMethod', 'BILINEAR_INTERPOLATION')
        parameters.put('demName', 'SRTM 3Sec')
        parameters.put('alignToStandardGrid', False)
        parameters.put('saveDEM', False)
        parameters.put('saveLatLon', False)
        parameters.put('saveIncidenceAngleFromEllipsoid', False)
        parameters.put('saveLocalIncidenceAngle', False)
        parameters.put('saveProjectedLocalIncidenceAngle', False)
        parameters.put('outputComplex', False)
        parameters.put('saveSelectedSourceBand', True)
        parameters.put('standardGridOriginX', 0.0)
        parameters.put('standardGridOriginY', 0.0)
        parameters.put('pixelSpacingInMeter', 10.0)
        parameters.put('nodataValueAtSea', True)
        parameters.put('saveSigmaNought', False)
        parameters.put('incidenceAngleForSigma0', 'Use projected local incidence angle from DEM')
        parameters.put('mapProjection', UTM_WGS84_AUTO)
        # parameters.put('sourceBands', 'Sigma0_' + polarization)

        terrain = output_dir + file_name + '_' + date + "_corrected_" + polarization
        # terrain = output_dir + 'test1' + '_' + date + "_corrected_" + polarization
        terrain_corrected_prdt = GPF.createProduct("Terrain-Correction", parameters, speckle_prdt)
        ProductIO.writeProduct(terrain_corrected_prdt, terrain, 'GeoTIFF')
        # ProductIO.writeProduct(terrain_corrected_prdt, terrain + '_big', 'GeoTIFF-BigTIFF')
        print 'Terrain correction done'

        print('Done with ' + polarization + ' for ' + folder)
        print

if 'win' in sys.platform:
    import winsound
    duration = 1000  # milliseconds
    freq = 1000  # Hz
    winsound.Beep(freq, duration)
    winsound.Beep(freq, duration)
now = datetime.datetime.now()
print('Finished at ' + now.strftime("%Y-%m-%d %H:%M:%S"))
