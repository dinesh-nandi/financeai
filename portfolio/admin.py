"""
Portfolio admin configuration
"""
from django.contrib import admin
from .models import Portfolio, PortfolioTransaction, PortfolioAnalytics, Watchlist, PortfolioHistory


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['user', 'stock', 'shares', 'average_buy_price', 'current_value', 'gain_loss']
    list_filter = ['stock__sector']
    search_fields = ['user__username', 'stock__symbol']


@admin.register(PortfolioTransaction)
class PortfolioTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'stock', 'transaction_type', 'shares', 'price_per_share', 'transaction_date']
    list_filter = ['transaction_type']
    search_fields = ['user__username', 'stock__symbol']
    date_hierarchy = 'transaction_date'


@admin.register(PortfolioAnalytics)
class PortfolioAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['user', 'risk_score', 'diversification_score', 'calculated_at']
    search_fields = ['user__username']


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'created_at']
    search_fields = ['user__username', 'name']
    filter_horizontal = ['stocks']


@admin.register(PortfolioHistory)
class PortfolioHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'total_value', 'day_gain_loss']
    search_fields = ['user__username']
    date_hierarchy = 'date'
