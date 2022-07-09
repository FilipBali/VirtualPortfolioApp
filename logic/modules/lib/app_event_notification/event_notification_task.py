import datetime
import threading

from logic.modules.lib.app_event_notification.email_manager import send_email
from logic.modules.stock_data_controller.stock_data_controller import get_data
from portfolioApp.models import NotificationEvent


def run_event_notification_task():

    # starts every 60 seconds
    threading.Timer(60.0, run_event_notification_task).start()


    # get all records from notificationevent table
    # get all instrument symbols from record
    # split to interday/intraday categories
    interday_records = NotificationEvent.objects.filter(type=1).all()
    intraday_records = NotificationEvent.objects.filter(type=2).all()

    # gel last prices (interday/intraday) for all instrument in that category
    interday_dict = {}
    intraday_dict = {}

    ####################################################################################################################
    #                                                    INTERDAY
    ####################################################################################################################
    for record in interday_records:
        if not record.company.symbol in interday_dict:
            actual_time = datetime.datetime.now()
            actual_time = str(actual_time)[:10]
            instrument_data = get_data(request=False,
                                       instrument=record.company.symbol,
                                       startdate=actual_time,
                                       enddate=actual_time,
                                       only_closed=True,
                                       notificiation_event=True)

            if instrument_data.size != 0:
                instrument_price = instrument_data[0]
                interday_dict[record.company.symbol] = instrument_price

    ####################################################################################################################
    #                                                    INTRADAY
    ####################################################################################################################


    for record in intraday_records:
        if not record.company.symbol in intraday_dict:
            actual_time = datetime.datetime.now()
            actual_time = str(actual_time)[:10]
            instrument_data = get_data(request=False,
                                       instrument=record.company.symbol,
                                       day=actual_time,
                                       intraday=True,
                                       notificiation_event=True)

            if instrument_data.size != 0:
                instrument_price = instrument_data['Close'][-1]
                intraday_dict[record.company.symbol] = instrument_price

    # go through all records and find out if need to be notified
    # dont forget on different types

    ####################################################################################################################
    #                                                    INTERDAY
    ####################################################################################################################
    for record in interday_records:
        record_saved_price = record.saved_price
        record_on_change = record.on_change
        record_notify = record.notify
        actual_instrument_price = interday_dict[record.company.symbol]

        # At a price change equal/above/below
        if record_notify == 1:
            # User wants to be notified when is equal or bellow
            if record_saved_price > record_on_change:
                if actual_instrument_price <= record_on_change:
                    #notify
                    email_recipient = record.user.email
                    email_subject = '[ ' + record.company.symbol + ' ]' + ' INTERDAY PRICE CHANGE'
                    email_message = record.company.symbol + ' actual price ' + str(actual_instrument_price) + ' ' \
                                    + str(record.company.currency) + '\n' \
                                    'Price alert was set at ' + str(record_on_change) +'\n' \
                                    'The price at that time was ' + str(record_saved_price) + ' ' \
                                    + str(record.company.currency)
                    ret = send_email(email_recipient, email_subject, email_message)
                    record.delete()

            # User wants to be notified when is equal or above
            elif record_saved_price < record_on_change:
                if actual_instrument_price >= record_on_change:
                    #notify
                    email_recipient = record.user.email
                    email_subject = '[ ' + record.company.symbol + ' ]' + ' INTERDAY PRICE CHANGE'
                    email_message = record.company.symbol + ' actual price ' + str(actual_instrument_price) + ' ' \
                                    + str(record.company.currency) + '\n' \
                                    'Price alert was set at ' + str(record_on_change) +'\n' \
                                    'The price at that time was ' + str(record_saved_price) + ' ' \
                                    + str(record.company.currency)
                    ret = send_email(email_recipient, email_subject, email_message)
                    record.delete()

        # Percentage increase current price
        elif record_notify == 2:
            increase = (((actual_instrument_price-record_saved_price)/record_saved_price) * 100)
            if increase >= record_on_change:
                # notify
                email_recipient = record.user.email
                email_subject = '[ ' + record.company.symbol + ' ]' + ' INTERDAY PRICE CHANGE'
                email_message = record.company.symbol + ' actual price ' + str(actual_instrument_price) + ' ' \
                                + str(record.company.currency) + '\n' \
                                'Price alert was set at ' + str(record_on_change) + ' % increase \n' \
                                'The price at that time was ' + str(record_saved_price) + ' ' \
                                + str(record.company.currency)
                ret = send_email(email_recipient, email_subject, email_message)
                record.delete()

        # Percentage decrease current price
        elif record_notify == 3:
            decrease = (((record_saved_price - actual_instrument_price) / actual_instrument_price) * 100)
            if decrease >= record_on_change:
                # notify
                email_recipient = record.user.email
                email_subject = '[ ' + record.company.symbol + ' ]' + ' INTERDAY PRICE CHANGE'
                email_message = record.company.symbol + ' actual price ' + str(actual_instrument_price) + ' ' \
                                + str(record.company.currency) + '\n' \
                                'Price alert was set at ' + str(record_on_change) + ' % decrease \n' \
                                'The price at that time was ' + str(record_saved_price) + ' ' \
                                + str(record.company.currency)
                ret = send_email(email_recipient, email_subject, email_message)
                record.delete()

    ####################################################################################################################
    #                                                    INTRADAY
    ####################################################################################################################
    for record in intraday_records:
        record_saved_price = record.saved_price
        record_on_change = record.on_change
        record_notify = record.notify
        actual_instrument_price = intraday_dict[record.company.symbol]

        # At a price change equal/above/below
        if record_notify == 1:
            # User wants to be notified when is equal or bellow
            if record_saved_price > record_on_change:
                if actual_instrument_price <= record_on_change:
                    #notify
                    email_recipient = record.user.email
                    email_subject = '[ ' + record.company.symbol + ' ]' + ' INTRADAY PRICE CHANGE'
                    email_message = record.company.symbol + ' actual price ' + str(actual_instrument_price) + ' ' \
                                    + str(record.company.currency) + '\n' \
                                    'Price alert was set at ' + str(record_on_change) +'\n' \
                                    'The price at that time was ' + str(record_saved_price) + ' ' \
                                    + str(record.company.currency)
                    ret = send_email(email_recipient, email_subject, email_message)
                    record.delete()

            # User wants to be notified when is equal or above
            elif record_saved_price < record_on_change:
                if actual_instrument_price >= record_on_change:
                    #notify
                    email_recipient = record.user.email
                    email_subject = '[ ' + record.company.symbol + ' ]' + ' INTRADAY PRICE CHANGE'
                    email_message = record.company.symbol + ' actual price ' + str(actual_instrument_price) + ' ' \
                                    + str(record.company.currency) + '\n' \
                                    'Price alert was set at ' + str(record_on_change) +'\n' \
                                    'The price at that time was ' + str(record_saved_price) + ' ' \
                                    + str(record.company.currency)
                    ret = send_email(email_recipient, email_subject, email_message)
                    record.delete()

        # Percentage increase current price
        elif record_notify == 2:
            increase = (((actual_instrument_price-record_saved_price)/record_saved_price) * 100)
            if increase >= record_on_change:
                # notify
                email_recipient = record.user.email
                email_subject = '[ ' + record.company.symbol + ' ]' + ' INTRADAY PRICE CHANGE'
                email_message = record.company.symbol + ' actual price ' + str(actual_instrument_price) + ' ' \
                                + str(record.company.currency) + '\n' \
                                'Price alert was set at ' + str(record_on_change) + ' % increase \n' \
                                'The price at that time was ' + str(record_saved_price) + ' ' \
                                + str(record.company.currency)
                ret = send_email(email_recipient, email_subject, email_message)
                record.delete()
        # Percentage decrease current price
        elif record_notify == 3:
            decrease = (((record_saved_price - actual_instrument_price) / actual_instrument_price) * 100)
            if decrease >= record_on_change:
                # notify
                email_recipient = record.user.email
                email_subject = '[ ' + record.company.symbol + ' ]' + ' INTRADAY PRICE CHANGE'
                email_message = record.company.symbol + ' actual price ' + str(actual_instrument_price) + ' ' \
                                + str(record.company.currency) + '\n' \
                                'Price alert was set at ' + str(record_on_change) + ' % decrease \n' \
                                'The price at that time was ' + str(record_saved_price) + ' ' \
                                + str(record.company.currency)
                ret = send_email(email_recipient, email_subject, email_message)
                record.delete()