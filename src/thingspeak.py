import requests
import numpy as np
import math
import json
import time
import os
from matplotlib import pyplot as plt
import random
import datetime
import pandas as pd
from adtk.data import validate_series
from adtk.visualization import plot
from adtk.detector import QuantileAD, OutlierDetector, SeasonalAD,InterQuartileRangeAD,LevelShiftAD,PersistAD
from sklearn.neighbors import LocalOutlierFactor
import matplotlib as mpl
from forecast import forecast
from notification import send_email
from notification import notify as telegram_notify
from dotenv import load_dotenv
load_dotenv()

READ_API_KEY=os.getenv('READ_API_KEY')
CHANNEL_ID=os.getenv('CHANNEL_ID')

data_fields = {
    'field1': 'Temperature',
    'field2': 'Relative Humidity',
    # 'field3': 'VOC Index',
    'field3': 'CO2 PPM',
    'field4': 'PM2.5',
    'field5': 'PM10'
}

def parse_data_instance(instance):
    nan_num = 0
    time_stamp = instance['created_at']
    for _iter,key in enumerate(data_fields.keys()):
        value = instance[key]
        if value == None:
            nan_num += 1
        # print(value)
    # exit()
    return np.asarray_chkfinite(list(instance.values()),dtype=object),np.array([time_stamp,nan_num],dtype=object)
parse_data_instance_v = np.vectorize(parse_data_instance)
def remove_nans(field,show_nans=False,remove_zeros=False):
    field = field.transpose()
    if show_nans:
        mask = field[1] != field[1]
    else:     
        mask = field[1] == field[1]
    if remove_zeros:
        mask2 = field[1] != 0.0
        mask = mask & mask2
    field = field[...,mask]
    return field.T

def parse_response(text):
    response_json = json.loads(text)
    # print(response_json)
    # exit()
    headers = np.array(response_json['channel'])
    data = np.array(response_json['feeds'])
    data,nan_num = parse_data_instance_v(data)
    nan_num = np.stack(nan_num)
    data = np.stack(data,axis=0)
    # print(nan_num)
    time_stamps = data[:,0]
    fields = {}
    for _iter,key in enumerate(data_fields.keys()):
        fields[key] = np.stack([time_stamps,data[:,_iter+2].astype(np.float32)],axis=1)
    data = np.delete(data,0,axis=1).astype(np.float32)
    return headers,time_stamps,data,fields,nan_num


def cache_data(fields,nan_num):
    directory = './cache'
    os.makedirs(directory,exist_ok=True)
    for _iter,key in enumerate(data_fields.keys()):
        filename = data_fields[key].replace(' ','_') + '.npy'
        file_path = os.path.join(directory,filename)
        np.save(file_path,fields[key])
        # print(fields[key])
    
    # save nan_num
    filename = 'nan_num.npy'
    file_path = os.path.join(directory,filename)
    np.save(file_path,nan_num)

def load_data():
    directory = './cache'
    fields = {}
    for _iter,key in enumerate(data_fields.keys()):
        filename = data_fields[key].replace(' ','_') + '.npy'
        file_path = os.path.join(directory,filename)
        fields[key] = np.load(file_path,allow_pickle=True)
    # load nan_num
    filename = 'nan_num.npy'
    file_path = os.path.join(directory,filename)
    nan_num = np.load(file_path,allow_pickle=True)
    return fields,nan_num

def nan_analysis(nan_num):
    os.makedirs('./plots/nan_analysis',exist_ok=True)
    X = nan_num[:,0].astype(np.datetime64)
    plt.plot(X,nan_num[:,1])
    plt.xlabel('Time')
    # plt.show()
    plt.savefig('./plots/nan_analysis/nan_num.png')
    plt.clf()

def freq_analysis(field,key,plot=True):
    os.makedirs('./plots/freq_analysis',exist_ok=True)
    sensor_interval_list=[]
    time = []
    outlier_thresh = 900
    max_gap=0
    if len(field)>1: # if just one datapoint, why do freq analysis at all
        # print(len(field)-1)
        for i in range(0,len(field)-1):
            timestamp1 = field[i,0]
            timestamp2 = field[i+1,0]
            
            # find the 'gap lengths' between two consecutive datapoints
            datetime_obj1 = datetime.datetime.strptime(
                timestamp1, '%Y-%m-%dT%H:%M:%SZ')
            datetime_obj2 = datetime.datetime.strptime(
                timestamp2, '%Y-%m-%dT%H:%M:%SZ')
            diff = datetime.timedelta.total_seconds(datetime_obj2-datetime_obj1)
            if diff > outlier_thresh:
                continue
            sensor_interval_list.append(diff)
            time.append(datetime_obj1)
            max_gap = max(max_gap, diff)
        # print(sensor_interval_list)
        # X = field[:,0].astype(np.datetime64)
        # plt.plot(X[:-1],sensor_interval_list)
        if plot:
            plt.plot(time,sensor_interval_list)
            plt.xlabel('Time')
            # plt.show()
            plt.savefig('./plots/freq_analysis/'+key+'.png')
            plt.clf()
    
    return max_gap, sensor_interval_list

