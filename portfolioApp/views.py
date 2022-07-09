import json
from datetime import datetime, timedelta

import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.cache import cache
from django.db.models import F
from django.db.models import Sum, IntegerField
from django.db.models.functions import Coalesce
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse

from logic.modules.lib.messages import create_ajax_message
from logic.modules.lib.prediction.predict_engines import get_prediction
from logic.modules.lib.program_functions.portfolio_manager import delete_instr_from_portf, delete_portfolio, \
    add_instrument_portfolio
from logic.modules.lib.program_functions.stock_viewer import get_stock_count, actual_owned_stock_balance_last
from logic.modules.stock_data_controller.stock_data_controller import get_data
from .forms import PortfolioForm, BuySellStockForm, NotificationEventForm
from .models import Portfolio, OwnedStock, Company, NotificationEvent


def load_instrument_list():
    instruList = []
    x = requests.get(
        'https://sandbox.iexapis.com/v1/ref-data/iex/symbols?token=Tsk_168e230b98fb405684f5be87790ba33b')
    listDicts = json.loads(x.text)
    for dict in listDicts:
        instruList.append(dict['symbol'])
    return instruList


@login_required()
def portfolio_list(request):
    form = UserCreationForm

    if request.method == 'POST' and request.is_ajax():

        if request.POST.__contains__('canceldelete'):
            table_data = Portfolio.objects.all().filter(user=request.user)
            str_table_data = []
            for row in table_data:
                str_table_data.append([row.id, row.name, row.numOwnedStock, row.note])

            response = {'table_data': str_table_data}
            return JsonResponse(response, safe=False)

        if request.POST.__contains__('forcedelete'):
            delete_data = delete_portfolio(request, request.POST['forcedelete'], force=True)

            table_data = Portfolio.objects.all().filter(user=request.user)
            str_table_data = []
            for row in table_data:
                str_table_data.append([row.id, row.name, row.numOwnedStock, row.note])

            response = {'table_data': str_table_data}
            return JsonResponse(response, safe=False)

        if request.POST.__contains__('delete_portfolio'):
            delete_portfolios = request.POST['delete_portfolio']

            delete_data = delete_portfolio(request, delete_portfolios)

            table_data = Portfolio.objects.all().filter(user=request.user)
            str_table_data = []
            for row in table_data:
                str_table_data.append([row.id, row.name, row.numOwnedStock, row.note])

            response = {'table_data': str_table_data, 'delete_data': delete_data}
            return JsonResponse(response, safe=False)

    if request.method == 'POST':

        if Portfolio.objects.filter(user=request.user, name=request.POST['name']).exists():
            messages.error(request, f'Creation failed. Portfolio ' + request.POST['name'] + ' already exists.')
            redirect('portfolio_list')
        else:
            portfolio_form = PortfolioForm(request.POST,
                                           request.FILES)
            if portfolio_form.is_valid():

                data = portfolio_form.cleaned_data

                recipe_data = Portfolio.objects.create(user=request.user, name=data['name'], note=data['note'])
                recipe_data.save()
                messages.success(request, f'Portfolio ' + data['name'] + ' has been created.')
            else:
                errors = portfolio_form.errors
                messages.error(request, f'Portfolio creation failed.')

    table_data = Portfolio.objects.all().filter(user=request.user)
    portfolio_form = PortfolioForm(request=request.user)
    instruList = load_instrument_list()
    return render(request, 'portfolioApp/portfolio_list/portfolio_list.html', {
        'form': form,
        'instruList': instruList,
        'table_data': table_data,
        'portfolio_form': portfolio_form,
        'title': 'Portfolios'
    })


