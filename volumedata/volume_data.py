import json
from datetime import datetime, timezone, date, timedelta

import matplotlib.pyplot as plt
import requests
from pandas.plotting import register_matplotlib_converters

vol_api_url_base = "http://www.thaiwater.net/DATA/REPORT/php/generate_rid_data.php?"
climate_api_url_base = "https://www.thaiwater.net/graph/generate_data.php?type=rainfall_24hr&date=07&month=03&year=2020"
volume_keys = ['2020', '2019', '2018']
LAM_CHAE_DAM_ID = 17
NAKHON_RATCHASIMA_STATION_CODE = '431201'
with open('volumedata/lam_chae_info.json') as json_file:
    older_lc_data = json.load(json_file)


def get_volume_data(dam_id, year):
    """Note: api isn't working correctly. Only fetches the latest 3 year worth of data.
    Hence 2017 is data is stored as 2-d array in basicconfig.py"""
    api_url = vol_api_url_base + 'dam={}'.format(dam_id)
    params = {'rtype': 0, 'xyear[]': year}
    response = requests.post(api_url, params=params)
    if response.status_code == 200:
        content = json.loads(response.content.decode('utf-8'))
        series = content['graphset'][0]['series']
        processed_response = {}
        for entry in series:
            if 'text' in entry and entry['text'] in volume_keys:
                vals = entry['values']
                processed_response[entry['text']] = {"time": [element[0] for element in vals],
                                                     "values": [element[1] for element in vals]}
        time_list = []
        vals_list = []
        for entry in older_lc_data["2017"]["volume"]:
            time_list.append(entry[0])
            vals_list.append(entry[1])
        processed_response['2017'] = {"time": time_list, "values": vals_list}

        time_list = []
        vals_list = []
        for entry in older_lc_data["2016"]["volume"]:
            time_list.append(entry[0])
            vals_list.append(entry[1])
        processed_response['2016'] = {"time": time_list, "values": vals_list}
        # note that timestamp in returned response is in unix timestamp format
        return processed_response

    else:
        return None


def get_inflow_data(dam_id, year):
    api_url = vol_api_url_base + 'dam={}'.format(dam_id)
    params = {'rtype': 1, 'xyear[]': year}
    response = requests.post(api_url, params=params)
    if response.status_code == 200:
        content = json.loads(response.content.decode('utf-8'))
        series = content['graphset'][0]['series']
        processed_response = {}
        for entry in series:
            if 'text' in entry and entry['text'] in volume_keys:
                vals = entry['values']
                processed_response[entry['text']] = {"time": [element[0] for element in vals],
                                                     "values": [element[1] for element in vals]}
        time_list = []
        vals_list = []
        for entry in older_lc_data["2017"]["inflow"]:
            time_list.append(entry[0])
            vals_list.append(entry[1])
        processed_response['2017'] = {"time": time_list, "values": vals_list}
        # note that timestamp in returned response is in unix timestamp format

        time_list = []
        vals_list = []
        for entry in older_lc_data["2016"]["inflow"]:
            time_list.append(entry[0])
            vals_list.append(entry[1])
        processed_response['2016'] = {"time": time_list, "values": vals_list}
        # note that timestamp in returned response is in unix timestamp format
        return processed_response

    else:
        return None


def convert_unix_to_datetime(time):
    return datetime.utcfromtimestamp(time / 1000).replace(tzinfo=timezone.utc).astimezone(tz=None)


def convert_unix_time_list_to_date(time_list):
    return [convert_unix_to_datetime(t) for t in time_list]


def create_timestamp(year: int):
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    dates = []
    while start <= end:
        dates.append(start)
        start += timedelta(days=1)
    return dates


def get_volume_for_date(selected_date: date, dam=LAM_CHAE_DAM_ID):
    year = selected_date.year
    vol_data = get_volume_data(dam, year)
    data_yr = vol_data[str(year)]
    converted_time = create_timestamp(year)
    vals = data_yr['values']
    for i in range(len(converted_time)):
        if converted_time[i].month == selected_date.month and converted_time[i].day == selected_date.day:
            return vals[i]


def get_volume_for_dates(year, date_list, dam=LAM_CHAE_DAM_ID):
    vol_data = get_volume_data(dam, year)
    data_yr = vol_data[str(year)]
    converted_dates = create_timestamp(year)
    vol_map = {converted_dates[i]: data_yr['values'][i] for i in range(len(converted_dates))}

    val_list = []
    for d in date_list:
        if d in vol_map:
            val_list.append(vol_map[d])
    return val_list


