from json import load
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import datetime
import os 

from lightgbm import LGBMRegressor
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.graphics.tsaplots import plot_acf
from scipy.stats import t
from sklearn.model_selection import TimeSeriesSplit, train_test_split
from sklearn.metrics import mean_absolute_error
data_fields = {
    'field1': 'Temperature',
    'field2': 'Relative Humidity',
    # 'field3': 'VOC Index',
    'field3': 'CO2 PPM',
    'field4': 'PM2.5',
    'field5': 'PM10'
}

def train_time_series_with_folds(df, horizon=4200,index=1):
    os.makedirs('plots/forecast', exist_ok=True)
    X = df.drop(index, axis=1)
    y = df[index]

    #take last week of the dataset for validation
    X_train, X_test = X.iloc[:-horizon,:], X.iloc[-horizon:,:]
    y_train, y_test = y.iloc[:-horizon], y.iloc[-horizon:]
    
    #create, train and do inference of the model
    model = LGBMRegressor(random_state=42)
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    
    #calculate MAE
    mae = np.round(mean_absolute_error(y_test, predictions), 3)    
    
    #plot reality vs prediction for the last week of the dataset
    plt.clf()
    fig = plt.figure(figsize=(16,6))
    plt.title(f'Real vs Prediction - MAE {mae}', fontsize=20)
    plt.plot(y_test, color='red')
    plt.plot(pd.Series(predictions, index=y_test.index), color='green')
    plt.xlabel('Time', fontsize=16)
    plt.ylabel(data_fields[f'field{index}'], fontsize=16)
    plt.legend(labels=['Real', 'Prediction'], fontsize=16)
    plt.grid()
    plt.savefig(f'''plots/forecast/forecast_{data_fields[f'field{index}']}.png'''.replace(' ','_'))
    # plt.show()
    
    #create a dataframe with the variable importances of the model
    df_importances = pd.DataFrame({
        'feature': model.feature_name_,
        'importance': model.feature_importances_
    }).sort_values(by='importance', ascending=False)
    
    #plot variable importances of the model
    plt.title('Variable Importances', fontsize=16)
    sns.barplot(x=df_importances.importance, y=df_importances.feature, orient='h')
    # plt.show()


def forecast(fields):
    n = len(fields['field1'])
    sensor_data = []
    for i in range(0,n):
        date_string = fields['field1'][i,0]
        datetime_obj = datetime.datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ')
        cin = []
        cin.append(datetime_obj)
        cin.append(fields['field1'][i,1])
        cin.append(fields['field2'][i,1])
        cin.append(fields['field3'][i,1])
        cin.append(fields['field4'][i,1])
        cin.append(fields['field5'][i,1])
        sensor_data.append(cin)
    s_train = pd.DataFrame(sensor_data, index=None)
    # print(s_train)
    # exit()
    s_train[0] = pd.to_datetime(s_train[0])
    s_train = s_train.set_index(0)

    print(s_train.info())
    for i in range(1,6):
        train_time_series_with_folds(s_train,index=i)
