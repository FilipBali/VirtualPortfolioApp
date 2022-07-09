from datetime import datetime

from django.db.models import Sum, F, Q
from django.db.models.functions import Coalesce

from logic.modules.lib.program_functions.stock_viewer import get_owned_stock_balance, \
    get_owned_stock_analysis
from logic.modules.stock_data_controller.stock_data_controller import get_data
from portfolioApp.models import Portfolio, OwnedStock


def portfolio_details_data(request, portfolio):
    # variable init
    details_data = {}
    details_data_time_intervals = {}
    stats_data = {}
    actual_own_count = {}

    # Get all instruments of portfolio
    if not OwnedStock.objects.filter(portfolio__user=request.user,
                                     portfolio_id=Portfolio.objects.get(name=portfolio,
                                                                        user=request.user).id,
                                     price=0, quantity=0).exists():
        # No stocks in portfolio
        return 'no_stock_in_portfolio'

    # Get all instruments of portfolio
    portfolio_stocks = OwnedStock.objects.filter(portfolio__user=request.user,
                                            portfolio_id=Portfolio.objects.get(name=portfolio,
                                                                               user=request.user).id,
                                            price=0, quantity=0).all()


    if not OwnedStock.objects.filter(price__gt=0,
                                     quantity__gt=0,
                                     type=1,
                                     portfolio_id=Portfolio.objects.get(name=portfolio,
                                                                        user=request.user).id).exists():
        return 'no_bought_stock'

    # Get all bought stocks of portfolio
    bought_portfolio_stocks = OwnedStock.objects.filter(price__gt=0,
                              quantity__gt=0,
                              type=1,
                              portfolio_id=Portfolio.objects.get(name=portfolio,
                                                                 user=request.user).id).order_by('date__date')

    # Get date of first bought stock
    first_stock_record_date = bought_portfolio_stocks[0].date

    end_date = datetime.today()
    start_date = first_stock_record_date
    # Perform string cut
    end_date = str(end_date)[:10]
    start_date = str(start_date)[:10]

    data = {}
    # Iterate in all portfolio stocks
    for stock in portfolio_stocks:
        # Get insturent data
        data = get_data(request, stock.company.symbol, start_date, end_date)

        # Get all stocks bought/sold
        portfolio_stocks_trading_data = OwnedStock.objects.filter(price__gt=0,
                                                                  quantity__gt=0,
                                                                  date__gte=start_date,
                                                                  date__lte=end_date,
                                                                  company__symbol=stock.company.symbol,
                                                                  portfolio_id=Portfolio.objects.get(name=portfolio,
                                                                                                     user=request.user).id)

        # TODO
        if portfolio_stocks_trading_data.count() == 0:
            details_data[stock.company.symbol] = [0 for x in range(0, len(data['stock_id']))]
            details_data_time_intervals[stock.company.symbol] = [data['stock_id'][0], data['stock_id'][-1]]
            continue

        # Sum quantity by days
        stock_by_day = portfolio_stocks_trading_data.values('date__date').order_by('date__date').annotate(
                # sum=Sum('quantity')
                sum=Coalesce(Sum(F('quantity'), filter=Q(type=1)), 0.0) -
                    Coalesce(Sum(F('quantity'), filter=Q(type=2)), 0.0)
        )

        owned_stock_data = get_owned_stock_analysis(stock_by_day, data['stock_id'].copy())
        actual_owned_stock_balance = get_owned_stock_balance(data['stock_closed'].copy(), owned_stock_data.copy())

        details_data_time_intervals[stock.company.symbol] = [data['stock_id'][0], data['stock_id'][-1]]
        details_data[stock.company.symbol] = actual_owned_stock_balance
        stats_data[stock.company.symbol] = (((data['stock_closed'][-1] - data['stock_closed'][-2]) /
                                               data['stock_closed'][-2]) * 100)

        actual_own_count[stock.company.symbol] = owned_stock_data[-1]

    # else:
    #     # TODO skontrolovat
    #     data['stock_id'] = [end_date]
    #     data['portfolio_closed'] = [0.0]

    # Find stock with the biggest X axis
    max_len = 0
    max_key = ""
    for stock in details_data:
        cur_len = len(details_data[stock])
        if cur_len > max_len:
            max_key = stock
            max_len = cur_len

    # Transform all stocks that has smaller X axis
    for stock in details_data:
        if len(details_data[stock]) != max_len:
            add_count = max_len - len(details_data[stock])
            zeros_array_to_add = [0 for x in range(0, add_count)]

            if details_data_time_intervals[stock][-1] == details_data_time_intervals[max_key][-1]:
                details_data[stock] = zeros_array_to_add + details_data[stock]

            elif details_data_time_intervals[stock][0] == details_data_time_intervals[max_key][0]:
                details_data[stock] = details_data[stock] + zeros_array_to_add

            else:
                ...
                print('Axis X transforming error')
                # start_index = details_data_time_intervals[max_key].index(details_data_time_intervals[stock][0])
                # end_index = details_data_time_intervals[max_key].index(details_data_time_intervals[stock][-1])
                # details_data[stock] = zeros_array_to_add[:start_index] + \
                #                       details_data[stock] + \
                #                       zeros_array_to_add[end_index:]


    sorted_stats_data= dict(sorted(stats_data.items(), key=lambda item: item[1]))

    top3_increase = []
    for x in list(sorted_stats_data)[0:3]:
        if sorted_stats_data[x] > 0:
            top3_increase.append(str(x) + ' ('+str(round(sorted_stats_data[x], 2)) + ' %) ')

    top3_decrease = []
    for x in list(reversed(list(sorted_stats_data)))[0:3]:
        if sorted_stats_data[x] < 0:
            top3_decrease.append(str(x) + ' ('+str(round(sorted_stats_data[x], 2)) + ' %) ')


    retdata = {'stock_id': data['stock_id']}
    retdata['portfolio_closed'] = [sum(elts) for elts in zip(*details_data.values())]

    if len(retdata['portfolio_closed']) !=0:
        if len(retdata['portfolio_closed']) == 1:
            retdata['portfolio_change'] = 0.0
        else:
            if retdata['portfolio_closed'][-2] == 0.0:
                retdata['portfolio_change'] = 0.0
            else:
                retdata['portfolio_change'] = round((((retdata['portfolio_closed'][-1]-retdata['portfolio_closed'][-2]) /
                                                           retdata['portfolio_closed'][-2]) * 100), 2)
    else:
        retdata['portfolio_change'] = ''

    retdata['stats_data'] = stats_data
    retdata['actual_own_count'] = actual_own_count

    retdata['top3_increase'] = top3_increase
    retdata['top3_decrease'] = top3_decrease



    return retdata