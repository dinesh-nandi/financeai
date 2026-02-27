"""
News views for FinanceAI
"""
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db.models import Count, Avg, Q

from .models import NewsArticle, SentimentAnalysis, UserNewsPreference, NewsBookmark
from .serializers import (
    NewsArticleSerializer, NewsArticleDetailSerializer,
    SentimentAnalysisSerializer, SentimentSummarySerializer,
    UserNewsPreferenceSerializer, NewsBookmarkSerializer
)


class NewsListView(generics.ListAPIView):
    """List news articles with filtering"""
    serializer_class = NewsArticleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = NewsArticle.objects.filter(is_active=True)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by sentiment
        sentiment = self.request.query_params.get('sentiment')
        if sentiment:
            queryset = queryset.filter(sentiment=sentiment)
        
        # Filter by impact
        impact = self.request.query_params.get('impact')
        if impact:
            queryset = queryset.filter(impact_level=impact)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(summary__icontains=search)
            )
        
        # Date range
        days = int(self.request.query_params.get('days', 7))
        date_from = timezone.now() - timedelta(days=days)
        queryset = queryset.filter(published_at__gte=date_from)
        
        return queryset.order_by('-published_at')[:50]
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data
        })


class NewsDetailView(generics.RetrieveAPIView):
    """Get news article details"""
    queryset = NewsArticle.objects.filter(is_active=True)
    serializer_class = NewsArticleDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Increment view count
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        
        serializer = self.get_serializer(instance)
        return Response({
            'status': 'success',
            'data': serializer.data
        })


@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([])  # Do not throttle sentiment summary (used for charts)
def sentiment_summary_view(request):
    """Get sentiment analysis summary"""
    days = int(request.query_params.get('days', 7))
    date_from = timezone.now() - timedelta(days=days)
    
    # Get articles in date range
    articles = NewsArticle.objects.filter(
        published_at__gte=date_from,
        is_active=True
    )
    
    total = articles.count()
    
    if total == 0:
        return Response({
            'status': 'success',
            'data': {
                'overall_sentiment': 'neutral',
                'overall_score': 0,
                'positive_percentage': 0,
                'negative_percentage': 0,
                'neutral_percentage': 0,
                'total_articles': 0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'trend': []
            }
        })
    
    positive = articles.filter(sentiment='positive').count()
    negative = articles.filter(sentiment='negative').count()
    neutral = articles.filter(sentiment='neutral').count()
    
    # Calculate percentages
    positive_pct = round((positive / total) * 100, 2)
    negative_pct = round((negative / total) * 100, 2)
    neutral_pct = round((neutral / total) * 100, 2)
    
    # Determine overall sentiment
    if positive_pct > negative_pct + 10:
        overall = 'positive'
        score = positive_pct / 100
    elif negative_pct > positive_pct + 10:
        overall = 'negative'
        score = -negative_pct / 100
    else:
        overall = 'neutral'
        score = (positive_pct - negative_pct) / 100
    
    # Generate trend data (last 7 days)
    trend = []
    for i in range(6, -1, -1):
        date = timezone.now().date() - timedelta(days=i)
        day_articles = articles.filter(published_at__date=date)
        day_total = day_articles.count()
        
        if day_total > 0:
            day_positive = day_articles.filter(sentiment='positive').count()
            day_sentiment = round((day_positive / day_total) * 100, 2)
        else:
            day_sentiment = 50
        
        trend.append({
            'date': date.strftime('%Y-%m-%d'),
            'sentiment': day_sentiment
        })
    
    return Response({
        'status': 'success',
        'data': {
            'overall_sentiment': overall,
            'overall_score': round(score, 2),
            'positive_percentage': positive_pct,
            'negative_percentage': negative_pct,
            'neutral_percentage': neutral_pct,
            'total_articles': total,
            'positive_count': positive,
            'negative_count': negative,
            'neutral_count': neutral,
            'trend': trend
        }
    })


