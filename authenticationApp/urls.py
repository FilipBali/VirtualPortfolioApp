from django.contrib.auth import views as auth_views
from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('home/', views.home, name='home'),

    path('accounts/', include('allauth.urls')),

    path('profile/', views.profile, name='profile'),
    path('notifications/', views.notifications, name='notifications'),

    path('login/', auth_views.LoginView.as_view(template_name='authenticationApp/login/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='authenticationApp/logout/logout.html'), name='logout'),
]


