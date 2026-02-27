"""
News URL configuration
"""
from django.urls import path
from . import views

urlpatterns = [
    path('latest/', views.NewsListView.as_view(), name='news_list'),
    path('article/<int:pk>/', views.NewsDetailView.as_view(), name='news_detail'),
    path('sentiment-summary/', views.sentiment_summary_view, name='sentiment_summary'),
    path('sentiment-trend/', views.sentiment_trend_view, name='sentiment_trend'),
    path('correlation/', views.news_correlation_view, name='news_correlation'),
    path('preferences/', views.UserNewsPreferenceView.as_view(), name='news_preferences'),
    path('bookmarks/', views.NewsBookmarkListView.as_view(), name='news_bookmarks'),
    path('bookmarks/<int:bookmark_id>/delete/', views.delete_bookmark_view, name='delete_bookmark'),
    path('live/', views.live_news_feed_view, name='news_live'),
]
