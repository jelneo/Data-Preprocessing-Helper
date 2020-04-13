import json
import math
from datetime import datetime
from functools import partial

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyproj
from pandas.plotting import register_matplotlib_converters
from scipy import stats
from shapely.ops import transform
from shapely.wkt import loads
from sklearn.metrics import mean_squared_error

import basicconfig as config

LAKE_CAPACITY = 159845 * 1233


def convert_wkt_from_dd_to_m_to_polygon(wkt_in):
    projection = partial(pyproj.transform, pyproj.Proj(init="epsg:4326"), pyproj.Proj(init="epsg:32629"))
    wkt = loads(wkt_in)
    return transform(projection, wkt)


with open("D:\\Texana\\Processing\\Area\\area.json", 'r', encoding='utf-8') as f:
    mask_wkt_json = json.load(f)
df = pd.read_csv("volumedata/texana.csv", parse_dates=['date'])
# print(df)
date_list = []
estimates = []
rec_dates = df['date'].values.flatten()
rec_dates = pd.to_datetime(rec_dates)
rec_dates = [d for d in rec_dates if 2016 <= d.year <= 2019]
recorded_areas = []
recorded_vols = []
accuracy = []

# no flood
nf_date_list = []
nf_estimates = []
nf_recorded_areas = []
nf_recorded_vols = []
nf_accuracy = []

# flood
f_date_list = []
f_estimates = []
f_recorded_areas = []
f_recorded_vols = []

for key in sorted(mask_wkt_json.keys()):
    date = datetime.strptime(key.split('_')[0], config.DATE_FORMAT).date()
    if date in rec_dates:
        recorded_area = df.loc[df['date'] == np.datetime64(date)]['surface_area'].values[0]
        if not np.isnan(recorded_area):
            date_list.append(date)
            estimates.append(mask_wkt_json[key])
            recorded_area = recorded_area * 4047
            recorded_areas.append(recorded_area)
            recorded_vol = df.loc[df['date'] == np.datetime64(date)]['reservoir_storage'].values[0] * 1233
            recorded_vols.append(recorded_vol)
            accuracy.append((recorded_area - mask_wkt_json[key]) / recorded_area * 100)
            if recorded_vol <= LAKE_CAPACITY:
                nf_date_list.append(date)
                nf_estimates.append(mask_wkt_json[key])
                nf_recorded_areas.append(recorded_area)
                nf_recorded_vols.append(recorded_vol)
                nf_accuracy.append((recorded_area - mask_wkt_json[key]) / recorded_area * 100)
            else:
                f_date_list.append(date)
                f_recorded_areas.append(recorded_area)
                f_recorded_vols.append(recorded_vol)
                f_estimates.append(mask_wkt_json[key])

# extract relevant recorded areas for verification
# convert acres to m^2
fig, ax = plt.subplots(1, 1, figsize=(13, 4))
register_matplotlib_converters()
ax.scatter(date_list, recorded_areas, label='in situ surface area')
# ax.scatter(f_date_list, f_recorded_areas, c='r', label='overflow')
ax.scatter(date_list, estimates, marker='x', label='estimated surface area')
# ax.scatter(f_date_list, f_estimates, c='b', marker='x', label='overflow estimate')
ax.set_ylabel("Surface area (m^2)")
ax.set_xlabel("Time")
# ax.set_ylim(bottom=0)
ax.legend()
plt.title("Comparison of estimated surface area and measured surface area of Lake Texana")

fig1, ax1 = plt.subplots(1, 1, figsize=(10, 3))
ax1.scatter(recorded_vols, recorded_areas, label='in situ surface area')
# ax1.scatter(f_recorded_vols, f_recorded_areas, c='r', label='overflow')
ax1.scatter(recorded_vols, estimates, marker='x', label='estimated surface area')
# ax1.scatter(f_recorded_vols, f_estimates, c='b', marker='x', label='overflow estimate')
ax1.set_ylabel("Surface area (m^2)")
ax1.set_xlabel("In situ water volume")
plt.title("In situ volume against surface area (estimated and in situ) of Lake Texana")
ax1.legend()
plt.tight_layout()

plt.show()
print('before removing flood data:')
print(f'correlation: {stats.pearsonr(estimates, recorded_areas)[0]}')
print(math.sqrt(mean_squared_error(recorded_areas, estimates)))
print(f'Mean accuracy: {np.array(accuracy).mean()}%')
print()

print('after removing flood data:')

fig, ax = plt.subplots(1, 1, figsize=(13, 4))
register_matplotlib_converters()
ax.scatter(nf_date_list, nf_recorded_areas, label='actual surface area')
ax.scatter(nf_date_list, nf_estimates, marker='x', label='estimated surface area')
ax.set_ylabel("Surface area (m^2)")
ax.set_xlabel("Time")
# ax.set_ylim(bottom=0)
ax.legend()
plt.title("Estimated surface area vs Measured Surface Area of Lake Texana (Without overflow)")

fig1, ax1 = plt.subplots(1, 1, figsize=(10, 3))
ax1.scatter(nf_recorded_vols, nf_recorded_areas, label='in situ surface area')
ax1.scatter(nf_recorded_vols, nf_estimates, marker='x', label='estimated surface area')
ax1.set_ylabel("Surface area (m^2)")
ax1.set_xlabel("In-situ water volume")
plt.title("Surface area (estimated and in-situ) vs Measured Surface Area of Lake Texana (Without overflow)")
ax1.legend()
plt.tight_layout()

plt.show()
print(f'correlation: {stats.pearsonr(nf_estimates, nf_recorded_areas)[0]}')
print(math.sqrt(mean_squared_error(nf_recorded_areas, nf_estimates)))
print(f'Mean accuracy: {np.array(nf_accuracy).mean()}%')
print(date_list)