@login_required()
def portfolio(request, portfolio):
    form = UserCreationForm

    ####################################################################################################################
    # If POST request with AJAX
    ####################################################################################################################
    if request.method == 'POST' and request.is_ajax():

        data = {}
        # If want to delete a instrument
        if request.POST.__contains__('delete_instrument'):
            # Which instrument
            instruments_delete = request.POST['instruments']
            # From which portfolio
            portfolio_name = request.POST['url_path']

            result = delete_instr_from_portf(request, instruments_delete)

            if len(result['done']) > 0:
                messages.success(request,
                                 'Successful delete: ' + ",".join(result['done']))
            if len(result['error']) > 0:
                messages.warning(request,
                               'Delete error! Please sell your share before delete: ' + ",".join(result['error']))

            table_data = Company.objects.filter(ownedstock__portfolio__user=request.user,
                                                ownedstock__portfolio__name=portfolio_name).distinct()
            str_table_data = []
            for row in table_data:
                str_table_data.append([row.id, row.symbol, row.name, row.exchange, row.currency, row.region])
            data['table_data'] = str_table_data

            data['messages'] = create_ajax_message(request, messages)
            return HttpResponse(json.dumps(data), content_type="application/json")

        if request.POST.__contains__('add_instrument'):
            instrument_search = request.POST['searchinput']
            portfolio_name = request.POST['portfolio_name']

            add_instrument_portfolio(request, portfolio_name,
                                     instrument_search,
                                     request.user)

            table_data = Company.objects.filter(ownedstock__portfolio__user=request.user,
                                                ownedstock__portfolio__name=portfolio_name).distinct()
            str_table_data = []
            for row in table_data:
                str_table_data.append([row.id, row.symbol, row.name, row.exchange, row.currency, row.region])
            data['table_data'] = str_table_data

            data['messages'] = create_ajax_message(request, messages)
            return HttpResponse(json.dumps(data), content_type="application/json")

    ####################################################################################################################
    # If no AJAX request
    # Then execute main part
    ####################################################################################################################

    portfolio_data = Portfolio.objects.get(name=portfolio,
                                           user=request.user)
    table_data = Company.objects.filter(ownedstock__portfolio__user=request.user,
                                        ownedstock__portfolio__name=portfolio).distinct()

    instruList = load_instrument_list()
    return render(request, 'portfolioApp/portfolio/portfolio.html', {
        'form': form,
        'instruList': instruList,
        'table_data': table_data,
        'portfolio_data': portfolio_data,
        'title': 'Portfolio ' + portfolio
    })

