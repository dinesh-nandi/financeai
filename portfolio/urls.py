"""
Portfolio URL configuration
"""
from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.PortfolioListView.as_view(), name='portfolio_list'),
    path('add/', views.AddPortfolioView.as_view(), name='portfolio_add'),
    path('remove/<int:pk>/', views.RemovePortfolioView.as_view(), name='portfolio_remove'),
    path('summary/', views.portfolio_summary_view, name='portfolio_summary'),
    path('analytics/', views.portfolio_analytics_view, name='portfolio_analytics'),
    path('allocation/', views.portfolio_allocation_view, name='portfolio_allocation'),
    path('performance/', views.portfolio_performance_view, name='portfolio_performance'),
    path('transactions/', views.portfolio_transactions_view, name='portfolio_transactions'),
    path('export/', views.export_portfolio_view, name='portfolio_export'),
]
