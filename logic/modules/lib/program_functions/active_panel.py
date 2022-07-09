from datetime import datetime, timedelta

from logic.modules.stock_data_controller.stock_data_controller import get_data
from portfolioApp.models import Company


def get_active_panel_data(request):
    data = []
    temp_data = []


    all_user_companies = Company.objects.filter(ownedstock__portfolio__user=request.user,
                                                ownedstock__price=0,
                                                ownedstock__quantity=0
                                                ).all().distinct()

    for company in all_user_companies:
        end_date = datetime.today()
        start_date = end_date - timedelta(days=7)

        # Perform string cut
        end_date = str(end_date)[:10]
        start_date = str(start_date)[:10]

        instruments_data = get_data(request,
                                    instrument=company.symbol,
                                    startdate=start_date,
                                    enddate=end_date,
                                    only_closed=True)

        # TODO ak instruments_data nema dva zaznamy?
        last_two_days = instruments_data[-2:]
        if last_two_days[0] != 0.0:
            percentage_diff = (((last_two_days[1] - last_two_days[0]) / last_two_days[0]) * 100)
        else:
            percentage_diff = last_two_days[1]

        # Status description
        # -1 = deincrese %
        #  0 = no change
        #  1 = increse %
        #
        status = 0
        if percentage_diff > 0:
            status = 1
        elif percentage_diff < 0:
            status = -1


        temp_data.append([company.symbol, round(percentage_diff, 2), round(last_two_days[1], 3), status])

        # Because active bar on homepage has 6 cards
        if len(temp_data) == 6:
            data.append(temp_data)
            temp_data = []

    # save last 6 or less iterations
    data.append(temp_data)

    return data
