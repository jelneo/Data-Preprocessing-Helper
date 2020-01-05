import json
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pandas.plotting import register_matplotlib_converters
from datetime import datetime, timezone, date

# api_url_base = "http://www.thaiwater.net/DATA/REPORT/php/generate_rid_data.php?dam=17&n=2019&xyear=2019"
api_url_base = "http://www.thaiwater.net/DATA/REPORT/php/generate_rid_data.php?"
volume_keys = ['Upper Rule Curve', 'Lower Rule Curve', '2019']


def get_volume_data(dam_id):
    api_url = api_url_base + 'dam={}'.format(dam_id)
    response = requests.post(api_url)
    if response.status_code == 200:
        content = json.loads(response.content.decode('utf-8'))
        series = content['graphset'][0]['series']
        processed_response = {}
        for entry in series:
            if 'text' in entry and entry['text'] in volume_keys:
                vals = entry['values']
                processed_response[entry['text']] = {"time": [element[0] for element in vals],
                                                     "values": [element[1] for element in vals]}
        # note that timestamp in returned response is in unix timestamp format
        return processed_response

    else:
        return None


def convert_unix_to_datetime(time_list):
    return [datetime.utcfromtimestamp(t // 1000).replace(tzinfo=timezone.utc).astimezone(tz=None) for t in time_list]


def get_volume_for(selected_date: date, dam=17):
    vol_data = get_volume_data(dam)
    year = selected_date.year
    data_yr = vol_data[str(year)]
    time = data_yr['time']
    converted_time = convert_unix_to_datetime(time)
    vals = data_yr['values']
    for i in range(len(converted_time)):
        if converted_time[i].month == selected_date.month and converted_time[i].day == selected_date.day:
            # print(converted_time[i])
            return vals[i]


def get_change_in_water_level(before_date, after_date):
    '''
    returns the change in water volume between two dates
    :param before_date: datetime date object
    :param after_date: datetime date object
    :return: change in water volume in million cubic metres
    '''
    before = get_volume_for(before_date)
    # print(f'{before_date}: {before} million cubic metres')
    after = get_volume_for(after_date)
    # print(f'{after_date}: {after} million cubic metres')
    # print(f'Volume change: {before - after} million cubic metres')
    return after - before


def plot_volume_data(data_series, title, x_label, y_label):
    time = data_series['time']
    converted_time = convert_unix_to_datetime(time)
    vals = data_series['values']

    register_matplotlib_converters()
    fig, ax = plt.subplots(1, 1, figsize=(6, 3))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b %Y'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")
    ax.plot(converted_time, vals)
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.grid()
    plt.gcf().autofmt_xdate()
    plt.show()


if __name__ == "__main__":
    data = get_volume_data(17)
    print(data)
    # plot_volume_data(data['2019'], "Dam Volume for Lam Chae Dam", x_label="Time", y_label="Volume (million cubic metres)")
    before_date = date(2019, 1, 1)
    after_date = date(2019, 1, 7)
    before = get_volume_for(before_date)
    print(f'{before_date}: {before} million cubic metres')
    after = get_volume_for(after_date)
    print(f'{after_date}: {after} million cubic metres')
    print(f'Volume change: {before - after} million cubic metres')
