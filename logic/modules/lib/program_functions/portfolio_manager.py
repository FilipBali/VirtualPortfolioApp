import os
from datetime import datetime

import yfinance as yf
from django.db.models import F, FloatField
from django.db.models import Sum
from django.db.models.functions import Coalesce
from iexfinance.refdata import get_symbols
from iexfinance.stocks import Stock

from authenticationApp.models import Profile
from logic.modules.iex_manager.iex_download import get_iex_api_details
from portfolioApp.models import Company, OwnedStock, Portfolio


############################################################################
#                                    ADD                                   #
############################################################################

def add_instrument_portfolio(request, portfolio_name, instr, user):
    data = {}

    # If company not exist in database table (model Company)
    if not Company.objects.filter(symbol=instr).exists():

        # 1 == IEX
        # 2 == Yahoo! Finance
        data_source = Profile.objects.get(user=request.user).source
        if data_source == 1:
            iex_api_details = get_iex_api_details(request)
            os.environ['IEX_API_VERSION'] = iex_api_details['iex_api_version']
            os.environ['IEX_TOKEN'] = iex_api_details['iex_token']

            company = Stock(instr)

            name = company.get_company_name()
            symbols = get_symbols()
            region, currency, exchange = '', '', ''

            for index, row in symbols.iterrows():
                if row['symbol'] == instr:
                    region = row['region']
                    currency = row['currency']
                    exchange = row['exchange']
                    break

            new_company = Company()
            new_company.symbol = instr
            new_company.name = name
            new_company.region = region
            new_company.currency = currency
            new_company.exchange = exchange
            new_company.save()

            data = {'symbol': instr, 'name': name, 'region': region, 'currency': currency,
                    'exchange': exchange}

        elif data_source == 2:

            company = yf.Ticker(instr)

            name = company.info['shortName']
            region = company.info['market']
            currency = company.info['currency']
            exchange = company.info['exchange']

            new_company = Company()
            new_company.symbol = instr
            new_company.name = name
            new_company.region = region
            new_company.currency = currency
            new_company.exchange = exchange
            new_company.save()

            data = {'symbol': instr, 'name': name, 'region': region, 'currency': currency,
                    'exchange': exchange}

    new_portf_record = OwnedStock()
    new_portf_record.quantity = 0
    new_portf_record.price = 0
    new_portf_record.date = datetime.now()

    new_portf_record.company_id = Company.objects.get(symbol=instr).id

    # user_portfolio = Portfolio.objects.get(user_id=request.user.id, name=request.POST)
    new_portf_record.portfolio_id = Portfolio.objects.get(user=user, name=portfolio_name).id

    new_portf_record.save()

    return data


############################################################################
#                                  DELETE                                  #
############################################################################
def delete_instr_from_portf(request, instr):
    # If kupene akcie? -> False

    result_dict = {
        'done': [],
        'error': []
    }

    instr_list = instr.split(",")
    for instr_obj in instr_list:
        amout = OwnedStock.objects.all().filter(portfolio__user=request.user, company__symbol=instr_obj,
                                                portfolio__name=request.POST['url_path']).aggregate(Sum('price'))

        if amout['price__sum'] > 0.0:
            result_dict['error'].append(instr_obj)
            continue

        obj_to_del = OwnedStock.objects.all().filter(portfolio__user=request.user, company__symbol=instr_obj)
        obj_to_del.delete()
        result_dict['done'].append(instr_obj)
    return result_dict
    # TODO vymazat company? alebo nechat v db?


def delete_portfolio(request, portfolios, force=False):
    # pozriet ci existuju este akcie v nom inak false
    # pozriet ci existje take portfolio
    # delete, potom True

    # Split portfolios
    portfolios_list = portfolios.split(",")


    portfolio_data = {}

    # For each portfolio in portfolios
    for porfolio_name in portfolios_list:

        portfolio_data[porfolio_name] = {}
        portfolio_data[porfolio_name] = {'company_no_share':[], 'company_with_share': []}

        # check if porfolio exists
        if Portfolio.objects.filter(user=request.user, name=porfolio_name).exists():

            # get portfolio instance
            portfolio_object = Portfolio.objects.get(user=request.user, name=porfolio_name)

            # check if portfolio has any stocks
            porfolio_stocks_count = Company.objects.all().filter(ownedstock__portfolio__user=request.user,
                                                                 ownedstock__portfolio=portfolio_object).distinct().count()

            if force == True:
                porfolio_stocks_company = Company.objects.all().filter(ownedstock__portfolio__user=request.user,
                                                                       ownedstock__portfolio=portfolio_object).distinct()

                for company_object in porfolio_stocks_company:
                    ownedstock_in_company = OwnedStock.objects.filter(company=company_object,
                                                                      portfolio=portfolio_object)

                    for share in ownedstock_in_company:
                        share.delete()

                portfolio_object.delete()


            # porfolio has no stocks
            elif porfolio_stocks_count == 0:
                # Deleting a portfolio is safe
                portfolio_object.delete()

            # porfolio has stocks
            else:
                # get company name of stocks
                porfolio_stocks_company = Company.objects.all().filter(ownedstock__portfolio__user=request.user,
                                                                       ownedstock__portfolio=portfolio_object).distinct()

                # check if owns share in stocks
                # if yes, split it in two groups (with share, with no share)
                company_no_share= []
                company_with_share = []
                for company_object in porfolio_stocks_company:

                    buy_sum = OwnedStock.objects.filter(type=1,
                                                        company=company_object,
                                                        portfolio=portfolio_object
                                                        ).aggregate(
                        # Coalesce(Expr, Default value if Expr is None -> If no rows)
                        sum_result=Coalesce(Sum(F('price') * F('quantity'), output_field=FloatField()), 0.0)
                    )

                    sell_sum = OwnedStock.objects.filter(type=2,
                                                        company=company_object,
                                                        portfolio=portfolio_object
                                                        ).aggregate(
                        # Coalesce(Expr, Default value if Expr is None -> If no rows)
                        sum_result=Coalesce(Sum(F('price') * F('quantity'), output_field=FloatField()), 0.0)
                    )

                    actual_balance = buy_sum['sum_result'] - sell_sum['sum_result']

                    if actual_balance == 0:
                        company_no_share.append(company_object.symbol)
                    else:
                        company_with_share.append(company_object.symbol)

                portfolio_data[porfolio_name]['company_no_share'] = company_no_share
                portfolio_data[porfolio_name]['company_with_share'] = company_with_share


                # if len(company_with_share) == 0:
                #     # offer force delete
                #     return {'force': company_no_share}
                #
                # else:
                #     # error (plese sell your share and then delete a portfolio)
                #     ...
        else:
            # TODO ERROR, portfolio not exists!
            ...

    return portfolio_data

######################################
