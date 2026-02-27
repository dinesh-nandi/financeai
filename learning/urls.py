"""
Learning URL configuration
"""
from django.urls import path
from . import views

urlpatterns = [
    path('topics/', views.TopicListView.as_view(), name='topic_list'),
    path('topics/<int:pk>/', views.TopicDetailView.as_view(), name='topic_detail'),
    path('submit-quiz/', views.SubmitQuizView.as_view(), name='submit_quiz'),
    path('progress/', views.UserProgressListView.as_view(), name='user_progress'),
    path('stats/', views.learning_stats_view, name='learning_stats'),
    path('update-progress/', views.update_progress_view, name='update_progress'),
    path('courses/', views.CourseListView.as_view(), name='course_list'),
]
