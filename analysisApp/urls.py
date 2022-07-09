from django.urls import path

from . import views

urlpatterns = [
    path('<str:portfolio>/analysis/', views.portfolio_analysis, name='portfolio_analysis'),
    path('<str:portfolio>/<str:stock>/analysis/', views.instrument_analysis, name='instrument_analysis')
]