"""
Users URL configuration
"""
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path('stats/', views.user_stats_view, name='user_stats'),
    path('activities/', views.UserActivityListView.as_view(), name='activities'),
    path('wallet/nonce/', views.wallet_nonce_view, name='wallet_nonce'),
    path('wallet/verify/', views.wallet_verify_view, name='wallet_verify'),
]
