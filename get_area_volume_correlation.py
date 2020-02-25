import json
import logging
import os
import platform
import re
from datetime import datetime
from functools import partial

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pyproj
from pandas.plotting import register_matplotlib_converters
from scipy import stats
from shapely.ops import transform
from shapely.wkt import loads

import basicconfig as config
from volumedata import get_volume_data


def convert_wkt_from_dd_to_m_to_polygon(wkt_in):
    projection = partial(pyproj.transform, pyproj.Proj(init="epsg:4326"), pyproj.Proj(init="epsg:32645"))
    wkt = loads(wkt_in)
    return transform(projection, wkt)


def convert_wkt_to_polygon(wkt_in):
    return loads(wkt_in)


def plot_area_volume(areas, volumes, dates):
    fig, ax1 = plt.subplots(1, 1, figsize=(12, 4))
    register_matplotlib_converters()
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d %b %Y'))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=30, ha="right")

    color = 'tab:blue'
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Water Volume (million cubic metres)', color=color)
    ax1.scatter(dates, volumes, color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:red'
    ax2.set_ylabel('Area (metre square)', color=color)  # we already handled the x-label with ax1
    ax2.scatter(dates, areas, color=color, marker='^')
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    fig.suptitle('Change in estimated area and in-situ water measurements', fontsize=16)
    plt.show()


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


mask_dir = config.GRD_PARENT_DIR + config.PROCESSING_DIR + config.GRD_MASK_DIR
data = open(mask_dir + 'data.json', 'r', encoding='utf-8')
mask_wkt_json = json.load(data)
data.close()

date_format = "%Y%m%d"

act_vol = []
dates = []
areas = []

for file in os.listdir(mask_dir):
    if '.json' in file:
        continue
    logger.info("Current folder: " + file)
    file_name = re.sub("\\..*$", "", file)
    date = datetime.strptime(file_name.split('_')[0], date_format).date()

    # get area
    area = convert_wkt_from_dd_to_m_to_polygon(mask_wkt_json[file_name]).area

    # get actual volume for particular date
    vol = get_volume_data.get_volume_for(date)

    # add to list
    dates.append(date)
    act_vol.append(vol)
    areas.append(area)

print(stats.pearsonr(areas, act_vol))
plot_area_volume(areas, act_vol, dates)

logger.info("Completed")
if platform.system() == "Windows":
    import winsound
    duration = 1000  # milliseconds
    freq = 1000  # Hz
    winsound.Beep(freq, duration)
    winsound.Beep(freq, duration)
