"""
News admin configuration
"""
from django.contrib import admin
from .models import NewsArticle, SentimentAnalysis, NewsSource, UserNewsPreference, NewsBookmark


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'source', 'sentiment', 'impact_level', 'category', 'published_at']
    list_filter = ['sentiment', 'impact_level', 'category', 'source']
    search_fields = ['title', 'summary']
    date_hierarchy = 'published_at'
    filter_horizontal = ['related_stocks']


@admin.register(SentimentAnalysis)
class SentimentAnalysisAdmin(admin.ModelAdmin):
    list_display = ['date', 'overall_sentiment', 'total_articles', 'positive_percentage']
    list_filter = ['overall_sentiment']
    date_hierarchy = 'date'


@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'reliability_score', 'last_fetch']
    list_filter = ['is_active']


@admin.register(UserNewsPreference)
class UserNewsPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_notifications', 'push_notifications']


@admin.register(NewsBookmark)
class NewsBookmarkAdmin(admin.ModelAdmin):
    list_display = ['user', 'article', 'created_at']
    search_fields = ['user__username', 'article__title']