@login_required()
def instrument(request, portfolio, stock):
    # Get searched intrument from URL

    ####################################################################################################################
    # If user wants to show a historical data of instrument
    ####################################################################################################################
    if 'get_historical' in request.GET:
        base_url = reverse('historical_data')
        stock = request.GET['stock']
        startdate = request.GET['startdate']
        enddate = request.GET['enddate']

        # Create redirect URL
        url = '{}?{}&startdate={}&enddate={}'.format(base_url, stock, startdate, enddate)
        return redirect(url)

    ####################################################################################################################
    # If POST request with AJAX
    ####################################################################################################################
    if request.method == 'POST' and request.is_ajax():

        # If want to get intraday data
        if 'change_graph_data_intraday' in request.POST:

            if request.user.profile.source == 1:
                messages.warning(request, 'For IEX CLoud data source, intraday view is not supported.')
                data = {'messages': create_ajax_message(request, messages), 'not_supported': ''}
                return JsonResponse(data, safe=True)

            # Which stock
            stock = request.POST['stock']
            # Which day
            day = request.POST['day']

            # If string from datetimepicker has invalid char at the end
            # Because how datetimepicker works
            if day[-1] == ' ':
                day = day[:-1]

            # Get intraday data
            data = get_data(request, stock, day=day, intraday=True)
            return JsonResponse(data, safe=False)

        # If change interday data
        if 'change_graph_data' in request.POST:
            # Which stock
            stock = request.POST['stock']
            # From date
            startdate = request.POST['startdate']
            # To date
            enddate = request.POST['enddate']

            # If string from datetimepicker has invalid char at the end
            # Because how datetimepicker works
            if startdate[-1] == ' ':
                startdate = startdate[:-1]

            # If string from datetimepicker has invalid char at the end
            # Because how datetimepicker works
            if enddate[-1] == ' ':
                enddate = enddate[:-1]

            # Get data
            data = get_data(request, stock, startdate, enddate, update=True)

            line_chart_axisY_min = min(data['stock_closed'])
            line_chart_axisY_max = max(data['stock_closed'])

            if line_chart_axisY_min != 0:
                line_chart_axisY_min = line_chart_axisY_min * 0.95
            line_chart_axisY_max = line_chart_axisY_max * 1.05

            data['line_chart_axisY_min'] = line_chart_axisY_min
            data['line_chart_axisY_max'] = line_chart_axisY_max

            # Create format [miliseconds, value]
            stock_closed_mili = []
            for item in data['stock_id']:
                # stock_closed_mili.append(datetime.now().timestamp() * 1000)
                stock_closed_mili.append(datetime.strptime((item), '%Y-%m-%d').timestamp() * 1000)

            # Merge data to graph variable
            data['line_chart_data'] = [list(a) for a in zip(stock_closed_mili, data['stock_closed'])]

            # Cache
            if not 'compare_graph_left' in request.POST:
                cache.set('ohlc', data['stock_candle'])
                cache.set('data', data)
            return JsonResponse(data, safe=True)

        # If user wants to buy/sell shares of instrument
        if 'buy_or_sell' in request.POST:
            # req = data from request
            req_type = request.POST['type']
            req_stock = request.POST['stock']
            req_portfolio = request.POST['portfolio']
            req_quantity = request.POST['quantity']
            req_price = request.POST['price']
            req_date = request.POST['date']

            # If something missing -> error
            if req_stock == '' or \
               req_portfolio == '' or \
               req_quantity == '' or \
               req_price == '' or \
               req_date == '':
                messages.warning(request, 'Missing parameter. (Stock, Portfolio, Quantity, Price, Date)')

                data = {'messages': create_ajax_message(request, messages)}
                data['error'] = ''
                return HttpResponse(json.dumps(data), content_type="application/json")

            # check if date is from future -> error
            today_string = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
            today = datetime.strptime(today_string, '%Y-%m-%d %H:%M:%S')
            check_date = datetime.strptime(req_date, '%Y-%m-%d %H:%M:%S')
            if check_date > today:
                if req_type == '1':
                    messages.warning(request, 'Error. Buy time or date is from future. Please select a parameters from'
                                              ' the present or the past. Buy share in future is not possible. '
                                              'It is now '+ today_string)
                elif req_type == '2':
                    messages.warning(request, 'Error. Sell time or date is from future. Please select a parameters from '
                                              'the present or the past. Sell share in future is not possible. '
                                              'It is now '+ today_string)

                data = {'messages': create_ajax_message(request, messages)}
                data['error'] = ''
                return HttpResponse(json.dumps(data), content_type="application/json")


            # check ak je menej nakupenych akcii ako sa me predat ->error
            # type 2 == sell
            if type == '2':
                temp_ownedstock_count = get_stock_count(request, request.POST['stock'], request.POST['portfolio'])
                if int(req_quantity) > temp_ownedstock_count:
                    messages.warning(request,
                                     'Can not be sell more shares than you actually own. '
                                     'You want sell ' + req_quantity +
                                     ' and you actually own ' +temp_ownedstock_count)

                    data = {'messages': create_ajax_message(request, messages)}
                    data['error'] = ''
                    return HttpResponse(json.dumps(data), content_type="application/json")

            # Buy stock
            if request.POST['type'] == '1':
                new_buy = OwnedStock()
                new_buy.type = 1
                new_buy.company_id = Company.objects.get(symbol=request.POST['stock']).id
                new_buy.portfolio_id = Portfolio.objects.get(name=request.POST['portfolio'], user=request.user).id
                new_buy.price = request.POST['price']
                new_buy.quantity = request.POST['quantity']
                new_buy.date = datetime.strptime(request.POST['date'], '%Y-%m-%d %H:%M:%S')
                new_buy.save()

                messages.success(request, 'Stock successfully bought.')

                data = {'messages': create_ajax_message(request, messages)}
                # Create structure for frontend
                end_date = datetime.today()
                start_date = end_date - timedelta(days=4)

                # Perform string cut
                enddate = str(end_date)[:10]
                startdate = str(start_date)[:10]

                # Get all data
                temp_data = get_data(request, request.POST['stock'], startdate, enddate)

                data['ownedstock_count'] = get_stock_count(request, request.POST['stock'], request.POST['portfolio'])
                # data['ownedstock_balance'] = get_actual_balance(request, stock, portfolio)
                data['ownedstock_balance'] = actual_owned_stock_balance_last(request, request.POST['stock'],
                                                                             request.POST['portfolio'],
                                                                             temp_data['stock_closed'][-1])

                return HttpResponse(json.dumps(data), content_type="application/json")

            # sell stock
            else:
                buy_count_ownedstock_in_past = OwnedStock.objects.all().filter(type=1,
                                                                           portfolio__user=request.user,
                                                                           portfolio_id=Portfolio.objects.get(user=request.user,
                                                                                                              name=req_portfolio).id,
                                                                           date__lte=req_date,
                                                                           company_id=Company.objects.get(
                                                                                      symbol=req_stock).id,
                                                                           ).aggregate(
                        sum_result=Coalesce(Sum(F('quantity'), output_field=IntegerField()), 0.0)
                )
                sell_count_ownedstock_in_past = OwnedStock.objects.all().filter(type=2,
                                                                           portfolio__user=request.user,
                                                                           portfolio_id=Portfolio.objects.get(user=request.user,
                                                                                                              name=req_portfolio).id,
                                                                           date__lte=req_date,
                                                                           company_id=Company.objects.get(
                                                                                      symbol=req_stock).id,
                                                                           ).aggregate(
                        sum_result=Coalesce(Sum(F('quantity'), output_field=IntegerField()), 0.0)
                )

                count_ownedstock_in_past = buy_count_ownedstock_in_past['sum_result'] - sell_count_ownedstock_in_past['sum_result']


                # cannot be sold because, there are less available share than user wants to sell
                if int(req_quantity) > count_ownedstock_in_past:
                    all_owned_items = OwnedStock.objects.all().filter(portfolio__user=request.user,
                                                                      quantity__gt=0,
                                                                    date__gt=req_date,
                                                                    portfolio_id=Portfolio.objects.get(
                                                                    user=request.user, name=req_portfolio).id,
                                                                    company_id=Company.objects.get(symbol=req_stock).id,
                                                                    ).order_by('date')
                    # start point = number of owned shares at that time
                    count_quantity = count_ownedstock_in_past

                    last_date = datetime.today()
                    for item in all_owned_items:

                        # get quantity of buy/sell
                        temp_quantity = item.quantity

                        # if buy
                        if item.type == 1:
                            count_quantity += temp_quantity

                            # if number of shares allow to sell
                            # save date for message
                            # but must be verified with first sell item in all_owned_items
                            if count_quantity >= int(req_quantity):
                                last_date = item.date

                        elif item.type == 2:
                            result = count_quantity - (temp_quantity + int(req_quantity))
                            if result >= 0:
                                messages.warning(request,
                                                 'You can not sell shares earlier than you bought it. '
                                                 'If you want to sell this amount of shares, please set date and time '
                                                 'later than ' + str(last_date)[:19])

                                data = {'messages': create_ajax_message(request, messages)}
                                data['error'] = ''
                                return HttpResponse(json.dumps(data), content_type="application/json")
                            else:
                                count_quantity -= temp_quantity

                    # Executed only if response was not sent
                    # Find last buy or sell date and send a response
                    else:
                        item = all_owned_items.reverse()[0]
                        last_date = item.date
                        messages.warning(request,
                                         'You can not sell shares earlier than you bought it. '
                                         'If you want to sell this amount of shares, please set date and time '
                                         'later than ' + str(last_date)[:19])

                        data = {'messages': create_ajax_message(request, messages)}
                        data['error'] = ''
                        return HttpResponse(json.dumps(data), content_type="application/json")


                # if the algorithm comes here then there are enought available share that can be sold
                # but it necessary check, if that amount of share is not already sold with next sell record

                all_owned_items = OwnedStock.objects.all().filter(portfolio__user=request.user,
                                                                  quantity__gt=0,
                                                                  date__gt=req_date,
                                                                  portfolio_id=Portfolio.objects.get(
                                                                      user=request.user, name=req_portfolio).id,
                                                                  company_id=Company.objects.get(symbol=req_stock).id,
                                                                  ).order_by('date')

                count_quantity = count_ownedstock_in_past
                last_date = datetime.today()

                for item in all_owned_items:
                    # get quantity of buy/sell
                    temp_quantity = item.quantity

                    # if buy
                    if item.type == 1:
                        count_quantity += temp_quantity

                        # if number of shares allow to sell
                        # save date for message
                        # but must be verified with first sell item in all_owned_items
                        if count_quantity >= int(req_quantity):
                            last_date = item.date

                    elif item.type == 2:
                        result = count_quantity - (temp_quantity + int(req_quantity))

                        # after first sell record there is still enough amount shares that can be sold
                        if result >= 0:
                            # go sell
                            break

                        # amount is already sold, so algoritm will try find a date when amout could be sold
                        else:
                            all_owned_items = OwnedStock.objects.all().filter(portfolio__user=request.user,
                                                                              quantity__gt=0,
                                                                              date__gt=req_date,
                                                                              portfolio_id=Portfolio.objects.get(
                                                                                  user=request.user,
                                                                                  name=req_portfolio).id,
                                                                              company_id=Company.objects.get(
                                                                                  symbol=req_stock).id,
                                                                              ).order_by('date')
                            # start point = number of owned shares at that time
                            count_quantity = count_ownedstock_in_past

                            last_date = datetime.today()
                            for item in all_owned_items:

                                # get quantity of buy/sell
                                temp_quantity = item.quantity

                                # if buy
                                if item.type == 1:
                                    count_quantity += temp_quantity

                                    # if number of shares allow to sell
                                    # save date for message
                                    # but must be verified with first sell item in all_owned_items
                                    if count_quantity >= int(req_quantity):
                                        last_date = item.date

                                elif item.type == 2:
                                    result = count_quantity - (temp_quantity + int(req_quantity))
                                    if result >= 0:
                                        messages.warning(request,
                                                         'You can not sell shares earlier than you bought it. '
                                                         'If you want to sell this amount of shares, please set date and time '
                                                         'later than ' + str(last_date)[:19])

                                        data = {'messages': create_ajax_message(request, messages)}
                                        data['error'] = ''
                                        return HttpResponse(json.dumps(data), content_type="application/json")
                                    else:
                                        count_quantity -= temp_quantity

                            # Executed only if response was not sent
                            # Find last buy or sell date and send a response
                            else:
                                item = all_owned_items.reverse()[0]
                                last_date = item.date
                                messages.warning(request,
                                                 'You can not sell shares earlier than you bought it. '
                                                 'If you want to sell this amount of shares, please set date and time '
                                                 'later than ' + str(last_date)[:19])

                                data = {'messages': create_ajax_message(request, messages)}
                                data['error'] = ''
                                return HttpResponse(json.dumps(data), content_type="application/json")

                new_sell = OwnedStock()
                new_sell.type = 2
                new_sell.company_id = Company.objects.get(symbol=request.POST['stock']).id
                new_sell.portfolio_id = Portfolio.objects.get(name=request.POST['portfolio'], user=request.user).id
                new_sell.price = request.POST['price']
                new_sell.quantity = request.POST['quantity']
                new_sell.date = datetime.strptime(request.POST['date'], '%Y-%m-%d %H:%M:%S')
                new_sell.save()
                messages.success(request, 'Stock successfully sold.')

                data = {'messages': create_ajax_message(request, messages)}
                # Create structure for frontend
                end_date = datetime.today()
                start_date = end_date - timedelta(days=10)

                # Perform string cut
                enddate = str(end_date)[:10]
                startdate = str(start_date)[:10]

                # Get all data
                temp_data = get_data(request, request.POST['stock'], startdate, enddate)



                data['ownedstock_count'] = get_stock_count(request, request.POST['stock'], request.POST['portfolio'])
                # data['ownedstock_balance'] = get_actual_balance(request, stock, portfolio)
                data['ownedstock_balance'] = actual_owned_stock_balance_last(request, request.POST['stock'],
                                                                             request.POST['portfolio'],
                                                                             temp_data['stock_closed'][-1])

                return HttpResponse(json.dumps(data), content_type="application/json")

        # If user wants to remove a instrument from portfolio
        if 'remove_from_portfolio' in request.POST:
            # check if shares have been purchased
            if OwnedStock.objects.filter(price__gt=0, quantity__gt=0, portfolio__user=request.user,
                                         portfolio__name=request.POST['portfolio'],
                                         company__symbol=request.POST['stock']).exists():
                # with shares -> error
                return JsonResponse({'modal': 'error'}, safe=True)

            else:
                # no shares -> delete
                object = OwnedStock.objects.filter(portfolio__user=request.user,
                                                   portfolio__name=request.POST['portfolio'],
                                                   company__symbol=request.POST['stock'])
                object.delete()
                return JsonResponse({'preview_redirect': '/portfolio/{}/{}/preview/'.format(request.POST['portfolio'],
                                                                                            request.POST['stock'])})

        if 'reset_prediction' in request.POST:
            cache.set('already_predicted', False)
            return JsonResponse({}, safe=True)

        if 'get_prediction' in request.POST:
            if cache.get('already_predicted'):
                data = {}
                data['prediction'] = False
                messages.warning(request, 'Instrument is already predicted.')
                data['messages'] = create_ajax_message(request, messages)
                return JsonResponse(data, safe=True)

            data = cache.get('data')
            cache.set('already_predicted', True)

            predict_num_days = request.POST['prediction']
            custom_length = request.POST['custom_length']
            prediction_type = request.POST['prediction_type']

            # if not set
            try:
                predict_num_days = int(predict_num_days)
            except:
                # 7 is default
                predict_num_days = 7

            # if not set
            try:
                custom_length = int(custom_length)
                if custom_length == 0:
                    messages.warning(request, "From last X days can not be 0.")
                    data = {'custom_length_zero': ''}
                    data['messages'] = create_ajax_message(request, messages)
                    cache.set('already_predicted', False)
                    return JsonResponse(data, safe=True)
            except:
                # 0 is all
                custom_length = 0

            if predict_num_days == 0:
                messages.warning(request, "Prediction is set for 0 days.")
                data = {'prediction_zero_days': ''}
                data['messages'] = create_ajax_message(request, messages)
                cache.set('already_predicted', False)
                return JsonResponse(data, safe=True)

            if predict_num_days < 0:
                messages.warning(request, "Prediction can not be negative number.")
                data = {'prediction_negative': ''}
                data['messages'] = create_ajax_message(request, messages)
                cache.set('already_predicted', False)
                return JsonResponse(data, safe=True)

            if custom_length < 0:
                messages.warning(request, "Base(from last X days) can not be negative number.")
                data = {'custom_length_negative': ''}
                data['messages'] = create_ajax_message(request, messages)
                cache.set('already_predicted', False)
                return JsonResponse(data, safe=True)


            data = get_prediction(request, data, prediction_type, predict_num_days, custom_length)

            if 'news' in data:
                data.pop('news', None)

            stock_closed_mili = []
            for item in data['prediction_days']:
                # stock_closed_mili.append(datetime.now().timestamp() * 1000)
                stock_closed_mili.append(datetime.strptime((item), '%Y-%m-%d').timestamp() * 1000)

            data['prediction'] = [list(a) for a in zip(stock_closed_mili, data['prediction_prices'])]
            data['messages'] = create_ajax_message(request, messages)
            return JsonResponse(data, safe=True)

        ################################################################################################################
        ################################################################################################################
        #                                            POST
        ################################################################################################################
        ################################################################################################################

    if request.method == 'POST':

        notification_event_form = NotificationEventForm(request.POST,
                                                        request.FILES)

        if notification_event_form.is_valid():
            if request.user.email != '':
                data = notification_event_form.cleaned_data

                # Interday
                if data['type'] == 1:
                    actual_time = datetime.now()
                    actual_time = str(actual_time)[:10]
                    instrument_data = get_data(request=False,
                                               instrument=stock,
                                               startdate=actual_time,
                                               enddate=actual_time,
                                               only_closed=True,
                                               notificiation_event=True)

                    price = instrument_data[-1]

                    ret = NotificationEvent.objects.create(user=request.user,
                                                           company=Company.objects.get(symbol=stock),
                                                           on_change=data['on_change'],
                                                           saved_price=price,
                                                           type=data['type'],
                                                           notify=data['notify']
                                                           )

                    ret.save()

                # Intraday
                else:
                    actual_time = datetime.now()
                    actual_time = str(actual_time)[:10]
                    instrument_data = get_data(request=False,
                                               instrument=stock,
                                               day=actual_time,
                                               enddate=actual_time,
                                               intraday=True,
                                               notificiation_event=True)

                    price = instrument_data['Close'][-1]

                    ret = NotificationEvent.objects.create(user=request.user,
                                                           company=Company.objects.get(symbol=stock),
                                                           on_change=data['on_change'],
                                                           saved_price=price,
                                                           type=data['type'],
                                                           notify=data['notify']
                                                           )

                    ret.save()
            else:
                messages.warning(requests, 'Failed to create notification. First, add your email in profile, please. Then try again.')

        else:
            messages.warning(requests, 'Failed to create notification. Form was not valid.')


    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################
    # Main part
    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################

    # If comapny exists in database, if not, then open as preview instrument and
    # If instrument is in portfolio
    if Company.objects.filter(symbol=stock).exists():

        form = UserCreationForm

        # Get navbar data
        portfolio_data = Portfolio.objects.get(name=portfolio, user=request.user)
        company_data = Company.objects.get(symbol=stock)

        # If there is not even an init record in OwnedStocks table (price==0, quantity==0)
        # then redirect
        if not OwnedStock.objects.filter(portfolio_id=portfolio_data.id,
                                         company_id=company_data.id,
                                         portfolio__user=request.user).exists():
            return redirect(request.path + 'preview/')

        # Get startdate and enddate, interval of Axis X
        startdate = ''
        enddate = ''

        # optional_GET_string = ''

        # If it is specified by URL
        if 'startdate' in request.GET and 'enddate' in request.GET:
            startdate = request.GET['startdate']
            enddate = request.GET['enddate']

        # If it is NOT specified by URL
        else:
            end_date = datetime.today()
            start_date = end_date - timedelta(days=30)

            # Perform string cut
            enddate = str(end_date)[:10]
            startdate = str(start_date)[:10]
            if not request.GET._mutable:
                request.GET._mutable = True
            request.GET['startdate'] = startdate
            request.GET['enddate'] = enddate
            optional_GET_string = '?startdate='+startdate+'&enddate='+enddate
            return HttpResponseRedirect(request.path + optional_GET_string)

        # Get all data
        data = get_data(request, request.resolver_match.kwargs['stock'], startdate, enddate)

        line_chart_axisY_min = min(data['stock_closed'])
        line_chart_axisY_max = max(data['stock_closed'])

        if line_chart_axisY_min != 0:
            line_chart_axisY_min = line_chart_axisY_min * 0.95
        line_chart_axisY_max = line_chart_axisY_max * 1.05

        data['line_chart_axisY_min'] = line_chart_axisY_min
        data['line_chart_axisY_max'] = line_chart_axisY_max

        stock_closed_mili = []
        for item in data['stock_id']:
            # stock_closed_mili.append(datetime.now().timestamp() * 1000)
            stock_closed_mili.append(datetime.strptime((item), '%Y-%m-%d').timestamp() * 1000)

        data['line_chart_data'] = [list(a) for a in zip(stock_closed_mili, data['stock_closed'])]

        # Set up buy/sell form
        BuySellStockForm_form = BuySellStockForm(instance=request.user.profile, request=request.user)
        notification_event_form = NotificationEventForm(instance=request.user.profile, request=request.user)

        # Create structure for frontend
        data['ownedstock_count'] = get_stock_count(request, stock, portfolio)
        # data['ownedstock_balance'] = get_actual_balance(request, stock, portfolio)
        data['ownedstock_balance'] = actual_owned_stock_balance_last(request, stock, portfolio,
                                                                     data['stock_closed'][-1])

        data['messages'] = create_ajax_message(request, messages)
        cache.set('ohlc', data['stock_candle'])
        cache.set('data', data)
        cache.set('already_predicted', False)
        cache.set('already_predicted_intraday', False)
        instruList = load_instrument_list()
        return render(request, 'portfolioApp/instrument/instrument.html',
                      {'form': form,
                       'data': data,
                       'BuySellStockForm_form': BuySellStockForm_form,
                       'notification_event_form': notification_event_form,
                        'instruList': instruList,
                        # Navbar
                       'portfolio_data': portfolio_data,
                       'stock_data': company_data,
                       'title': 'Instrument ' + stock
        })

    else:
        return redirect(request.path + 'preview/')


