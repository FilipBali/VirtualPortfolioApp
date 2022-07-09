import json
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect

from logic.modules.lib.app_event_notification.event_notification_task import run_event_notification_task
from logic.modules.lib.messages import create_ajax_message
from logic.modules.lib.program_functions.active_panel import get_active_panel_data
from logic.modules.lib.program_functions.portfolio_details import portfolio_details_data
from logic.modules.lib.program_functions.stock_viewer import get_portfolios_data
from portfolioApp.forms import StockSourceUpdateFrom
from portfolioApp.models import Portfolio, NotificationEvent
from .forms import UserRegisterFrom, UserUpdateForm, ProfileUpdateFrom


def register(request):
    if request.method == 'POST':
        form = UserRegisterFrom(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Your account {username} has been created.')
            return redirect('login')
    else:
        form = UserRegisterFrom()
    return render(request, 'authenticationApp/register/register.html', {'form': form, 'title': 'Register'})


is_event_notifications_process_running = False


@login_required()
def notifications(request):
    if request.POST.__contains__('delete_notifications'):
        delete_notifications = request.POST['delete_notifications']

        notifications_list = delete_notifications.split(",")

        for notification_id in notifications_list:
            notification_object = NotificationEvent.objects.get(id=int(notification_id))
            notification_object.delete()

        table_data = NotificationEvent.objects.all().filter(user=request.user)
        str_table_data = []
        for row in table_data:
            row_type = ''
            if row.type == 1:
                row_type = 'Interday'
            else:
                row_type = 'Intraday'

            str_table_data.append([row.id, row.company.symbol, row_type,row.date, row.saved_price, row.on_change, row.notify])

        response = {'table_data': str_table_data}
        return JsonResponse(response, safe=False)

    if request.POST.__contains__('event_notifications_process'):
        already_running = True
        global is_event_notifications_process_running
        if is_event_notifications_process_running == False:
            run_event_notification_task()
            already_running = False

        is_event_notifications_process_running = True

        response = {'already_running': already_running}
        return JsonResponse(response, safe=False)

    table_data = NotificationEvent.objects.all().filter(user=request.user)

    company_symbol_dict = []
    for table_object in table_data:
        company_symbol_dict.append(table_object.company.symbol)

    return render(request, 'authenticationApp/notifications/notifications.html', {
        'table_data': table_data,
        'company_symbol_dict': company_symbol_dict
    })


@login_required()
def profile(request):
    active_tab = 'profile_settings'
    if request.method == 'POST':

        if request.POST.__contains__('source'):
            stock_source_form = StockSourceUpdateFrom(request.POST,
                                                      request.FILES,
                                                      instance=request.user.profile)
            if stock_source_form.is_valid():
                stock_source_form.save()

                messages.success(request, f'Your account has been updated.')
                active_tab = 'application_settings'
        else:


            user_form = UserUpdateForm(request.POST,
                                       instance=request.user)

            profile_form = ProfileUpdateFrom(request.POST,
                                             request.FILES,
                                             instance=request.user.profile)
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()

                messages.success(request, f'Your account has been updated.')

    user_form = UserUpdateForm(instance=request.user)
    profile_form = ProfileUpdateFrom(instance=request.user.profile, request=request.user)
    stock_source_form = StockSourceUpdateFrom(instance=request.user.profile, request=request.user)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'stock_source_form': stock_source_form,
        'active_tab': active_tab,
        'title': 'Profile'
    }

    return render(request, 'authenticationApp/profile/profile.html', context)


@login_required()
def home(request):
    form = UserCreationForm

    if request.POST and request.is_ajax():

        if 'show_portfolio_details' in request.POST:
            portfolio = request.POST['portfolio']
            portfolio_details = portfolio_details_data(request, portfolio)

            # if no stocks in portfolio
            if portfolio_details == 'no_stock_in_portfolio':
                messages.warning(request, 'No intruments/stocks in portfolio.')
                data = {'messages': create_ajax_message(request, messages)}
                return HttpResponse(json.dumps(data), content_type="application/json")

            if portfolio_details == 'no_bought_stock':
                return HttpResponse(json.dumps({'no_bought_stock':''}), content_type="application/json")

            stock_closed_mili = []
            for item in portfolio_details['stock_id']:
                stock_closed_mili.append(datetime.strptime((item), '%Y-%m-%d').timestamp() * 1000)
            portfolio_details['line_chart_data'] = [list(a) for a in zip(stock_closed_mili, portfolio_details['portfolio_closed'])]

            return JsonResponse(portfolio_details, safe=False)

    portfolio_count = Portfolio.objects.filter(user=request.user).count()

    if portfolio_count != 0:
        try:
            data = get_portfolios_data(request)
        except Exception as e:
            if e.args[0] == 'No IEX API VERSION or IEX TOKEN':
                messages.error(request, "Wrong or missing IEX API VERSION or IEX TOKEN.")
                return redirect('profile')

        active_panel_data = get_active_panel_data(request)

        return render(request, 'authenticationApp/home/home.html', {

            'active_panel_bool': False,
            'portofios_cards_bool': False,
            'data': data,
            'active_panel_data': active_panel_data,
            'form': form,
            'title': 'Home'
        })

    else:
        return render(request, 'authenticationApp/home/home.html', {

            'active_panel_bool': False,
            'portofios_cards_bool': False,
            'form': form,
        })