def get_inflow_for_date(selected_date: date, dam=LAM_CHAE_DAM_ID):
    year = selected_date.year
    inflow_data = get_inflow_data(dam, year)
    data_yr = inflow_data[str(year)]
    time = data_yr['time']
    converted_time = create_timestamp(year)
    vals = data_yr['values']
    for i in range(len(converted_time)):
        if converted_time[i].month == selected_date.month and converted_time[i].day == selected_date.day:
            return vals[i]


def get_inflow_for_dates(year, date_list, dam=LAM_CHAE_DAM_ID):
    inflow_data = get_inflow_data(dam, year)
    data_yr = inflow_data[str(year)]
    converted_dates = create_timestamp(year)
    inflow_map = {converted_dates[i]: data_yr['values'][i] for i in range(len(converted_dates))}

    val_list = []
    for d in date_list:
        if d in inflow_map:
            val_list.append(inflow_map[d])
    return val_list


def get_volume_for_year(year, dam=LAM_CHAE_DAM_ID):
    vol_data = get_volume_data(dam, year)
    data_yr = vol_data[str(year)]
    vals = data_yr['values']
    return vals


def get_change_in_water_level(before_date, after_date):
    '''
    returns the change in water volume between two dates
    :param before_date: datetime date object
    :param after_date: datetime date object
    :return: change in water volume in million cubic metres
    '''
    before = get_volume_for_date(before_date)
    after = get_volume_for_date(after_date)
    return after - before


def plot_volume_data(data_series, title, x_label, y_label):
    time = []
    vals = []
    for year in data_series.keys():
        converted_time = create_timestamp(int(year))
        time = time + converted_time
        vals = vals + data_series[year]['values']

    register_matplotlib_converters()
    fig, ax = plt.subplots(1, 1, figsize=(10, 4))
    ax.scatter(time, vals, marker='.')
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.grid()
    plt.show()


def get_daily_cumulative_rainfall(start_date, end_date, area=NAKHON_RATCHASIMA_STATION_CODE):
    """Units in mm"""
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    url = climate_api_url_base + f'&type=rainfall_24hr&code={area}&sdate={start_date_str}&edate={end_date_str}'
    response = requests.get(url, verify=False)
    if response.status_code == 200:
        content = json.loads(response.content.decode('utf-8'))
        if content == 0:
            return None
        series = content['graphset'][0]['series']
        values = series[0]['values']
        processed_response = {}
        for entry in values:
            processed_response[convert_unix_to_datetime(entry[0])] = entry[1]
        return processed_response
    else:
        return None


def get_daily_temperature(start_date, end_date, area=NAKHON_RATCHASIMA_STATION_CODE):
    """Units in degree celsius"""
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    url = climate_api_url_base + f'&type=t_dry&code={area}&sdate={start_date_str}&edate={end_date_str}'
    response = requests.get(url, verify=False)
    if response.status_code == 200:
        content = json.loads(response.content.decode('utf-8'))
        if content == 0:
            return None
        series = content['graphset'][0]['series']
        values = series[0]['values']
        processed_response = {}
        for entry in values:
            processed_response[convert_unix_to_datetime(entry[0]).date()] = entry[1]
        return processed_response
    else:
        return None


def get_rainfall_for_date(selected_date):
    result = get_daily_cumulative_rainfall(selected_date, selected_date + timedelta(days=1))
    if result is None:
        return None
    for key in result.keys():
        if key.year == selected_date.year and key.month == selected_date.month and key.day == selected_date.day:
            return result[key]
    return None


def get_rainfall_for_dates(date_list):
    prcp_data = get_daily_cumulative_rainfall(date_list[0], date_list[-1] + timedelta(days=1))
    if prcp_data is None:
        return None

    val_list = []
    selected_dates = set(date_list)
    for d in prcp_data.keys():
        if d.date() in selected_dates:
            val_list.append(prcp_data[d])
    return val_list


def get_temp_for_date(selected_date):
    result = get_daily_temperature(selected_date, selected_date + timedelta(days=1))
    if result is None:
        return None
    for key in result.keys():
        if key.year == selected_date.year and key.month == selected_date.month and key.day == selected_date.day:
            return result[key]
    return None


def get_temp_for_dates(date_list):
    temp_data = get_daily_temperature(date_list[0], date_list[-1] + timedelta(days=1))
    if temp_data is None:
        return None

    val_list = []
    dates = set(temp_data.keys())
    for d in date_list:
        if d in dates:
            val_list.append(temp_data[d])
        else:
            val_list.append(None)
    return val_list
