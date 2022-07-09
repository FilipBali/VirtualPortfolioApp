from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now


class Portfolio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    note = models.CharField(max_length=255)

    class Meta:
        unique_together = (('user', 'name'),)

    @property
    def numOwnedStock(self):
        return len(self.ownedstock_set.filter(quantity=0, price=0))

    def __str__(self):
        return f'{self.user.username} Profile'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class Company(models.Model):
    symbol = models.CharField(max_length=255, default='')
    name = models.CharField(max_length=255, default='')
    region = models.CharField(max_length=255, default='')
    currency = models.CharField(max_length=255, default='')
    exchange = models.CharField(max_length=255, default='')


class OwnedStock(models.Model):
    portfolio = models.ForeignKey(Portfolio,on_delete=models.CASCADE)
    company = models.ForeignKey(Company ,on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.FloatField()
    date = models.DateTimeField()
    type = models.IntegerField(choices=[
        (1, 'Buy'),
        (2, 'Sell'),
    ], default=1)


    @property
    def companyName(self):
        return self.company.symbol

    @property
    def summation(self):
        return self.price * self.quantity

    @property
    def isoDate_without_time(self):
        return self.date.strftime('%Y-%m-%d')

class News(models.Model):
    article_headline = models.CharField(max_length=2500)
    article_text = models.CharField(max_length=5000)
    source = models.CharField(max_length=5000, blank=True)

    url = models.CharField(max_length=5000, default="www.google.com")
    datetime = models.DateField(default=now)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)


class NotificationEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, default=0)
    saved_price = models.FloatField(default=0)
    on_change = models.FloatField(default=0)
    date = models.DateTimeField(null=False, blank=False, auto_now=True)
    type = models.IntegerField(choices=[
        (1, 'Interday'),
        (2, 'Intraday'),
    ], default=1)
    notify = models.IntegerField(choices=[
        (1, 'At a price change equal/above/below'),
        (2, 'Percentage increase current price'),
        (3, 'Percentage decrease current price'),
    ], default=1)
