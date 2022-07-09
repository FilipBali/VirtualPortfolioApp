from datetime import timedelta, datetime

import numpy as np
import pandas as pd
import pmdarima as pm
from django.contrib import messages
from pmdarima.model_selection import train_test_split
from sklearn.linear_model import LinearRegression


# radic
def get_prediction(request, data, type, predict_time=7, custom_lenght=0):

    if type == 'linear_regression':
        data = linear_regression(request, data, predict_time=predict_time, custom_lenght=custom_lenght)
        return data
    elif type == 'moving_averages':
        ...
    elif type == 'auto_arima':
        data = arima_manager(request, data, predict_time=predict_time, custom_lenght=custom_lenght)
        return data


def arima_manager(request, data, predict_time, custom_lenght):
    arima_forecast = arima_predict(request, data, predict_time=predict_time, custom_lenght=custom_lenght)
    list_arima_forecast = list(arima_forecast)

    last_day = datetime.strptime((data['stock_id'][-1]), '%Y-%m-%d')
    prediction_days = []
    prediction_prices = []
    for day in range(0, predict_time):
        last_day = last_day + timedelta(days=1)
        prediction_days.append(str(last_day)[:10])

    prediction_days.insert(0, data['stock_id'][-1])
    list_arima_forecast.insert(0, data['stock_closed'][-1])
    data['prediction_days'] = prediction_days
    data['prediction_prices'] = list_arima_forecast
    return data


def arima_predict(request, data, predict_time, custom_lenght):
    AxisX = data['stock_id']
    AxisY = data['stock_closed']

    y = pd.DataFrame(AxisY)
    train, test = train_test_split(y, train_size=len(y)-1)

    model = pm.auto_arima(train)

    forecasts = model.predict(7)  # predict N steps into the future

    return forecasts


def moving_averages(request, data, predict_time, custom_lenght):
    AxisX = data['stock_id']
    AxisY = data['stock_closed']

    mylist = AxisY
    N = 3
    cumsum, moving_aves = [0], []

    for i, x in enumerate(mylist, 1):
        cumsum.append(cumsum[i - 1] + x)
        if i >= N:
            moving_ave = (cumsum[i] - cumsum[i - N]) / N
            # can do stuff with moving_ave here
            moving_aves.append(moving_ave)

    # return data


def linear_regression(request, data, predict_time, custom_lenght):

    AxisX = data['stock_id']
    AxisY = data['stock_closed']

    temp_x = pd.Series(([AxisY.index(i)] for i in AxisY))
    x = np.array(temp_x.index).reshape(-1, 1)

    y = pd.Series((i for i in AxisY))

    if custom_lenght !=0:
        if len(x) >= custom_lenght:
            x = x[(len(x)-custom_lenght):]
        else:
            messages.warning(request, 'Custom lenght is out of graph Axis X interval. Default(lenght of whole axis x) is set instead.')

    if custom_lenght != 0:
        if len(y) >= custom_lenght:
            y = y.iloc[(len(y)-custom_lenght):]
        else:
            ...

    linreg = LinearRegression().fit(x, y)
    # linreg.score(x, y)
    predictions = linreg.predict(x)

    sum = 0.0
    if len(predictions) != 1:
        for index, value in enumerate(predictions, start=1):
            sum += ((predictions[index]-predictions[index-1])/predictions[index-1])
            if index+1 == len(predictions):
                break

    average = 0.0
    if len(predictions) != 1:
        average = sum/((len(predictions))-1)

    last_day = datetime.strptime((data['stock_id'][-1]), '%Y-%m-%d')
    prediction_days = []
    predict_value = data['stock_closed'][-1]
    prediction_prices = []
    for day in range(0, predict_time):
        predict_value = predict_value * (1.00+average)
        prediction_prices.append(predict_value)
        last_day = last_day + timedelta(days=1)
        prediction_days.append(str(last_day)[:10])

    prediction_days.insert(0, data['stock_id'][-1])
    prediction_prices.insert(0, data['stock_closed'][-1])

    data['prediction_days'] = prediction_days
    data['prediction_prices'] = prediction_prices

    return data
