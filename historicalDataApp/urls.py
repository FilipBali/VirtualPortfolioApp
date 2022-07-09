from django.urls import path

from . import views

urlpatterns = [
    path('', views.historical_data, name='historical_data'),
]