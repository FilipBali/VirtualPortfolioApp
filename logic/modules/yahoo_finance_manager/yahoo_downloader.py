from datetime import datetime, timedelta

import requests
import xmltodict
import yfinance as yf
from stocknews import StockNews


# Download instrument data (Open, High, Low, Close, (Optional: Volume))
# Params: instrument(string)
#         start_date(datetime)
#         end_date(datetime)
#         volume(boolean)
#
# Return:
#  time_data = list of dates [date,date,date,date,...]
#
#                                        |          DAY1                    | |           DAY2                | | DAYn |
#   price_data = list of OHLC + volume.. [[open, high, low, close, (volume)], [open, high, low, close] (volume), .....]
#
# If source is NOT available then return array of zeros
#
def get_yahoo_ohlc(instrument, start_date, end_date, volume=False):
    price_data = []
    time_data = []

    if end_date == '':
        raw_historical_data = yf.download(  # or pdr.get_data_yahoo(...
            tickers=instrument,
            # period='1d',
            start=str(start_date)[:10],
            threads=True,
        )
    else:
        raw_historical_data = yf.download(  # or pdr.get_data_yahoo(...
            tickers=instrument,
            # period='1d',
            start=str(start_date)[:10],
            end=str(end_date)[:10],
            threads=True,
        )

    if raw_historical_data.size == 0:
        return [0.0, 0.0, 0.0, 0.0]

    else:
        if volume:
            for raw_object in raw_historical_data.iterrows():
                # utc_time = datetime.strptime(raw_object + 'T00:00:00',
                #                              "%Y-%m-%dT%H:%M:%S")
                milliseconds = ((datetime.strptime(str(raw_object[0]),
                                                   "%Y-%m-%d %H:%M:%S")) - datetime(1970, 1, 1)) // timedelta(
                    milliseconds=1)
                # tmp = list(raw_historical_data[raw_object].values())
                tmp = [milliseconds, raw_object[1].Open, raw_object[1].High, raw_object[1].Low, raw_object[1].Close,
                       raw_object[1].Volume]

                # tmp.insert(0, milliseconds)
                price_data.append(tmp)

                time_data.append(str(raw_object[0])[:10])

        else:
            for raw_object in raw_historical_data.iterrows():
                # utc_time = datetime.strptime(raw_object + 'T00:00:00',
                #                              "%Y-%m-%dT%H:%M:%S")
                milliseconds = ((datetime.strptime(str(raw_object[0]),
                                                   "%Y-%m-%d %H:%M:%S")) - datetime(1970, 1, 1)) // timedelta(
                    milliseconds=1)
                # tmp = list(raw_historical_data[raw_object].values())
                tmp = [milliseconds, raw_object[1].Open, raw_object[1].High, raw_object[1].Low, raw_object[1].Close]

                # tmp.insert(0, milliseconds)
                price_data.append(tmp)

                time_data.append(str(raw_object[0])[:10])

    return time_data, price_data


# Download instrument data (Close)
# Params: instrument (string)
#         start_date (string) yyyy-mm-dd
#         end_date (string) yyyy-mm-dd
#
# Return instrument close data for a given interval (DataFrame: AxisX=0(Index), AxisY=Timestamps)
# If source is NOT available then return array of zeros
#
def get_yahoo_only_close(instrument, start_date, end_date, notification=False):
    # try:
    #     raw_historical_data = web.DataReader(instrument, 'yahoo', start_date, end_date)
    # except:
    #     ...

    if end_date == '':
        raw_historical_data = yf.download(  # or pdr.get_data_yahoo(...
            tickers=instrument,
            # period='1d',
            start=str(start_date)[:10],
            threads=True,
        )
    else:
        if notification == True:

            start_date_datetime = datetime.strptime(start_date,"%Y-%m-%d")
            start_date_datetime = start_date_datetime - timedelta(days=7)
            raw_historical_data = yf.download(
                tickers=instrument,
                # period='1d',
                start=str(start_date_datetime)[:10],
                end=str(end_date)[:10],
                threads=True,
            )
        else:
            raw_historical_data = yf.download(
                tickers=instrument,
                # period='1d',
                start=str(start_date)[:10],
                end=str(end_date)[:10],
                threads=True,
            )


    if 'raw_historical_data' in locals():
        if raw_historical_data.size == 0:
            return [0.0, 0.0, 0.0, 0.0]

        else:
            ret_data = raw_historical_data['Close']
            return ret_data
    else:
        return [0.0, 0.0, 0.0, 0.0]