@login_required()
def instrument_preview(request, portfolio, stock):
    # Get searched intrument from URL

    if not Portfolio.objects.filter(user=request.user, name=portfolio).exists() and \
            request.method != 'POST' and \
            request.method != 'GET' and \
            not request.is_ajax():
        messages.error(request, 'Portfolio ' + portfolio + ' not exists.')
        return redirect('portfolio_list')

    if 'get_historical' in request.GET:
        base_url = reverse('historical_data')
        # query_string = urlencode({'stock': stock})
        stock = request.GET['stock']
        startdate = request.GET['startdate']
        enddate = request.GET['enddate']

        url = '{}?{}&startdate={}&enddate={}'.format(base_url, stock, startdate, enddate)
        return redirect(url)

    if request.method == 'POST' and request.is_ajax():

        if 'add_to_portfolio' in request.POST:
            add_instrument_portfolio(request, request.POST['portfolio'], request.POST['stock'], request.user)
            return JsonResponse(
                {'new_stock_in_portfolio_redirect': '/portfolio/{}/{}/'.format(request.POST['portfolio'],
                                                                               request.POST['stock'])})

        if 'startdate' in request.POST and 'enddate' in request.POST:

            stock = request.POST['stock']
            startdate = request.POST['startdate']
            enddate = request.POST['enddate']

            if startdate[-1] == ' ':
                startdate = startdate[:-1]

            if enddate[-1] == ' ':
                enddate = enddate[:-1]

            data = get_data(request, stock, startdate, enddate, update=True)
            cache.set('ohlc', data['stock_candle'])
            return JsonResponse(data, safe=True)

    if not Portfolio.objects.filter(user=request.user, name=portfolio).exists():
        messages.error(request, 'Portfolio ' + portfolio + ' not exists.')
        return redirect('portfolio_list')

    form = UserCreationForm
    url_instr = request.resolver_match.kwargs['stock']

    startdate = ''
    enddate = ''
    if 'startdate' in request.GET and 'enddate' in request.GET:
        startdate = request.GET['startdate']
        enddate = request.GET['enddate']
    else:
        end_date = datetime.today()
        start_date = end_date - timedelta(days=30)

        enddate = str(end_date)[:10]
        startdate = str(start_date)[:10]

    data = {}
    try:
        data = get_data(request, url_instr, startdate, enddate)
    except Exception as e:
        if hasattr(e, 'status') and hasattr(e, 'response'):
            messages.error(request, e.response)
            return redirect('portfolio_list')

    portfolio_data = Portfolio.objects.get(name=portfolio, user=request.user)

    return render(request, 'portfolioApp/instrument_preview/instrument_preview.html', {
        'data': data,
        'form': form,

        # Navbar
        'portfolio_data': portfolio_data,

        'title': 'Instrument ' + stock + ' preview'
    })
