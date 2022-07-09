import time

from django import template

from portfolioApp.models import NotificationEvent

register = template.Library()


def print_timestamp(timestamp):
    return time.strftime('%Y-%m-%d'.format(timestamp%1000), time.gmtime(timestamp/1000.0))

def print_timestamp_analysis(timestamp):
    return str(timestamp.year) + '-' + str(timestamp.month) +'-' + str(timestamp.day)

def print_timestamp_notifications(timestamp):
    return str(timestamp.year) + '-' + str(timestamp.month) +'-' + str(timestamp.day)

def print_notification_text(type):
    if type == 1:
        return 'At a price change equal/above/below'
    elif type == 2:
        return 'Percentage increase current price'
    elif type == 3:
        return 'Percentage decrease current price'

def print_symbol_notifications(notification_id):
    object = NotificationEvent.objects.get(id=notification_id)
    symbol = str(object.company.symbol)
    return symbol

def print_type_notifications(notification_type):
    if notification_type == 1:
        return 'Interday'
    elif notification_type == 2:
        return 'Intraday'

register.filter(print_timestamp)
register.filter(print_timestamp_analysis)
register.filter(print_timestamp_notifications)
register.filter(print_notification_text)
register.filter(print_symbol_notifications)
register.filter(print_type_notifications)