# Get instrument data for graph visualization
# Params: data (dict) - where to store data
#         instrument (string)
#         startdate (string) yyyy-mm-dd
#         enddate (string) yyyy-mm-dd
#
# Return: date(dict)
# Added to the dictionary:
#   stock_id = list of dates
#   stock_closed = list of closed prices
#                                        |          DAY1          | |           DAY2        | | DAYn |
#   stock_candle = list of OHLC prices.. [[open, high, low, close], [open, high, low, close], .......]
#
def yahoo_graph_data(data, instrument, startdate, enddate):
    temp_startdate = ''
    temp_enddate = ''

    if startdate != '':
        temp_startdate = datetime.strptime(startdate, '%Y-%m-%d')
    if enddate != '':
        temp_enddate = datetime.strptime(enddate, '%Y-%m-%d')

    time_data, price_data = get_yahoo_ohlc(instrument,
                                           temp_startdate,
                                           temp_enddate)

    data['stock_id'] = time_data
    data['stock_closed'] = [val[-2] for val in price_data]
    data['stock_candle'] = price_data

    return data

def yahoo_instrument_details(data, instrument):
    company = yf.Ticker(instrument)
    data['symbol'] = company.info['symbol']
    data['currency'] = company.info['currency']
    data['company_name'] = company.info['shortName']
    data['company_volume'] = company.info['volume']
    data['company_primary_exchange'] = company.info['exchange']
    return data



def get_yahoo_intraday(instrument, startdate, enddate, notification=False):
    if notification == True:

        actual_time = datetime.now() - timedelta(days=4)
        actual_time = str(actual_time)[:10]

        # start_date_datetime = datetime.strptime(startdate, "%Y-%m-%d")
        # start_date_datetime = start_date_datetime - timedelta(days=7)
        raw_data = yf.download(  # or pdr.get_data_yahoo(...
            # tickers list or string as well
            tickers=instrument,

            # use "period" instead of start/end
            # valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
            # (optional, default is '1mo')
            # period="1d",

            start=actual_time,
            end=enddate,

            # fetch data by interval (including intraday if period < 60 days)
            # valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
            # (optional, default is '1d')
            interval="1m",

            # group by ticker (to access via data['SPY'])
            # (optional, default is 'column')
            group_by='ticker',

            # adjust all OHLC automatically
            # (optional, default is False)
            auto_adjust=True,

            # download pre/post regular market hours data
            # (optional, default is False)
            prepost=False,

            # use threads for mass downloading? (True/False/Integer)
            # (optional, default is True)
            threads=True,

            # proxy URL scheme use use when downloading?
            # (optional, default is None)
            proxy=None
        )

        return raw_data
    else:
       raw_data = yf.download(  # or pdr.get_data_yahoo(...
            # tickers list or string as well
            tickers=instrument,

            # use "period" instead of start/end
            # valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
            # (optional, default is '1mo')
            # period="1d",

           start=startdate,
           end=enddate,

            # fetch data by interval (including intraday if period < 60 days)
            # valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
            # (optional, default is '1d')
            interval="1m",

            # group by ticker (to access via data['SPY'])
            # (optional, default is 'column')
            group_by='ticker',

            # adjust all OHLC automatically
            # (optional, default is False)
            auto_adjust=True,

            # download pre/post regular market hours data
            # (optional, default is False)
            prepost=False,

            # use threads for mass downloading? (True/False/Integer)
            # (optional, default is True)
            threads=True,

            # proxy URL scheme use use when downloading?
            # (optional, default is None)
            proxy=None
       )

       return raw_data



