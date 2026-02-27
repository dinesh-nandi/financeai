"""
Prediction admin configuration
"""
from django.contrib import admin
from .models import Stock, Prediction, StockPriceHistory, AIPredictionModel, MarketIndicator


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'name', 'current_price', 'price_change', 'sector', 'last_updated']
    list_filter = ['sector']
    search_fields = ['symbol', 'name']
    readonly_fields = ['last_updated']


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ['user', 'stock', 'user_prediction', 'ai_prediction', 'is_correct', 'created_at']
    list_filter = ['user_prediction', 'ai_prediction', 'is_correct']
    search_fields = ['user__username', 'stock__symbol']
    readonly_fields = ['created_at']


@admin.register(StockPriceHistory)
class StockPriceHistoryAdmin(admin.ModelAdmin):
    list_display = ['stock', 'date', 'close_price', 'volume']
    list_filter = ['stock']
    search_fields = ['stock__symbol']
    date_hierarchy = 'date'


@admin.register(AIPredictionModel)
class AIPredictionModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'version', 'accuracy_percentage', 'is_active', 'created_at']
    list_filter = ['is_active']


@admin.register(MarketIndicator)
class MarketIndicatorAdmin(admin.ModelAdmin):
    list_display = ['stock', 'indicator_type', 'value', 'calculated_at']
    list_filter = ['indicator_type']
    search_fields = ['stock__symbol']
