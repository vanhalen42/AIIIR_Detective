from operator import mod
import sklearn
import sklearn.linear_model as linear
from sklearn.model_selection import train_test_split
import pandas as pd
import os
import numpy as np
import datetime
from matplotlib import pyplot as plt
from thingspeak import remove_nans
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LinearRegression
degree=5


directory = './ground_truth'

co2_file = 'aeroqual_co2.csv'
pm_file = 'aeroqual_PM.csv'

co2_gt = pd.read_csv(os.path.join(directory,co2_file), sep=',', header=None).to_numpy(dtype=object)
pm_gt = pd.read_csv(os.path.join(directory,pm_file), sep=',', header=None).to_numpy(dtype=object)
header = co2_gt[0,:]
print(header)
co2_gt = np.delete(co2_gt,0,axis=0)
pm_gt = np.delete(pm_gt,0,axis=0)
timestamp = co2_gt[:,0]
for _iter,time in enumerate(timestamp):
    datetime_obj1 = datetime.datetime.strptime(time,'%d %b %Y %H:%M')
    timestamp[_iter] = datetime_obj1
co2_gt = np.stack([timestamp,co2_gt[:,-1].astype(np.float32)],axis=1)
co2_fetched = np.load('./cache/CO2_PPM_lin.npy',allow_pickle=True)
co2_fetched = remove_nans(co2_fetched)

timestamp = co2_fetched[:,0]
for _iter,time in enumerate(timestamp):
    datetime_obj1 = datetime.datetime.strptime(time,'%Y-%m-%dT%H:%M:%SZ')
    timestamp[_iter] = datetime_obj1
X = []
Y = []
for data in co2_gt:
    for fetched in co2_fetched:
        if data[0].date() == fetched[0].date() and data[0].hour == fetched[0].hour and data[0].minute == fetched[0].minute:
            if data[1] > 1000 or fetched[1] > 1000:
                continue
            if fetched[0].date() > datetime.datetime(2022,9,9).date():
                continue
            if data[1] in Y:
                continue
            # if data[1] in Y:
            #     index = Y.index(data[1])
            #     Y.append(data[1])
            #     X.append((fetched[1] + Y[index])/2)
            # else:
            Y.append(data[1])
            X.append(fetched[1])

# print(co2_fetched)
# print(co2_gt)
# print(correspondence)
# plt.plot(correspondence)
print(X)
print(Y)
plt.scatter(X,Y)
# plt.show()
# print(pm_gt)
# model=make_pipeline(PolynomialFeatures(degree),LinearRegression())
model = LinearRegression()
X = np.array(X).reshape(-1, 1)
y = np.array(Y).reshape(-1, 1)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.25)
model.fit(X_train, y_train)
print(model.score(X_test, y_test))
y_pred = model.predict(X_test)
print(f'line predicted: {y_pred}')
plt.scatter(X_test, y_test, color ='b')
plt.plot(X_test, y_pred, color ='k')
  
# plt.show()
plt.savefig('co2.png')
