import snappy
import datetime
# For hpc
import sys
# sys.path.append('/home/svu/e0036687/.snap/snap-python')

from snappy import ProductIO, WKTReader
from snappy import HashMap

import os, gc
from snappy import GPF

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
Does the following preprocessing steps:
1. calibration
2. subset
# 3. terrain correction
dep on product type, slc,grnd, raw 
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

        ### CALIBRATION
        parameters = HashMap()
        parameters.put('outputSigmaBand', True)
        # parameters.put('sourceBands', 'Intensity_' + polarization)
        parameters.put('selectedPolarisations', polarization)
        parameters.put('outputImageScaleInDb', False)

        calib = output_dir + file_name + '_' + date + "_calibrate_" + polarization
        # calib = output_dir + 'test_' + date + "_calibrate_" + polarization
        target_0 = GPF.createProduct("Calibration", parameters, sentinel_1)
        # ProductIO.writeProduct(target_0, calib, 'GeoTIFF')
        ProductIO.writeProduct(target_0, calib, 'BEAM-DIMAP')
        print 'Calibration done'

        # Next, specify a subset AOI to reduce the data amount and processing time.
        # The AOI specified by its outer polygon corners and is formatted through a Well Known Text (WKT).

        ### SUBSET

        calibration = ProductIO.readProduct(calib + ".dim")

        wkt = "POLYGON((91.13462713834258 23.503659930299406, 88.7222620230574 23.917065641765348, 88.43093071565514 22.417698128729405, 90.81621481093471 22.001211295818294, 91.13462713834258 23.503659930299406))"

        geom = WKTReader().read(wkt)
        parameters = HashMap()
        parameters.put('geoRegion', geom)
        parameters.put('outputImageScaleInDb', False)

        subset = output_dir + file_name + '_' + date + "_subset_" + polarization
        # subset = output_dir + 'test_' + date + "_subset_" + polarization
        target_1 = GPF.createProduct("Subset", parameters, calibration)

        # ProductIO.writeProduct(target_1, subset, 'GeoTIFF')
        ProductIO.writeProduct(target_1, subset, 'BEAM-DIMAP')
        print 'Subset done'

        # Apply a Range Doppler Terrain Correction to correct for layover and foreshortening effects, by using the
        # SRTM 3 arcsecond product (90m) that is downloaded automatically. You could also specify an own DEM product
        # with a higher spatial resolution from a local input_dir:

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
        # parameters.put('sourceBands', 'Sigma0_' + polarization)

        terrain = output_dir + file_name + '_' + date + "_corrected_" + polarization
        # terrain = output_dir + 'test1' + '_' + date + "_corrected_" + polarization
        target_2 = GPF.createProduct("Terrain-Correction", parameters, target_1)
        ProductIO.writeProduct(target_2, terrain, 'GeoTIFF')
        ProductIO.writeProduct(target_2, terrain + '_big', 'GeoTIFF-BigTIFF')
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
