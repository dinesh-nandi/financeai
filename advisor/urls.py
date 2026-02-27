"""
Advisor URL configuration
"""
from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.chat_view, name='advisor_chat'),
    path('history/', views.chat_history_view, name='advisor_history'),
    path('sessions/', views.ChatSessionListView.as_view(), name='advisor_sessions'),
    path('sessions/<int:pk>/', views.ChatSessionDetailView.as_view(), name='advisor_session_detail'),
    path('suggested-prompts/', views.suggested_prompts_view, name='advisor_prompts'),
    path('recommendations/', views.recommendations_view, name='advisor_recommendations'),
    path('stats/', views.advisor_stats_view, name='advisor_stats'),
]