def outlier_detection(field,key):
    os.makedirs('./plots/outlier_detection',exist_ok=True)
    os.makedirs('./cache/outlier_detection',exist_ok=True)
    sensor_data = []
    num_anomalies = 0
    if len(field)>1: # if just one datapoint, why do freq analysis at all
        # print(len(field)-1)
        for i in range(0,len(field)-1):
            date_string = field[i,0]
            datetime_obj = datetime.datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ')
            cin = []
            cin.append(datetime_obj)
            cin.append(field[i,1])
            sensor_data.append(cin)
        s_train = pd.DataFrame(sensor_data, index=None)
        s_train = s_train.set_index(0)
        s_train = s_train.fillna(0)
        s_train = validate_series(s_train)
        nneigh = min(len(field)-1,1000)
        # outlier_detector = OutlierDetector(LocalOutlierFactor(contamination=0.05, n_neighbors=nneigh))
        outlier_detector = QuantileAD(low=0.01,high=0.99)
        # outlier_detector = InterQuartileRangeAD(c=1.5)
        # outlier_detector = PersistAD()
        anomalies = outlier_detector.fit_detect(s_train)
        anomalies_np = anomalies.to_numpy()
        num_anomalies = anomalies_np.sum()
        plot(s_train, anomaly=anomalies, ts_linewidth=1, ts_markersize=3, anomaly_color='red',
            anomaly_alpha=0.3, curve_group='all')
        # plt.show()
        plt.savefig('./plots/outlier_detection/'+key+'.png')
        plt.clf()
        # save anomalies
        filename = key + '.npy'
        file_path = os.path.join('./cache/outlier_detection',filename)
        np.save(file_path,anomalies)
    
    return num_anomalies

def thingspeak_read_actual(datapoints = 5000):
    num_results = datapoints
    url = f'''https://thingspeak.com/channels/{CHANNEL_ID}/feed.json?results={num_results}?api_key={READ_API_KEY}''' 
    response = requests.get(url=url)
    print('Data Fetched')
    headers,time_stamps,data,fields,nan_num = parse_response(response.text)
    cache_data(fields,nan_num)
    print('Data Cached')

def notify(field):

    markdown_text = "*Daily Update*\n"
    email_text ="Summary of data posted in the past 24 hours\n\n"

    non_nans = {}
    for key in data_fields.keys():
        non_nans[key] = None
    
    # nan summary 
    min_nan = np.inf
    max_nan = 0
    min_nan_key = ''
    max_nan_key = ''
    for key in field.keys():
        remove_zeros = False
        if key == 'field3' or key == 'field6':
            remove_zeros = True
        nans = remove_nans(field[key],show_nans=True,remove_zeros=remove_zeros)
        non_nan = remove_nans(field[key],remove_zeros=remove_zeros)
        non_nans[key] = non_nan
        if nans.shape[0] < min_nan:
            min_nan = nans.shape[0]
            min_nan_key = data_fields[key]
        if nans.shape[0] > max_nan:
            max_nan = nans.shape[0]
            max_nan_key = data_fields[key]
    if max_nan == 0:
        markdown_text += f'''*No nan values in any field*\n'''
        email_text += f'''No nan values in any field\n'''
    else:
        markdown_text += f'''*Maximum number of nan values: {max_nan} in {max_nan_key}*\n'''
        markdown_text += f'''*Minimum number of nan values: {min_nan} in {min_nan_key}*\n\n'''
        email_text += f'''Maximum number of nan values: {max_nan} in {max_nan_key}\n'''
        email_text += f'''Minimum number of nan values: {min_nan} in {min_nan_key}\n\n'''

    # freq analysis
    max_gap = 0
    max_gap_key = ''
    for key in non_nans.keys():
        gap, sensor_interval_list = freq_analysis(non_nans[key],key=data_fields[key].replace(' ','_'),plot=True)
        if gap > max_gap:
            max_gap = gap
            max_gap_key = data_fields[key]
    markdown_text += f'''*Maximum gap between two consecutive datapoints: {max_gap}s in {max_gap_key}*\n\n'''
    email_text += f'''Maximum gap between two consecutive datapoints: {max_gap}s in {max_gap_key}\n\n'''

    # outlier detection
    max_outliers = 0
    max_outliers_key = ''
    for key in non_nans.keys():
        num_anomalies = outlier_detection(non_nans[key],key=data_fields[key].replace(' ','_'))
        if num_anomalies > max_outliers:
            max_outliers = num_anomalies
            max_outliers_key = data_fields[key]
    markdown_text += f'''*Maximum number of anomalies: {max_outliers} in {max_outliers_key}*\n\n'''
    email_text += f'''Maximum number of anomalies: {max_outliers} in {max_outliers_key}\n\n'''
    forecast(field)
    send_email(email_text)
    # send_plot()
def sentry():
    while True:
        # thingspeak_read_actual()
        fields,_ = load_data()
        telegram_alert(fields)
        time.sleep(300)


def telegram_alert(fields):
    # read alert_config.json
    with open('./alert_config.json','r') as f:
        config = json.load(f)

    for key in fields.keys():
        non_nan = remove_nans(fields[key])
        upper_bound = float(config[data_fields[key]])
        mask = non_nan[:,-1] > upper_bound
        if np.any(mask):
            print('Alert')
            print(data_fields[key])
            alert_text = data_fields[key] + f'\n Alert!\n\n Sensor has exceeded the threshold {upper_bound}\n Values returned:\n\n'
            val = non_nan[mask][-1]
            alert_text += 'Latest value:\n'
            alert_text += f'''Time: {datetime.datetime.strptime(val[0], '%Y-%m-%dT%H:%M:%SZ')}\nValue: {val[1]}\n\n'''
            telegram_notify('registered_users.json',alert_text)
        

def master():
    print("AIIIR")
    # make menu
    option1 = input('1. Daily Summary + Analysis\n2. Sentry Mode\n')

    if option1 == '2':
        sentry()

    # thingspeak_read_actual()
    fields,nan_num = load_data()
    notify(fields)


if __name__ == '__main__':
    master()
