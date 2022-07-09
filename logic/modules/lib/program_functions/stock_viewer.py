from datetime import datetime, timedelta

from django.db.models import F, FloatField
from django.db.models import Sum
from django.db.models.functions import Coalesce

from logic.modules.stock_data_controller.stock_data_controller import get_data
from portfolioApp.models import OwnedStock, Company, Portfolio


def actual_owned_stock_balance_last(request, stock_symbol, portfolio_name, last_stock_price):

        buy_sum = OwnedStock.objects.filter(type=1,
                                            company_id=Company.objects.get(symbol=stock_symbol).id,
                                            portfolio_id=Portfolio.objects.get(name=portfolio_name,
                                                                               user=request.user).id
                                            ).aggregate(
            # Coalesce(Expr, Default value if Expr is None -> If no rows)
            sum_result=Coalesce(Sum(F('quantity'), output_field=FloatField()), 0.0)
        )

        sell_sum = OwnedStock.objects.filter(type=2,
                                             company_id=Company.objects.get(symbol=stock_symbol).id,
                                             portfolio_id=Portfolio.objects.get(name=portfolio_name,
                                                                                user=request.user).id
                                             ).aggregate(
            sum_result=Coalesce(Sum(F('quantity'), output_field=FloatField()), 0.0)
        )

        stock_balance = (buy_sum['sum_result'] - sell_sum['sum_result']) * last_stock_price


        return stock_balance


def get_actual_balance(request, stock, portfolio, is_date=False, date_lte=''):

    if is_date:

        buy_sum = OwnedStock.objects.filter(type=1,
                                            date__lte=date_lte,
                                            company_id=Company.objects.get(symbol=stock).id,
                                            portfolio_id=Portfolio.objects.get(name=portfolio,
                                                                               user=request.user).id
                                            ).aggregate(
            # Coalesce(Expr, Default value if Expr is None -> If no rows)
            sum_result=Coalesce(Sum(F('price') * F('quantity'), output_field=FloatField()), 0.0)
        )

        sell_sum = OwnedStock.objects.filter(type=2,
                                             date__lte=date_lte,
                                             company_id=Company.objects.get(symbol=stock).id,
                                             portfolio_id=Portfolio.objects.get(name=portfolio,
                                                                                user=request.user).id
                                             ).aggregate(
            sum_result=Coalesce(Sum(F('price') * F('quantity'), output_field=FloatField()), 0.0)
        )

        stock_balance = buy_sum['sum_result'] - sell_sum['sum_result']
        return stock_balance

    else:
        buy_sum = OwnedStock.objects.filter(type=1,
                                            company_id=Company.objects.get(symbol=stock).id,
                                            portfolio_id=Portfolio.objects.get(name=portfolio,
                                                                               user=request.user).id
                                            ).aggregate(
            # Coalesce(Expr, Default value if Expr is None -> If no rows)
            sum_result=Coalesce(Sum(F('price') * F('quantity'), output_field=FloatField()), 0.0)
        )

        sell_sum = OwnedStock.objects.filter(type=2,
                                             company_id=Company.objects.get(symbol=stock).id,
                                             portfolio_id=Portfolio.objects.get(name=portfolio,
                                                                                user=request.user).id
                                             ).aggregate(
            sum_result=Coalesce(Sum(F('price') * F('quantity'), output_field=FloatField()), 0.0)
        )

        stock_balance = buy_sum['sum_result'] - sell_sum['sum_result']
        return stock_balance


def get_stock_count(request, stock_name, portfolio_name, is_date=False ,startdate=False, enddate=False):

    buy_count = OwnedStock.objects.filter(type=1,
                                                price__gt=0, quantity__gt=0,
                                                portfolio_id=Portfolio.objects.get(name=portfolio_name,
                                                                                   user=request.user).id,
                                                company=Company.objects.get(symbol=stock_name).id,
                                                portfolio__user=request.user
                                          ).aggregate(
            sum_result=Coalesce(Sum(F('quantity'), output_field=FloatField()), 0.0)
    )


    sell_count = OwnedStock.objects.filter(type=2,
                                                price__gt=0, quantity__gt=0,
                                                portfolio_id=Portfolio.objects.get(name=portfolio_name,
                                                                                   user=request.user).id,
                                                company=Company.objects.get(symbol=stock_name).id,
                                                portfolio__user=request.user
                                          ).aggregate(
            sum_result=Coalesce(Sum(F('quantity'), output_field=FloatField()), 0.0)
    )

    ownedstock_count = buy_count['sum_result'] - sell_count['sum_result']

    return int(ownedstock_count)


