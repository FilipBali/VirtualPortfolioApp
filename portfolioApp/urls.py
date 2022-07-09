from django.urls import path

from . import views

urlpatterns = [

    path('', views.portfolio_list, name='portfolio_list'),
    path('<str:portfolio>/', views.portfolio, name='portfolio'),

    path('<str:portfolio>/<str:stock>/', views.instrument, name='instrument'),

    path('<str:portfolio>/<str:stock>/preview/', views.instrument_preview, name='instrument_preview'),
]