import os
from datetime import datetime

from django.contrib import messages
from iexfinance.stocks import Stock

from authenticationApp.models import Profile
from logic.modules.iex_manager.iex_download import iex_graph_data, get_iex_api_details, get_iex_only_close, \
    get_iex_ohlc, check_authentication, iex_instrument_details, iex_news_data
from logic.modules.yahoo_finance_manager.yahoo_downloader import get_yahoo_ohlc, yahoo_graph_data, \
    get_yahoo_only_close, get_yahoo_intraday_data, yahoo_instrument_details, get_yahoo_news


def get_data(request,
             instrument,
             startdate='', enddate='', day='',
             update=False, home_page=False, historical_data=False,
             only_closed=False, intraday=False, notificiation_event=False, analysis=False):

    # 1 == IEX
    # 2 == Yahoo! Finance
    if notificiation_event:
        data_source = 2
    else:
        data_source = Profile.objects.get(user=request.user).source

    if data_source == 1:

        if not check_authentication(request):
            raise Exception('No IEX API VERSION or IEX TOKEN')

        iex_api_details = get_iex_api_details(request)
        os.environ['IEX_API_VERSION'] = iex_api_details['iex_api_version']
        os.environ['IEX_TOKEN'] = iex_api_details['iex_token']

        if home_page:
            ret_data = get_iex_only_close(request, instrument, startdate, enddate)
            return ret_data

        if only_closed:
            ret_data = get_iex_only_close(request, instrument, startdate, enddate)
            return ret_data


        if historical_data:
            time_data, price_data = get_iex_ohlc(request,
                                                 request.POST['selected_stock'],
                                                 datetime.strptime(request.POST['datepicker_start'],
                                                                   '%Y-%m-%d'),
                                                 datetime.strptime(request.POST['datepicker_end'],
                                                                   '%Y-%m-%d'),
                                                 volume=True)
            return time_data, price_data

        data = {}
        company = Stock(instrument)
        # a = datetime.now()
        if update:
            data = iex_graph_data(request, data, instrument, company, startdate, enddate, update=True)
        else:
            data = iex_graph_data(request, data, instrument, company, startdate, enddate)
            if len(data['stock_closed']) == 1 and len(data['stock_candle']) == 1:
                if data['stock_closed'][0] == 0.0:
                    messages.warning(request,
                                     'Sorry! For this investment instrument, some data from IEX Cloud are not available.')
                    return data

            data = iex_instrument_details(data, company)
            data = iex_news_data(data, company)

        return data

    elif data_source == 2:
        if home_page:
            ret_data = get_yahoo_only_close(instrument, startdate, enddate)
            return ret_data

        if only_closed and notificiation_event:
            ret_data = get_yahoo_only_close(instrument, startdate, enddate, notification=True)
            return ret_data

        if intraday and notificiation_event:
            ret_data = get_yahoo_intraday_data(instrument, day, notification=True)
            return ret_data

        if intraday:
            ret_data = get_yahoo_intraday_data(instrument, day)
            return ret_data

        if only_closed:
            ret_data = get_yahoo_only_close(instrument, startdate, enddate)
            return ret_data

        if analysis:
            data = {}
            data = yahoo_graph_data(data, instrument, startdate, '')
            return data

        if historical_data:
            time_data, price_data = get_yahoo_ohlc(request.POST['selected_stock'],
                                                   datetime.strptime(request.POST['datepicker_start'],
                                                                    '%Y-%m-%d'),
                                                   datetime.strptime(request.POST['datepicker_end'],
                                                                    '%Y-%m-%d'),
                                                   volume=True)
            return time_data, price_data

        data = {}
        data = yahoo_graph_data(data, instrument, startdate, enddate)
        data = yahoo_instrument_details(data, instrument)
        data = get_yahoo_news(data, instrument)
        return data

