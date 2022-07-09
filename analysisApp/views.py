import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, FloatField, Q
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render

from logic.modules.lib.program_functions.stock_viewer import store_date_array, \
    get_owned_stock_analysis, get_balance_stock_analysis, get_price_change_stock, get_graph_stock_analysis, \
    get_owned_stock_balance
from logic.modules.stock_data_controller.stock_data_controller import get_data
from portfolioApp.models import Portfolio, OwnedStock, Company


@login_required()
def portfolio_analysis(request, portfolio):

    data = {}

    if request.method == 'POST' and request.is_ajax():

        if 'update' in request.POST:

            if request.POST['stock'] == 'All':
                update_data = OwnedStock.objects.filter(price__gt=0,
                                                        quantity__gt=0,
                                                        date__gte=request.POST['datepicker_start'],
                                                        date__lte=request.POST['datepicker_end'],
                                                        portfolio=Portfolio.objects.get(name=request.POST['portfolio'],
                                                                                        user=request.user).id)
            else:
                update_data = OwnedStock.objects.filter(price__gt=0,
                                                        quantity__gt=0,
                                                        date__gte=request.POST['datepicker_start'],
                                                        date__lte=request.POST['datepicker_end'],
                                                        company__symbol=request.POST['stock'],
                                                        portfolio=Portfolio.objects.get(name=request.POST['portfolio'],
                                                                                        user=request.user).id)

            str_price_data = []
            for row in update_data:
                str_price_data.append([row.date, row.price, row.quantity, row.companyName])
            return JsonResponse(str_price_data, safe=False)

    portfolio_stocks_trading_data = OwnedStock.objects.filter(price__gt=0,
                                                              quantity__gt=0,
                                                              portfolio=Portfolio.objects.get(name=portfolio,
                                                                                              user=request.user).id)

    # get all instrument of user (in all portfolios)
    user_company = Company.objects.values_list('symbol', flat=True).filter(
        ownedstock__portfolio__user=request.user
    ).distinct()

    portfolio_data = Portfolio.objects.get(name=portfolio, user=request.user)
    return render(request, 'portfolioApp/portfolio_analysis/portfolio_analysis.html', {
        'portfolio_data': portfolio_data,
        'portfolio_stocks_trading_data': portfolio_stocks_trading_data,
        'user_company': user_company,
        'title': portfolio + ' analysis'
    })


