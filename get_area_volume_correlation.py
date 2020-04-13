import json
import logging
import math
import platform
from datetime import datetime
from functools import partial

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyproj
from pandas.plotting import register_matplotlib_converters
from scipy import stats
from shapely.ops import transform
from shapely.wkt import loads
from sklearn import linear_model
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures

import basicconfig as config
from volumedata import volume_data


def convert_wkt_from_dd_to_m_to_polygon(wkt_in):
    projection = partial(pyproj.transform, pyproj.Proj(init="epsg:4326"), pyproj.Proj(init="epsg:32645"))
    wkt = loads(wkt_in)
    return transform(projection, wkt)


def convert_wkt_to_polygon(wkt_in):
    return loads(wkt_in)


def lc_f(x):
    return x**5 * -3.45029849e-05 + x**4 * -1.03694521e-02 + x**3 * 1.32219950e+01 + x**2 * -3.43262465e+03 + x * 4.06867333e+05 + 4092039.14152627


def lt_f(x):
    return x * 0.06990723 + 23929881.39967912


def plot_x_y_rs(x, y, x_test, y_test, x_label, y_label, title):
    data = [(x, y) for x, y in zip(x, y)]
    data = sorted(data, key=lambda tup: tup[0])
    x_sorted = [a[0] for a in data]
    y_sorted = [a[1] for a in data]

    test_data = [(a, b) for a, b in zip(x_test, y_test)]
    test_data = sorted(test_data, key=lambda tup: tup[0])
    x_t_sorted = [a[0] for a in test_data]
    y_t_sorted = [a[1] for a in test_data]
    fig, ax = plt.subplots(1, 1, figsize=(10, 3))
    ax.scatter(x, y, c='green', label='2016-2019 data (training)')
    ax.scatter(x_t_sorted, y_t_sorted, c='r', label='2020 data (test)')
    ax.plot(x_sorted, [lc_f(v) for v in x_sorted], c='blue', label="regression line")
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.legend()
    plt.title(title)
    print('mae: %.2f' % (math.sqrt(mean_absolute_error(y_t_sorted, [lc_f(v) for v in x_t_sorted]))))
    print('rmse: %.2f' % (math.sqrt(mean_squared_error(y_t_sorted, [lc_f(v) for v in x_t_sorted]))))
    print('nrmse (mean): %.2f' % (math.sqrt(mean_squared_error(y_t_sorted, [lc_f(v) for v in x_t_sorted])) / np.array(y_t_sorted).std()))
    print(f'correlation: {stats.pearsonr([lc_f(v) for v in x_t_sorted], y_t_sorted)[0]}')
    plt.show()


def plot_x_y_rs_texana(x, y, x_o, y_o, x_label, y_label, title):
    data = [(x, y) for x, y in zip(x, y)]
    data = sorted(data, key=lambda tup: tup[0])
    x_sorted = [a[0] for a in data]
    y_sorted = [a[1] for a in data]

    test_data = [(a, b) for a, b in zip(x_o, y_o)]
    test_data = sorted(test_data, key=lambda tup: tup[0])
    x_o_sorted = [a[0] for a in test_data]
    y_o_sorted = [a[1] for a in test_data]
    fig, ax = plt.subplots(1, 1, figsize=(10, 3))
    ax.scatter(x, y, c='green', label='estimated surface area')
    ax.scatter(x_o_sorted, y_o_sorted, c='r', label='actual surface area')
    ax.plot(x_sorted, [lt_f(v) for v in x_sorted], c='blue', label="regression line")
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.legend()
    plt.title(title)
    print(len([lt_f(v) for v in x_o_sorted]))
    print(len(y_o_sorted))
    print(f'y_pred: {[lt_f(v) for v in x_o_sorted]}')
    print(f'y_act: {y_o_sorted}')
    print('mae: %.2f' % (math.sqrt(mean_absolute_error(y_o_sorted, [lt_f(v) for v in x_o_sorted]))))
    print(f'correlation: {stats.pearsonr([lt_f(v) for v in x_o_sorted], y_o_sorted)[0]}')
    plt.show()


