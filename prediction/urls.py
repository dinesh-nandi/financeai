"""
Prediction URL configuration
"""
from django.urls import path
from . import views

urlpatterns = [
    path('stocks/', views.StockListView.as_view(), name='stock_list'),
    path('stocks/compare/', views.stock_compare_view, name='stock_compare'),
    path('stocks/<str:symbol>/', views.StockDetailView.as_view(), name='stock_detail'),
    path('stocks/<str:symbol>/chart/', views.stock_chart_data_view, name='stock_chart'),
    path('stocks/<str:symbol>/indicators/', views.stock_indicators_view, name='stock_indicators'),
    path('stocks/<str:symbol>/sentiment/', views.stock_sentiment_view, name='stock_sentiment'),
    path('stocks/<str:symbol>/risk/', views.stock_risk_view, name='stock_risk'),
    path('make/', views.MakePredictionView.as_view(), name='make_prediction'),
    path('history/', views.PredictionHistoryView.as_view(), name='prediction_history'),
    path('stats/', views.prediction_stats_view, name='prediction_stats'),
    path('backtest/', views.backtest_view, name='backtest'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('resolve/<int:prediction_id>/', views.resolve_prediction_view, name='resolve_prediction'),
]
