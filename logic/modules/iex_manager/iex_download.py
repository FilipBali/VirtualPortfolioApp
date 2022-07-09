import os
from datetime import datetime, timedelta

from iexfinance.refdata import get_symbols
from iexfinance.stocks import get_historical_data

from authenticationApp.models import Profile
from portfolioApp.models import News


# from backend.modules.lib.prediction.predict_engines import try_statsmodels



def check_authentication(request):
    data = get_iex_api_details(request)
    if data['iex_api_version'] is None or data['iex_token'] == None:
        return False
    else:
        return True


# Get IEX Finance authentization parameters
# Params: request
#
# Return user's iex_api_version and iex_token from database (dictionary)
def get_iex_api_details(request):
    return {'iex_api_version': Profile.objects.get(user=request.user).iex_api_version,
                  'iex_token': Profile.objects.get(user=request.user).iex_token}


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
def get_iex_ohlc(request, instr, start_date, end_date, volume=False):

    iex_api_details = get_iex_api_details(request)
    os.environ['IEX_API_VERSION'] = iex_api_details['iex_api_version']
    os.environ['IEX_TOKEN'] = iex_api_details['iex_token']

    try:
        raw_historical_data = get_historical_data(instr, start_date, end_date)
    except:
        if volume:
            base = datetime.today()
            date_list = [base - timedelta(days=x) for x in range(4)]
            return [str(base)[:10]], [[0000000000000, 0.0, 0.0, 0.0, 0.0, 0]]
        else:
            base = datetime.today()
            date_list = [base - timedelta(days=x) for x in range(4)]
            return [str(base)[:10]], [[0000000000000, 0.0, 0.0, 0.0, 0.0]]

    if not 'raw_historical_data' in locals():
        base = datetime.today()
        date_list = [base - timedelta(days=x) for x in range(4)]
        return [str(base)[:10]], [[0000000000000,0.0, 0.0, 0.0, 0.0]]

    price_data = []
    time_data = []
    changed = []
    if raw_historical_data.size == 0:
        base = datetime.today()
        date_list = [base - timedelta(days=x) for x in range(4)]
        return [str(base)[:10]], [[0000000000000,0.0, 0.0, 0.0, 0.0]]

    else:
        if volume:
            for raw_object in raw_historical_data.iterrows():
                # utc_time = datetime.strptime(raw_object + 'T00:00:00',
                #                              "%Y-%m-%dT%H:%M:%S")
                milliseconds = ((datetime.strptime(str(raw_object[0]),
                                                   "%Y-%m-%d %H:%M:%S")) - datetime(1970, 1, 1)) // timedelta(
                    milliseconds=1)
                # tmp = list(raw_historical_data[raw_object].values())
                tmp = [milliseconds, raw_object[1].open, raw_object[1].high, raw_object[1].low, raw_object[1].close,
                       raw_object[1].volume]

                # tmp.insert(0, milliseconds)
                price_data.append(tmp)

                time_data.append(str(raw_object[0])[:10])
        else:
            for raw_object in raw_historical_data.iterrows():

                # utc_time = datetime.strptime(raw_object + 'T00:00:00',
                #                              "%Y-%m-%dT%H:%M:%S")
                milliseconds = ((datetime.strptime(str(raw_object[0]),
                                             "%Y-%m-%d %H:%M:%S")) - datetime(1970, 1, 1)) // timedelta(milliseconds=1)


                # tmp = list(raw_historical_data[raw_object].values())
                tmp = [milliseconds, raw_object[1].open, raw_object[1].high, raw_object[1].low, raw_object[1].close]


                tdate = str(datetime.strptime(str(raw_object[0]), "%Y-%m-%d %H:%M:%S"))[:10]
                changed.append([tdate, raw_object[1].close])

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
def get_iex_only_close(request, instr, start_date, end_date):
    iex_api_details = get_iex_api_details(request)
    os.environ['IEX_API_VERSION'] = iex_api_details['iex_api_version']
    os.environ['IEX_TOKEN'] = iex_api_details['iex_token']
    try:
        raw_historical_data = get_historical_data(instr, start_date, end_date)
    except:
        ...

    if 'raw_historical_data' in locals():
        if raw_historical_data.size == 0:
            ret_data = [0.0, 0.0, 0.0, 0.0]
            return ret_data

        else:
            ret_data = raw_historical_data['close']
            return ret_data
    else:
        ret_data = [0.0, 0.0, 0.0, 0.0]
        return ret_data

def get_news(instrument):
    return News.objects.all().filter(company__symbol=instrument).order_by('-datetime')

# Get instrument data for graph visualization
# Params: data (dict) - where to store data
#         instrument (string)
#         startdate (string) yyyy-mm-dd
#         enddate (string) yyyy-mm-dd
#         update (boolean) - news are not updating on ajax request
#
# Return: date(dict)
# Added to the dictionary:
#   stock_id = list of dates
#   stock_closed = list of closed prices
#                                        |          DAY1          | |           DAY2        | | DAYn |
#   stock_candle = list of OHLC prices.. [[open, high, low, close], [open, high, low, close], .......]
#
def iex_graph_data(request, data, instrument, company, startdate, enddate, update=False):
    iex_api_details = get_iex_api_details(request)
    os.environ['IEX_API_VERSION'] = iex_api_details['iex_api_version']
    os.environ['IEX_TOKEN'] = iex_api_details['iex_token']

    time_data, price_data = get_iex_ohlc(request,
                                         instrument,
                                         datetime.strptime(startdate, '%Y-%m-%d'),
                                         datetime.strptime(enddate, '%Y-%m-%d'), volume=True)

    data['stock_id'] = time_data
    data['stock_closed'] = [val[-2] for val in price_data]
    data['stock_candle'] = price_data

    if not update:
        data['news'] = get_news(instrument)

    return data


def iex_instrument_details(data, company):
    data['symbol'] = company.get_company().index[0]

    symbols = get_symbols()
    region, currency, exchange = '', '', ''

    for index, row in symbols.iterrows():
        if row['symbol'] == data['symbol']:
            data['region'] = row['region']
            data['currency'] = row['currency']
            data['exchange'] = row['exchange']
            break

    data['company_name'] = company.get_company_name()
    data['company_volume'] = company.get_volume()
    data['company_primary_exchange'] = company.get_primary_exchange()
    return data


def iex_news_data(data, company):
    news = {}
    try:
        news_tdate = company.get_news()
    except:
        return data

    id = 0
    for new_article in news_tdate.iterrows():
        if new_article[1]['lang'] == 'en':
            save_article = {}

            save_article['id'] = id
            save_article['article_headline'] = new_article[1]['headline']
            save_article['article_text'] = new_article[1]['summary']
            save_article['source'] = new_article[1]['source']
            save_article['url'] = new_article[1]['url']

            news[id] = save_article
            id += 1
            # article = News()
            # article.article_headline = news[1]['headline']
            # article.article_text = news[1]['summary']
            # article.source = news[1]['source']
            #
            # article_time = datetime.fromtimestamp(news[0] / 1000.0)
            #
            # article.url = news[1]['url']
            # article.datetime = article_time
            # article.company_id = Company.objects.get(symbol=company.get_company().index[0]).id
            # article.save()

    data['news'] = {'instrument_source': '1', 'data': news}
    return data
