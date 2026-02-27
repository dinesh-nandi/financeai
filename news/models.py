"""
News models for FinanceAI
"""
from django.db import models
from django.contrib.auth.models import User


class NewsArticle(models.Model):
    """Financial news articles"""
    
    SENTIMENT_CHOICES = [
        ('positive', 'Positive'),
        ('negative', 'Negative'),
        ('neutral', 'Neutral'),
    ]
    
    IMPACT_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    CATEGORY_CHOICES = [
        ('tech', 'Technology'),
        ('finance', 'Finance'),
        ('energy', 'Energy'),
        ('healthcare', 'Healthcare'),
        ('consumer', 'Consumer'),
        ('industrial', 'Industrial'),
        ('general', 'General'),
    ]
    
    title = models.CharField(max_length=500)
    summary = models.TextField()
    content = models.TextField(blank=True)
    url = models.URLField()
    source = models.CharField(max_length=100)
    author = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    
    # Sentiment analysis
    sentiment = models.CharField(max_length=10, choices=SENTIMENT_CHOICES, default='neutral')
    sentiment_score = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    sentiment_confidence = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Impact analysis
    impact_level = models.CharField(max_length=10, choices=IMPACT_CHOICES, default='medium')
    impact_score = models.DecimalField(max_digits=5, decimal_places=2, default=50)
    
    # Related stocks
    related_stocks = models.ManyToManyField('prediction.Stock', blank=True, related_name='news_articles')
    
    # Metadata
    published_at = models.DateTimeField()
    fetched_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    view_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'news_articles'
        ordering = ['-published_at']
        verbose_name = 'News Article'
        verbose_name_plural = 'News Articles'
    
    def __str__(self):
        return self.title[:100]
    
    @property
    def sentiment_label(self):
        """Get sentiment label with emoji"""
        labels = {
            'positive': '🟢 Positive',
            'negative': '🔴 Negative',
            'neutral': '🟡 Neutral'
        }
        return labels.get(self.sentiment, 'Neutral')
    
    @property
    def impact_label(self):
        """Get impact label"""
        labels = {
            'high': '🔴 High Impact',
            'medium': '🟠 Medium Impact',
            'low': '🟢 Low Impact'
        }
        return labels.get(self.impact_level, 'Medium')


class SentimentAnalysis(models.Model):
    """Daily sentiment analysis summary"""
    date = models.DateField(unique=True)
    
    # Overall sentiment
    overall_sentiment = models.CharField(
        max_length=10,
        choices=NewsArticle.SENTIMENT_CHOICES,
        default='neutral'
    )
    overall_score = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    
    # Article counts
    total_articles = models.PositiveIntegerField(default=0)
    positive_count = models.PositiveIntegerField(default=0)
    negative_count = models.PositiveIntegerField(default=0)
    neutral_count = models.PositiveIntegerField(default=0)
    
    # Sentiment percentages
    positive_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    negative_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    neutral_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Market correlation
    market_correlation = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'news_sentiment_analysis'
        ordering = ['-date']
        verbose_name = 'Sentiment Analysis'
        verbose_name_plural = 'Sentiment Analyses'
    
    def __str__(self):
        return f"Sentiment {self.date} - {self.overall_sentiment}"


class NewsSource(models.Model):
    """News sources configuration"""
    name = models.CharField(max_length=100)
    url = models.URLField()
    api_key = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    reliability_score = models.DecimalField(max_digits=4, decimal_places=2, default=8.0)
    fetch_interval = models.PositiveIntegerField(default=60, help_text='Fetch interval in minutes')
    last_fetch = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'news_sources'
        ordering = ['name']
        verbose_name = 'News Source'
        verbose_name_plural = 'News Sources'
    
    def __str__(self):
        return self.name


class UserNewsPreference(models.Model):
    """User news preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='news_preferences')
    
    # Categories
    preferred_categories = models.JSONField(default=list, blank=True)
    
    # Keywords
    watchlist_keywords = models.JSONField(default=list, blank=True)
    
    # Filters
    min_impact_level = models.CharField(
        max_length=10,
        choices=NewsArticle.IMPACT_CHOICES,
        default='low'
    )
    
    # Notifications
    email_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'news_user_preferences'
        verbose_name = 'User News Preference'
        verbose_name_plural = 'User News Preferences'
    
    def __str__(self):
        return f"{self.user.username}'s News Preferences"


class NewsBookmark(models.Model):
    """User bookmarked news"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarked_news')
    article = models.ForeignKey(NewsArticle, on_delete=models.CASCADE, related_name='bookmarks')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'news_bookmarks'
        unique_together = ['user', 'article']
        ordering = ['-created_at']
        verbose_name = 'News Bookmark'
        verbose_name_plural = 'News Bookmarks'
    
    def __str__(self):
        return f"{self.user.username} - {self.article.title[:50]}"