def find_optimal_alpha(x, y, degrees):
    data = [(a, b) for a, b in zip(x, y)]
    data = sorted(data, key=lambda tup: tup[0])
    x_sorted = [t[0] for t in data]
    y_sorted = [t[1] for t in data]
    y_reshape = np.array(y_sorted).reshape(-1, 1)
    x_reshape = np.array(x_sorted).reshape(-1, 1)
    for count, degree in enumerate(degrees):
        model = make_pipeline(PolynomialFeatures(degree), linear_model.RidgeCV(alphas=[0, 0.1, 1.0, 5.0, 10.0, 15.0, 25.0, 50.0], cv=10))
        model.fit(x_reshape, y_reshape)
        y_plot = model.predict(x_reshape)
        print(f'degree: {degree}')
        print(f'best alpha: {model.steps[1][1].alpha_}')
        print(model.steps[1][1].coef_)
        print(model.steps[1][1].intercept_)
        print('rmse: %.2f' % math.sqrt(mean_squared_error(y_sorted, y_plot)))


def plot_x_y_rs_experiment(x, y, x_label, y_label, title):
    fig1, ax1 = plt.subplots(1, 1, figsize=(10, 3))
    ax1.scatter(x, y, c='green')
    fig2, ax2 = plt.subplots(1, 1, figsize=(10, 3))
    ax2.scatter(x, y, c='green')
    # zip and sort tuples based on vol (x-axis) to plot a proper line graph
    data = [(a, b) for a, b in zip(x, y)]
    data = sorted(data, key=lambda tup: tup[0])
    x_sorted = [t[0] for t in data]
    y_sorted = [t[1] for t in data]
    y_reshape = np.array(y_sorted).reshape(-1, 1)
    x_reshape = np.array(x_sorted).reshape(-1, 1)
    # colors = ['gray', 'yellow', 'blue', 'red', 'magenta']

    for count, degree in enumerate([1, 2, 3, 4, 5, 6, 7, 8]):
        model = make_pipeline(PolynomialFeatures(degree), linear_model.LinearRegression())
        # model = make_pipeline(PolynomialFeatures(degree), linear_model.RidgeCV(alphas=[0.1, 1.0, 5.0, 10.0, 15.0], cv=10))
        model.fit(x_reshape, y_reshape)
        y_plot = model.predict(x_reshape)
        if degree < 5:
            ax1.plot(x_sorted, y_plot, label="degree %d" % degree, linewidth=(8 - (degree - 1)))
        else:
            ax2.plot(x_sorted, y_plot, label="degree %d" % degree, linewidth=(8 - (degree - 5)))
        ax1.scatter(recorded_vol, recorded_areas)
        ax1.legend(loc=2)
        ax2.legend(loc=2)
        # Print the model's coefficients.
        print(f"degree: {degree}")
        print(model.steps[1][1].coef_)
        print(model.steps[1][1].intercept_)
        # print(f'best alpha: {model.steps[1][1].alpha_}')
        print('rmse: %.2f' % math.sqrt(mean_squared_error(y_sorted, y_plot)))
    ax1.set_xlabel(x_label)
    ax1.set_ylabel(y_label)
    plt.title(title)

    ax2.set_xlabel(x_label)
    ax2.set_ylabel(y_label)
    plt.title(title)
    plt.show()


def piecewise_linear(x, x0, x1, b, k1, k2, k3):
    condlist = [x < x0, (x >= x0) & (x < x1), x >= x1]
    funclist = [lambda x: k1 * x + b, lambda x: k1 * x + b + k2 * (x - x0),
                lambda x: k1 * x + b + k2 * (x - x0) + k3 * (x - x1)]
    return np.piecewise(x, condlist, funclist)


def plot_area_volume(areas, volumes, dates):
    fig, ax1 = plt.subplots(1, 1, figsize=(13, 4))
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
    ax2.scatter(dates, areas, color=color, marker='x')
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    fig.suptitle('Time series of estimated surface area and in-situ water measurements', fontsize=16)
    plt.show()


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(name)s: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


mask_2016_dir = config.GRD_PARENT_DIR + "Processing_2016\\" + config.GRD_MASK_DIR
mask_2017_dir = config.GRD_PARENT_DIR + "Processing_2017\\" + config.GRD_MASK_DIR
mask_2018_dir = config.GRD_PARENT_DIR + "Processing_2018\\" + config.GRD_MASK_DIR
mask_2019_dir = config.GRD_PARENT_DIR + config.PROCESSING_DIR + config.GRD_MASK_DIR
mask_2020_dir = config.GRD_PARENT_DIR + "Processing_2020\\" + config.GRD_MASK_DIR


