"""
News serializers for FinanceAI
"""
from rest_framework import serializers
from .models import NewsArticle, SentimentAnalysis, NewsSource, UserNewsPreference, NewsBookmark


class NewsArticleSerializer(serializers.ModelSerializer):
    """Serializer for news articles"""
    sentiment_label = serializers.ReadOnlyField()
    impact_label = serializers.ReadOnlyField()
    related_stocks_list = serializers.SerializerMethodField()
    
    class Meta:
        model = NewsArticle
        fields = [
            'id', 'title', 'summary', 'url', 'source', 'author',
            'category', 'sentiment', 'sentiment_label', 'sentiment_score',
            'sentiment_confidence', 'impact_level', 'impact_label',
            'impact_score', 'related_stocks_list',
            'published_at', 'view_count'
        ]
    
    def get_related_stocks_list(self, obj):
        return [stock.symbol for stock in obj.related_stocks.all()]


class NewsArticleDetailSerializer(NewsArticleSerializer):
    """Detailed serializer for news articles"""
    content = serializers.CharField()
    
    class Meta(NewsArticleSerializer.Meta):
        fields = NewsArticleSerializer.Meta.fields + ['content', 'fetched_at']


class SentimentAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for sentiment analysis"""
    
    class Meta:
        model = SentimentAnalysis
        fields = [
            'date', 'overall_sentiment', 'overall_score',
            'total_articles', 'positive_count', 'negative_count', 'neutral_count',
            'positive_percentage', 'negative_percentage', 'neutral_percentage',
            'market_correlation'
        ]


class SentimentSummarySerializer(serializers.Serializer):
    """Serializer for sentiment summary"""
    overall_sentiment = serializers.CharField()
    overall_score = serializers.FloatField()
    positive_percentage = serializers.FloatField()
    negative_percentage = serializers.FloatField()
    neutral_percentage = serializers.FloatField()
    total_articles = serializers.IntegerField()
    positive_count = serializers.IntegerField()
    negative_count = serializers.IntegerField()
    neutral_count = serializers.IntegerField()
    trend = serializers.ListField()


class NewsSourceSerializer(serializers.ModelSerializer):
    """Serializer for news sources"""
    
    class Meta:
        model = NewsSource
        fields = ['id', 'name', 'url', 'is_active', 'reliability_score']


class UserNewsPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for user news preferences"""
    
    class Meta:
        model = UserNewsPreference
        fields = [
            'preferred_categories', 'watchlist_keywords',
            'min_impact_level', 'email_notifications', 'push_notifications'
        ]


class NewsBookmarkSerializer(serializers.ModelSerializer):
    """Serializer for news bookmarks"""
    article = NewsArticleSerializer(read_only=True)
    
    class Meta:
        model = NewsBookmark
        fields = ['id', 'article', 'notes', 'created_at']


class NewsFilterSerializer(serializers.Serializer):
    """Serializer for news filter parameters"""
    category = serializers.ChoiceField(
        choices=NewsArticle.CATEGORY_CHOICES,
        required=False
    )
    sentiment = serializers.ChoiceField(
        choices=NewsArticle.SENTIMENT_CHOICES,
        required=False
    )
    impact = serializers.ChoiceField(
        choices=NewsArticle.IMPACT_CHOICES,
        required=False
    )
    search = serializers.CharField(required=False)
    days = serializers.IntegerField(default=7, min_value=1, max_value=30)