def store_date_array(date):
    analysis_chart_pointstart = {}
    analysis_chart_pointstart['day'] = date[8:10]
    analysis_chart_pointstart['month'] = str(int(date[6:7]) - 1)  # -1 for graph annomaly
    analysis_chart_pointstart['year'] = date[:4]
    return analysis_chart_pointstart


def get_owned_stock_analysis(stock_by_day, owned_stock_data):
    not_replace_index = []

    for stock_object in stock_by_day.iterator():
        if str(stock_object['date__date']) in owned_stock_data:
            not_replace_index.append(owned_stock_data.index(str(stock_object['date__date'])))
            owned_stock_data[owned_stock_data.index(str(stock_object['date__date']))] = stock_object['sum']

    for idx, temp in enumerate(owned_stock_data):
        if idx not in not_replace_index:
            owned_stock_data[idx] = 0

    save_stock_value = 0
    for idx, temp in enumerate(owned_stock_data):
        if temp == 0:
            owned_stock_data[idx] = save_stock_value
        else:
            save_stock_value = save_stock_value + temp
            owned_stock_data[idx] = save_stock_value

    return owned_stock_data


def get_balance_stock_analysis(sum_stock_by_day, balance_stock_data):
    not_replace_index = []

    for stock_object in sum_stock_by_day.iterator():
        if str(stock_object['date__date']) in balance_stock_data:
            not_replace_index.append(balance_stock_data.index(str(stock_object['date__date'])))
            balance_stock_data[balance_stock_data.index(str(stock_object['date__date']))] = stock_object['sum']

    for idx, temp in enumerate(balance_stock_data):
        if idx not in not_replace_index:
            balance_stock_data[idx] = 0

    save_stock_value = 0
    for idx, temp in enumerate(balance_stock_data):
        if temp == 0:
            balance_stock_data[idx] = save_stock_value
        else:
            save_stock_value = save_stock_value + temp
            balance_stock_data[idx] = save_stock_value

    return balance_stock_data


def get_owned_stock_balance(stock_prices, owned_stocks):

    balance_array = []

    for idx, temp in enumerate(stock_prices):
        balance_array.append(stock_prices[idx] * owned_stocks[idx])

    return balance_array



def get_price_change_stock(price_change_stock):
    array_len = len(price_change_stock)
    price_change_data = [0.0]
    for idx, value in enumerate(price_change_stock):
        if idx == (array_len-1):
            break
        price_change_data.append(((price_change_stock[idx+1]-value)/value)*100)

    return price_change_data

def get_graph_stock_analysis(stock_id, stock_closed,
                             owned_stock_data,
                             price_change_data,
                             balance_stock_data,
                             actual_owned_stock_balance):



    main_data = {"xData": [], 'datasets':[]}
    main_data['xData'] = [str(obj_date) for obj_date in stock_id]

    datasets_data = []
    graph_data = {'name': '',
                 'data': [],
                 'unit': '',
                 'type': '',
                 'valueDecimals': ''
                 }

    graph_data['name'] = 'Stock price'
    graph_data['data'] = stock_closed
    graph_data['unit'] = '$'
    graph_data['type'] = 'line'
    graph_data['valueDecimals'] = '1'
    datasets_data.append(graph_data.copy())

    graph_data['name'] = 'Owned shares'
    graph_data['data'] = owned_stock_data
    graph_data['unit'] = 'shares'
    graph_data['type'] = 'line'
    graph_data['valueDecimals'] = '1'
    datasets_data.append(graph_data.copy())

    graph_data['name'] = 'Daily stock change'
    graph_data['data'] = price_change_data
    graph_data['unit'] = '%'
    graph_data['type'] = 'column'
    graph_data['valueDecimals'] = '1'
    datasets_data.append(graph_data.copy())

    graph_data['name'] = 'Balance'
    graph_data['data'] = balance_stock_data
    graph_data['unit'] = '$'
    graph_data['type'] = 'line'
    graph_data['valueDecimals'] = '1'
    datasets_data.append(graph_data.copy())

    graph_data['name'] = 'Owned stock balance'
    graph_data['data'] = actual_owned_stock_balance
    graph_data['unit'] = '$'
    graph_data['type'] = 'line'
    graph_data['valueDecimals'] = '1'
    datasets_data.append(graph_data.copy())


    main_data['datasets'] = datasets_data
    return main_data


