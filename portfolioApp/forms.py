from django import forms
from django.forms import Widget
from django.utils.safestring import mark_safe

from authenticationApp.models import Profile
from .models import Portfolio, OwnedStock, NotificationEvent


class StockSourceUpdateFrom(forms.ModelForm):
    # iex_api_version = forms.TextInput(widget=PrependWidget_IEXapiVersion(base_widget=forms.TextInput,
    #                                                                      data='IEX Finance API version'))


    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(StockSourceUpdateFrom, self).__init__(*args, **kwargs)
        source = forms.ModelChoiceField(
            queryset=Profile.objects.values_list('source', flat=True)
        )
        self.fields['source'].label = ""

    class Meta:
        model = Profile
        fields = ['source', 'iex_api_version', 'iex_token']


class PortfolioForm(forms.Form):
    name = forms.CharField(min_length=1, max_length=50)
    note = forms.CharField(min_length=1, max_length=100)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(PortfolioForm, self).__init__(*args, **kwargs)


    class Meta:
        model = Portfolio
        fields = ['name', 'note']


class PrependWidget_Date(Widget):
    """ Widget that prepend boostrap-style span with data to specified base widget """

    def __init__(self, base_widget, data, *args, **kwargs):
        u"""Initialise widget and get base instance"""
        super(PrependWidget_Date, self).__init__(*args, **kwargs)
        self.base_widget = base_widget(*args, **kwargs)
        self.data = data

    def render(self, name, value, attrs=None, renderer=None):
        u"""Render base widget and add bootstrap spans"""
        field = self.base_widget.render(name, value, attrs)
        return mark_safe((
            u'<div class="input-group mb-3">'
            u'  <div class="input-group-prepend">'
            u'    <span class="input-group-text" id="date-addon">%(data)s</span>'
            u'  </div>'
            # u'  <input type="text" class="form-control" placeholder="Username" aria-label="Username" aria-describedby="basic-addon1">'

            # u'  <input type="text" name="date" class="datetimeinput form-control " required="" id="id_date">' # original
            u'  <input type="text" placeholder="Required field" aria-label="date" class="datetimeinput form-control" aria-describedby="date-addon" required="" id="id_date">'
            u'</div>'
        ) % {'field': field, 'data': self.data})


class PrependWidget_Price(Widget):
    """ Widget that prepend boostrap-style span with data to specified base widget """

    def __init__(self, base_widget, data, *args, **kwargs):
        u"""Initialise widget and get base instance"""
        super(PrependWidget_Price, self).__init__(*args, **kwargs)
        self.base_widget = base_widget(*args, **kwargs)
        self.data = data

    def render(self, name, value, attrs=None, renderer=None):
        u"""Render base widget and add bootstrap spans"""
        field = self.base_widget.render(name, value, attrs)
        return mark_safe((
            u'<div class="input-group mb-3">'
            u'  <div class="input-group-prepend">'
            u'    <span class="input-group-text" id="price-addon">%(data)s</span>'
            u'  </div>'
            # u'  <input type="text" class="form-control" placeholder="Username" aria-label="Username" aria-describedby="basic-addon1">'
            u'  <input type="number" name="price" step="any" placeholder="Required field" aria-label="Price" class="numberinput form-control" aria-describedby="price-addon" required="" id="id_price">'
            u'</div>'
        ) % {'field': field, 'data': self.data})


class PrependWidget_Quality(Widget):
    """ Widget that prepend boostrap-style span with data to specified base widget """

    def __init__(self, base_widget, data, *args, **kwargs):
        u"""Initialise widget and get base instance"""
        super(PrependWidget_Quality, self).__init__(*args, **kwargs)
        self.base_widget = base_widget(*args, **kwargs)
        self.data = data

    def render(self, name, value, attrs=None, renderer=None):
        u"""Render base widget and add bootstrap spans"""
        field = self.base_widget.render(name, value, attrs)
        return mark_safe((
            u'<div class="input-group mb-3">'
            u'  <div class="input-group-prepend">'
            u'    <span class="input-group-text" id="quantity-addon">%(data)s</span>'
            u'  </div>'
            # u'  <input type="text" class="form-control" placeholder="Username" aria-label="Username" aria-describedby="basic-addon1">'
            u'  <input type="number" name="quantity" step="any" placeholder="Required field" aria-label="quantity" class="numberinput form-control" aria-describedby="quantity-addon" required="" id="id_quantity">'
            u'</div>'
        ) % {'field': field, 'data': self.data})

class BuySellStockForm(forms.ModelForm):

    date = forms.DateField(label='', widget=PrependWidget_Date(base_widget=forms.TextInput, data='Date'))
    price = forms.IntegerField(label='', widget=PrependWidget_Price(base_widget=forms.TextInput, data='Price'))
    quantity = forms.IntegerField(label='', widget=PrependWidget_Quality(base_widget=forms.TextInput, data='Quantity'))

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(BuySellStockForm, self).__init__(*args, **kwargs)
        self.fields['type'].label = ""

    class Meta:
        model = OwnedStock
        fields = ['type', 'date', 'price', 'quantity']


class NotificationEventForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(NotificationEventForm, self).__init__(*args, **kwargs)

    class Meta:
        model = NotificationEvent
        fields = ['on_change','type', 'notify']