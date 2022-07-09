from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from authenticationApp.models import Profile
from logic.modules.lib.messages import create_ajax_message
from logic.modules.stock_data_controller.stock_data_controller import get_data
from logic.modules.yahoo_finance_manager.yahoo_downloader import yahoo_instrument_details
from portfolioApp.models import Company


@login_required()
def historical_data(request, *args, **kwargs):
    data = {}

    ####################################################################################################################
    # If POST request with AJAX
    ####################################################################################################################
    if request.method == 'POST' and request.is_ajax():
        time_data, price_data = get_data(request,
                                         request.POST['selected_stock'],
                                         datetime.strptime(request.POST['datepicker_start'],
                                                           '%Y-%m-%d'),
                                         datetime.strptime(request.POST['datepicker_end'],
                                                           '%Y-%m-%d'),
                                         historical_data=True)
        if len(price_data) == 1:
            if price_data[0][0] == 0:
                messages.warning(request, 'No data from stock data source.')
                data['messages'] = create_ajax_message(request, messages)
                data['error'] = ''
                return JsonResponse(data, safe=False)

        data = {}
        if Profile.objects.get(user=request.user).source == 1:
            company_data = Company.objects.get(symbol=request.POST['selected_stock'])
            data['currency'] = company_data.currency
        else:
            data = yahoo_instrument_details(data, request.POST['selected_stock'])


        str_price_data = []
        for price_row in price_data:
            str_price_data.append([str(i) for i in price_row])
        data['str_price_data'] = str_price_data
        return JsonResponse(data, safe=False)

    ####################################################################################################################
    # If no AJAX request
    # Then execute main part
    ####################################################################################################################

    # get all instrument of user (in all portfolios)
    data['user_company'] = Company.objects.values_list('symbol', flat=True) \
        .filter(ownedstock__portfolio__user=request.user).distinct()

    return render(request, 'historicalDataApp/historical_data/historical_data.html',
                  {'user_company': data['user_company'],
                  'title': 'Historical data'})