def get_yahoo_intraday_data(instrument, day, volume=False, notification=False):

    ret_data = {}
    price_data = []
    time_data = []
    closed_data = []

    start_date = datetime.strptime(day, '%Y-%m-%d')
    end_date = start_date + timedelta(days=1)

    # Perform string cut
    startdate = str(start_date)[:10]
    enddate = str(end_date)[:10]

    raw_data = get_yahoo_intraday(instrument, startdate, enddate, notification=notification)

    if notification:
        return raw_data

    if raw_data.size == 0:
        ret_data['time_data'] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        ret_data['stock_candle'] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        ret_data['line_chart_data'] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        return ret_data

    else:
        if volume:
            for raw_object in raw_data.iterrows():
                # utc_time = datetime.strptime(raw_object + 'T00:00:00',
                #                              "%Y-%m-%dT%H:%M:%S")
                milliseconds = ((datetime.strptime(str(raw_object[0]),
                                                   "%Y-%m-%dT%H:%M:%S")) - datetime(1970, 1, 1)) // timedelta(
                    milliseconds=1)
                # tmp = list(raw_historical_data[raw_object].values())
                tmp = [milliseconds, raw_object[1].Open, raw_object[1].High, raw_object[1].Low, raw_object[1].Close,
                       raw_object[1].Volume]

                # tmp.insert(0, milliseconds)
                price_data.append(tmp)

                time_data.append(str(raw_object[0])[:10])

        else:
            for raw_object in raw_data.iterrows():
                # utc_time = datetime.strptime(raw_object + 'T00:00:00',
                #                              "%Y-%m-%dT%H:%M:%S")
                # milliseconds = ((datetime.strptime(str(raw_object[0]),
                #                                    "%Y-%m-%d %H:%M:%S")) - datetime(1970, 1, 1)) // timedelta(
                #     milliseconds=1)

                milliseconds = raw_object[0].value
                # tmp = list(raw_historical_data[raw_object].values())
                tmp = [int(milliseconds/1000000), raw_object[1].Open, raw_object[1].High, raw_object[1].Low, raw_object[1].Close]

                closed_data.append([int(milliseconds/1000000), raw_object[1].Close])

                # tmp.insert(0, milliseconds)
                price_data.append(tmp)

                time_data.append(str(raw_object[0])[:10])

    ret_data = yahoo_instrument_details(ret_data, instrument)

    ret_data['time_data'] = time_data
    ret_data['stock_candle'] = price_data
    ret_data['line_chart_data'] = closed_data

    return ret_data

def get_yahoo_news(data, instrument):

    news = {}

    sn = StockNews(instrument, wt_key='MY_WORLD_TRADING_DATA_KEY', save_news=False)
    yahoo_news_url = sn.YAHOO_URL

    yahoo_news_url = yahoo_news_url.replace("%s", instrument)

    yahoo_news_response = requests.get(yahoo_news_url)
    yahoo_news_data = xmltodict.parse(yahoo_news_response.content)
    id = 0
    if 'rss' in yahoo_news_data and\
       'channel' in yahoo_news_data['rss'] and\
       'item' in yahoo_news_data['rss']['channel']:

        for new_article in yahoo_news_data['rss']['channel']['item']:
            save_article = {}
            save_article['id'] = id
            save_article['article_headline'] = new_article['title']
            save_article['article_text'] = new_article['description']
            save_article['source'] = yahoo_news_data['rss']['channel']['title']
            save_article['url'] = new_article['link']

            news[id] = save_article
            id += 1

    data['news'] = {'instrument_source': '2', 'data': news}
    return data
