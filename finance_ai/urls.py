"""
FinanceAI URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # JWT Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API Routes
    path('api/auth/', include('users.urls')),
    path('api/dashboard/', include('learning.urls_dashboard')),
    path('api/learning/', include('learning.urls')),
    path('api/prediction/', include('prediction.urls')),
    path('api/news/', include('news.urls')),
    path('api/portfolio/', include('portfolio.urls')),
    path('api/advisor/', include('advisor.urls')),
    
    # Frontend Pages
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path('register/', TemplateView.as_view(template_name='register.html'), name='register'),
    path('dashboard/', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    path('learning/', TemplateView.as_view(template_name='learning.html'), name='learning'),
    path('prediction/', TemplateView.as_view(template_name='prediction.html'), name='prediction'),
    path('news/', TemplateView.as_view(template_name='news.html'), name='news'),
    path('portfolio/', TemplateView.as_view(template_name='portfolio.html'), name='portfolio'),
    path('advisor/', TemplateView.as_view(template_name='advisor.html'), name='advisor'),
    path('community/', TemplateView.as_view(template_name='community.html'), name='community'),
]