act_vol = []
dates = []
areas = []
test_x = []
test_y = []
all_data_masks_dir = [mask_2016_dir, mask_2017_dir, mask_2018_dir, mask_2019_dir, mask_2020_dir]
for mask_dir in all_data_masks_dir:
    data = open(mask_dir + 'data.json', 'r', encoding='utf-8')
    mask_wkt_json = json.load(data)
    data.close()
    for key in mask_wkt_json.keys():
        if '.json' in key:
            continue
        logger.info("Current folder: " + key)
        date = datetime.strptime(key.split('_')[0], config.DATE_FORMAT).date()

        # get area
        area = convert_wkt_from_dd_to_m_to_polygon(mask_wkt_json[key]).area

        # get actual volume for particular date
        vol = volume_data.get_volume_for_date(date)

        # add to list
        if '2020' in mask_dir:
            test_y.append(area)
            test_x.append(vol)
        else:
            # dates.append(date)
            act_vol.append(vol)
            areas.append(area)

print(f'y_true = {test_y}')
print(f'y_prd = {[f(v) for v in test_x]}')


print(f'correlation: {stats.pearsonr(areas, act_vol)}')
plot_area_volume(areas, act_vol, dates)

plot_x_y_rs_experiment(act_vol, areas, 'Actual volume (m^3)', 'Estimated surface area (m^2)', 'Relationship between surface area and volume for Lam Chae reservoir')
find_optimal_alpha(act_vol, areas, [2, 3, 4, 5, 6])
plot_x_y_rs(act_vol, areas, test_x, test_y, 'In-situ volume (m^3)', 'Estimated surface area (m^2)', 'Relationship between surface area and volume for Lam Chae reservoir')


with open("D:\\Texana\\Processing\\Area\\area.json", 'r', encoding='utf-8') as f:
    mask_wkt_json = json.load(f)
df = pd.read_csv("C:\\Users\\Jelena\\Data-Preprocessing-Helper\\volumedata\\texana.csv", parse_dates=['date'])
estimates_for_vol = []
estimates_for_height = []
rec_dates = df['date'].values.flatten()
rec_dates = pd.to_datetime(rec_dates)
rec_dates = [d for d in rec_dates if 2016 <= d.year <= 2019]
recorded_vol = []
recorded_height = []
recorded_areas = []
for key in sorted(mask_wkt_json.keys()):
    date = datetime.strptime(key.split('_')[0], config.DATE_FORMAT).date()
    if date in rec_dates:
        rec_vol = df.loc[df['date'] == np.datetime64(date)]['reservoir_storage'].values[0]
        rec_height = df.loc[df['date'] == np.datetime64(date)]['water_level'].values[0]
        rec_area = df.loc[df['date'] == np.datetime64(date)]['surface_area'].values[0]
        if not np.isnan(rec_vol) and not np.isnan(rec_area):
            estimates_for_vol.append(mask_wkt_json[key])
            rec_vol = rec_vol * 1233    # convert acre-feet to m^3
            recorded_vol.append(rec_vol)
            recorded_areas.append(rec_area * 4047)
        if not np.isnan(rec_height):
            estimates_for_height.append(mask_wkt_json[key])
            rec_height = rec_height / 3.281 # convert acres to m^2
            recorded_height.append(rec_height)

# extract relevant recorded areas for verification
plot_x_y_rs_experiment(recorded_vol, estimates_for_vol, 'Actual volume (m^3)', 'Estimated surface area (m^2)', 'Relationship between area and volume for Lake Texana')
plot_x_y_rs_texana(recorded_vol, estimates_for_vol, recorded_vol, recorded_areas, 'Actual volume (m^3)', 'Estimated surface area (m^2)', 'Relationship between area and volume for Lake Texana')

logger.info("Completed")
if platform.system() == "Windows":
    import winsound
    duration = 1000  # milliseconds
    freq = 1000  # Hz
    winsound.Beep(freq, duration)
    winsound.Beep(freq, duration)
