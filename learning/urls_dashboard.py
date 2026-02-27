"""
Dashboard URL configuration for FinanceAI
"""
from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Avg
from portfolio.models import Portfolio
from prediction.models import Prediction
from news.models import NewsArticle
from users.models import UserProfile


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    """Get dashboard summary data"""
    user = request.user
    
    # Portfolio value
    portfolio_items = Portfolio.objects.filter(user=user)
    total_portfolio_value = sum(
        item.shares * item.current_price 
        for item in portfolio_items
    )
    
    # Risk score from profile
    try:
        profile = user.profile
        risk_score = 68  # Default moderate risk
        if profile.risk_appetite == 'conservative':
            risk_score = 35
        elif profile.risk_appetite == 'aggressive':
            risk_score = 85
    except:
        risk_score = 68
    
    # Prediction accuracy
    predictions = Prediction.objects.filter(user=user)
    total_predictions = predictions.count()
    correct_predictions = predictions.filter(is_correct=True).count()
    prediction_accuracy = round(
        (correct_predictions / total_predictions) * 100, 2
    ) if total_predictions > 0 else 0
    
    # News sentiment
    recent_news = NewsArticle.objects.order_by('-published_at')[:50]
    if recent_news:
        avg_sentiment = sum(n.sentiment_score for n in recent_news) / len(recent_news)
        sentiment_label = 'Bullish' if avg_sentiment > 0.2 else 'Bearish' if avg_sentiment < -0.2 else 'Neutral'
    else:
        avg_sentiment = 0
        sentiment_label = 'Neutral'
    
    return Response({
        'status': 'success',
        'data': {
            'total_portfolio_value': round(total_portfolio_value, 2),
            'portfolio_change': 5.23,
            'portfolio_change_value': 6182.00,
            'risk_score': risk_score,
            'risk_label': 'Moderate Risk',
            'prediction_accuracy': prediction_accuracy,
            'prediction_change': 3,
            'sentiment_score': round(avg_sentiment, 2),
            'sentiment_label': sentiment_label,
            'sentiment_change': 12
        }
    })


urlpatterns = [
    path('summary/', dashboard_summary, name='dashboard_summary'),
]