def get_portfolios_stock_stats(all_portfolios_data):

    stocks_last_balance = {}

    stock_count = 0
    total_value = 0.0
    # ['RealPortfolio']['JKE']['owned_stock_balance_last']
    for portfolio in all_portfolios_data.keys():
        stocks_last_balance[portfolio] = {}
        for stock in all_portfolios_data[portfolio].keys():
            stock_count += int(all_portfolios_data[portfolio][stock]['stock_count'])
            total_value += float(all_portfolios_data[portfolio][stock]['stock_value'])
            stocks_last_balance[portfolio][stock] = int(all_portfolios_data[portfolio][stock]['stock_count'])


    return stock_count, stocks_last_balance, total_value


def get_portfolios_data(request):

    portfolios_data = {}
    # get all user's portfolios from db
    portfolios = Portfolio.objects.filter(user=request.user).all()

    for portfolio in portfolios:
        portfolios_data[portfolio.name] = get_portfolio_data(request, portfolio)

    portfolios_stock_count, stocks_last_balance_dict, total_value = get_portfolios_stock_stats(portfolios_data)

    temp_data = []
    card_data = []
    btn_index = 0
    for temp_portfolio in stocks_last_balance_dict:
        temp_stock_array = []
        for temp_stock in stocks_last_balance_dict[temp_portfolio]:
            temp_stock_array.append([temp_stock,stocks_last_balance_dict[temp_portfolio][temp_stock]])

        portfolio_note = Portfolio.objects.get(name=temp_portfolio, user=request.user).note

        temp_data.append([btn_index, temp_portfolio, temp_stock_array, portfolio_note])

        btn_index = btn_index + 1

        # Because portfolio panel on homepage has 3 cards
        if len(temp_data) == 3:
            card_data.append(temp_data)
            temp_data = []

    # if not temp_data[-1]:
    #     del temp_data[-1]

    # save last 6 or less iterations
    # if not empty
    if temp_data:
        card_data.append(temp_data)


    ret_data = {}
    ret_data['portfolios_stock_count'] = portfolios_stock_count
    ret_data['stocks_last_balance_dict'] = stocks_last_balance_dict
    ret_data['total_value'] = round(total_value, 4)
    ret_data['card_data'] = card_data
    return ret_data

def get_portfolio_data(request, portfolio):

    temp_portfolio_data = {}
    # get portfolio stocks
    owned_stocks = OwnedStock.objects.filter(portfolio__user=request.user,
                                            portfolio_id=portfolio.id,
                                            price=0, quantity=0).all()

    for stock in owned_stocks:
        temp_portfolio_data[stock.company.symbol] = get_instrument_data(request,portfolio,stock)

    # portfolio_data[portfolio.name] = temp_portfolio_data[0]
    return temp_portfolio_data


def get_instrument_data(request,portfolio,stock):
    temp_instrument_data = {}

    end_date = datetime.today()
    start_date = end_date - timedelta(days=21)

    last_closed_price = get_data(request,
                                 stock.company.symbol,
                                 str(start_date)[:10],
                                 str(end_date)[:10], home_page=True)
    last_closed_price = last_closed_price[-1]

    temp_instrument_data['owned_stock_balance_last'] = (actual_owned_stock_balance_last(request,
                                                                                   stock.company.symbol,
                                                                                   portfolio.name,
                                                                                   last_closed_price))

    stock_count = get_stock_count(request, stock.company.symbol, portfolio.name)
    temp_instrument_data['stock_count'] = stock_count
    temp_instrument_data['stock_value'] = round(last_closed_price * stock_count, 4)

    return temp_instrument_data