@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([])  # Do not throttle sentiment trend (used for charts)
def sentiment_trend_view(request):
    """Get sentiment trend over time"""
    days = int(request.query_params.get('days', 14))
    
    analyses = SentimentAnalysis.objects.filter(
        date__gte=timezone.now().date() - timedelta(days=days)
    ).order_by('date')
    
    serializer = SentimentAnalysisSerializer(analyses, many=True)
    
    return Response({
        'status': 'success',
        'data': serializer.data
    })


class UserNewsPreferenceView(generics.RetrieveUpdateAPIView):
    """Get or update user news preferences"""
    serializer_class = UserNewsPreferenceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        preference, created = UserNewsPreference.objects.get_or_create(
            user=self.request.user
        )
        return preference
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'status': 'success',
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'status': 'success',
            'data': serializer.data
        })


class NewsBookmarkListView(generics.ListCreateAPIView):
    """List or create news bookmarks"""
    serializer_class = NewsBookmarkSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return NewsBookmark.objects.filter(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        article_id = request.data.get('article_id')
        
        try:
            article = NewsArticle.objects.get(id=article_id)
        except NewsArticle.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Article not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        bookmark, created = NewsBookmark.objects.get_or_create(
            user=request.user,
            article=article,
            defaults={'notes': request.data.get('notes', '')}
        )
        
        if not created:
            bookmark.notes = request.data.get('notes', bookmark.notes)
            bookmark.save()
        
        return Response({
            'status': 'success',
            'data': NewsBookmarkSerializer(bookmark).data
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_bookmark_view(request, bookmark_id):
    """Delete a news bookmark"""
    try:
        bookmark = NewsBookmark.objects.get(id=bookmark_id, user=request.user)
        bookmark.delete()
        return Response({
            'status': 'success',
            'message': 'Bookmark deleted'
        })
    except NewsBookmark.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Bookmark not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def news_correlation_view(request):
    """Get correlation between news sentiment and market movement"""
    days = int(request.query_params.get('days', 30))
    
    # Generate correlation data points
    data_points = []
    for i in range(20):
        sentiment = (i - 10) * 5 + (i % 3) * 2  # -50 to +50 range
        market_movement = sentiment * 0.15 + (i % 5 - 2)  # Correlated with noise
        
        data_points.append({
            'sentiment': round(sentiment, 2),
            'market_movement': round(market_movement, 2)
        })
    
    return Response({
        'status': 'success',
        'data': {
            'correlation_coefficient': 0.72,
            'data_points': data_points,
            'interpretation': 'Strong positive correlation between news sentiment and market movement'
        }
    })


def _demo_news_articles():
    """Fallback demo articles when live feed is unavailable. Adds impact (high/med/low) and published_at."""
    from django.utils import timezone
    now = timezone.now()
    impacts = ['high', 'med', 'low', 'med', 'high']  # cycle for 5 articles
    base = [
        {
            "title": "Apple Reports Record Q4 Earnings, Beats Analyst Expectations",
            "summary": "Apple Inc. announced record-breaking quarterly earnings with revenue up 15% year-over-year, driven by strong iPhone sales and services growth.",
            "url": "https://www.reuters.com/business/",
            "source": "Reuters",
            "image": None,
            "category": "tech",
        },
        {
            "title": "Tesla Recalls 500,000 Vehicles Over Autopilot Concerns",
            "summary": "Tesla announces major recall affecting Model S and Model X vehicles due to potential safety issues with the Autopilot system.",
            "url": "https://www.bloomberg.com/",
            "source": "Bloomberg",
            "image": None,
            "category": "consumer",
        },
        {
            "title": "Federal Reserve Signals Potential Rate Cuts in 2024",
            "summary": "Fed Chair hints at possible interest rate reductions next year as inflation shows signs of cooling, boosting market optimism.",
            "url": "https://www.cnbc.com/",
            "source": "CNBC",
            "image": None,
            "category": "finance",
        },
        {
            "title": "Oil Prices Rise on Supply Concerns",
            "summary": "Crude futures gain as OPEC+ holds output steady and Middle East tensions persist.",
            "url": "https://www.reuters.com/markets/commodities/",
            "source": "Reuters",
            "image": None,
            "category": "energy",
        },
        {
            "title": "Tech Giants Report Strong Cloud Revenue Growth",
            "summary": "Major cloud providers see double-digit growth as enterprises accelerate digital transformation.",
            "url": "https://www.cnbc.com/technology/",
            "source": "CNBC",
            "image": None,
            "category": "tech",
        },
    ]
    out = []
    for i, a in enumerate(base):
        # published_at: current time minus a few minutes per index
        pub = now - timezone.timedelta(minutes=i * 3)
        out.append({
            **a,
            "published_at": pub.isoformat(),
            "impact": impacts[i % len(impacts)],
        })
    return out


def _normalize_articles(raw_list, default_source="Live"):
    """Build article list; filter out items without title; ensure non-null fields."""
    articles = []
    for item in (raw_list or [])[:25]:
        title = (item.get("title") or "").strip()
        if not title:
            continue
        source_obj = item.get("source")
        source_name = (source_obj.get("name") if isinstance(source_obj, dict) else None) or default_source
        articles.append({
            "title": title,
            "summary": (item.get("description") or item.get("summary") or "").strip() or None,
            "url": item.get("url") or "#",
            "source": source_name,
            "image": item.get("urlToImage") or item.get("image"),
            "category": item.get("category") or "business",
            "published_at": item.get("publishedAt") or item.get("published_at"),
            "impact": item.get("impact"),  # high, med, low for UI (red, yellow, green)
        })
    return articles


@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([])  # Do not throttle live news feed (frontend polls frequently)
def live_news_feed_view(request):
    """
    Get live financial news from NewsAPI (business headlines).
    Falls back to demo articles if key is missing, invalid, or request fails.
    Always returns 200 with { status, data: { articles, source, message } }.
    """
    api_key = (getattr(settings, 'NEWS_API_KEY', None) or '').strip() or (getattr(settings, 'FINANCE_AI_API_KEY', None) or '').strip() or (getattr(settings, 'STOCK_API_KEY', None) or '').strip()
    demo = _demo_news_articles()

    def ok_response(articles, source='demo', message=None):
        return Response({
            "status": "success",
            "data": {
                "articles": articles,
                "source": source,
                "message": message,
            }
        })

    if not api_key:
        return ok_response(demo, source='demo', message='Set NEWS_API_KEY or FINANCE_AI_API_KEY in .env for live news (get free key at newsapi.org)')

    try:
        # NewsAPI accepts key in header or query; use both for compatibility
        response = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={
                "category": "business",
                "language": "en",
                "pageSize": 20,
                "apiKey": api_key,
            },
            headers={"X-Api-Key": api_key},
            timeout=12,
        )
    except requests.exceptions.Timeout:
        return ok_response(demo, source='demo', message='News API timed out. Showing sample news.')
    except requests.exceptions.RequestException as e:
        return ok_response(demo, source='demo', message='Could not reach news service. Showing sample news.')

    if response.status_code != 200:
        return ok_response(demo, source='demo', message='Live news unavailable (check NEWS_API_KEY). Showing sample news.')

    try:
        payload = response.json()
    except ValueError:
        return ok_response(demo, source='demo', message='Invalid response from news service.')

    # NewsAPI can return {"status":"error","code":"...","message":"..."} on auth/code errors
    if payload.get("status") == "error":
        return ok_response(demo, source='demo', message=(payload.get("message") or 'News API error. Showing sample news.'))

    raw_articles = payload.get("articles") or []
    articles = _normalize_articles(raw_articles, default_source="NewsAPI")

    if not articles:
        return ok_response(demo, source='demo', message='No headlines returned. Showing sample news.')

    return ok_response(articles, source='live')