@login_required()
def instrument_analysis(request, portfolio, stock):
    if request.method == 'POST' and request.is_ajax():

        if 'update' in request.POST:
            resp = {}

            update_data = OwnedStock.objects.filter(price__gt=0,
                                                    quantity__gt=0,
                                                    date__gte=request.POST['datepicker_start'],
                                                    date__lte=request.POST['datepicker_end'],
                                                    company__symbol=request.POST['stock'],
                                                    portfolio=Portfolio.objects.get(name=request.POST['portfolio'],
                                                                                    user=request.user).id)

            str_price_data = []
            for row in update_data:
                str_price_data.append([row.date, row.price, row.quantity])

            resp['str_price_data'] = str_price_data

            portfolio_stocks_trading_data = OwnedStock.objects.filter(price__gt=0,
                                                                      quantity__gt=0,
                                                                      date__gte=request.POST['datepicker_start'],
                                                                      date__lte=request.POST['datepicker_end'],
                                                                      company__symbol=request.POST['stock'],
                                                                      portfolio=Portfolio.objects.get(
                                                                          name=request.POST['portfolio'],
                                                                          user=request.user).id)

            if portfolio_stocks_trading_data.count() == 0:
                messages.warning(request, 'No shares')
                return redirect('instrument', portfolio=portfolio, stock=stock)

            # spocita quantitu za den
            stock_by_day = portfolio_stocks_trading_data.values('date__date').order_by('date__date').annotate(

                sum=Coalesce(Sum(F('quantity'), filter=Q(type=1)), 0.0) -
                    Coalesce(Sum(F('quantity'), filter=Q(type=2)), 0.0)
            )


            sum_stock_by_day = portfolio_stocks_trading_data.values('date__date').order_by('date__date').annotate(
                sum=Coalesce(Sum(F('price') * F('quantity'), filter=Q(type=2), output_field=FloatField()), 0.0) -
                    Coalesce(Sum(F('price') * F('quantity'), filter=Q(type=1), output_field=FloatField()), 0.0)
            )


            data = get_data(request, request.POST['stock'], request.POST['datepicker_start'], request.POST['datepicker_end'],
                            update=True)

            analysis_chart_pointstart = store_date_array(request.POST['datepicker_start'])

            owned_stock_data = get_owned_stock_analysis(stock_by_day, data['stock_id'].copy())

            balance_stock_data = get_balance_stock_analysis(sum_stock_by_day, data['stock_id'].copy())
            actual_owned_stock_balance = get_owned_stock_balance(data['stock_closed'].copy(), owned_stock_data.copy())

            price_change_data = get_price_change_stock(data['stock_closed'].copy())

            main_data = get_graph_stock_analysis(data['stock_id'].copy(),
                                                 data['stock_closed'].copy(),
                                                 owned_stock_data,
                                                 price_change_data,
                                                 balance_stock_data,
                                                 actual_owned_stock_balance)

            graph_json_data = json.dumps(main_data)

            resp['analysis_chart_pointstart'] = analysis_chart_pointstart
            resp['graph_json_data'] = graph_json_data

            return JsonResponse(resp, safe=False)

    portfolio_stocks_trading_data = OwnedStock.objects.filter(price__gt=0,
                                                              quantity__gt=0,
                                                              company__symbol=stock,
                                                              portfolio=Portfolio.objects.get(name=portfolio,
                                                                                              user=request.user).id)

    if portfolio_stocks_trading_data.count() == 0:
        messages.warning(request, 'No shares')
        return redirect('instrument', portfolio=portfolio, stock=stock)

    # spocita quantitu za den
    stock_by_day = portfolio_stocks_trading_data.values('date__date').order_by('date__date').annotate(

        sum=Coalesce(Sum(F('quantity'), filter=Q(type=1)), 0.0) - Coalesce(Sum(F('quantity'), filter=Q(type=2)), 0.0)
    )

    #
    sum_stock_by_day = portfolio_stocks_trading_data.values('date__date').order_by('date__date').annotate(
        sum=Coalesce(Sum(F('price') * F('quantity'), filter=Q(type=2), output_field=FloatField()), 0.0) -
            Coalesce(Sum(F('price') * F('quantity'), filter=Q(type=1), output_field=FloatField()), 0.0)
    )

    the_earliest_date = portfolio_stocks_trading_data.order_by('date')[0]
    the_earliest_date = str(the_earliest_date.date)[:10]

    the_latest_date = portfolio_stocks_trading_data.order_by('-date')[0]
    the_latest_date = str(the_latest_date.date)[:10]

    # Get financial data for stock
    data = get_data(request, stock, the_earliest_date, the_latest_date, update=True, analysis=True)

    # split date to dict
    analysis_chart_pointstart = store_date_array(the_earliest_date)

    owned_stock_data = get_owned_stock_analysis(stock_by_day, data['stock_id'].copy())

    balance_stock_data = get_balance_stock_analysis(sum_stock_by_day, data['stock_id'].copy())
    actual_owned_stock_balance = get_owned_stock_balance(data['stock_closed'].copy(), owned_stock_data.copy())

    price_change_data = get_price_change_stock(data['stock_closed'].copy())

    main_data = get_graph_stock_analysis(data['stock_id'].copy(),
                                         data['stock_closed'].copy(),
                                         owned_stock_data,
                                         price_change_data,
                                         balance_stock_data,
                                         actual_owned_stock_balance)

    graph_json_data = json.dumps(main_data)

    portfolio_data = Portfolio.objects.get(name=portfolio, user=request.user)
    company_data = Company.objects.get(symbol=stock)
    return render(request, 'portfolioApp/instrument_analysis/instrument_analysis.html', {
        'portfolio_stocks_trading_data': portfolio_stocks_trading_data,
        'analysis_chart_pointStart': analysis_chart_pointstart,
        'graph_json_data': graph_json_data,

        # Navbar
        'portfolio_data': portfolio_data,
        'stock_data': company_data,
        'title': stock + ' analysis'
    })
