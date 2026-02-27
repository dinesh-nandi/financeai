"""
Prediction models for FinanceAI
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Stock(models.Model):
    """Stock information"""
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=200)
    sector = models.CharField(max_length=100, blank=True)
    current_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    previous_close = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    market_cap = models.BigIntegerField(null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    pe_ratio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fifty_two_week_high = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    fifty_two_week_low = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'prediction_stocks'
        ordering = ['symbol']
        verbose_name = 'Stock'
        verbose_name_plural = 'Stocks'
    
    def __str__(self):
        return f"{self.symbol} - {self.name}"
    
    @property
    def price_change(self):
        if self.previous_close:
            return round(
                ((self.current_price - self.previous_close) / self.previous_close) * 100, 
                2
            )
        return 0


class Prediction(models.Model):
    """User stock predictions"""
    
    DIRECTION_CHOICES = [
        ('up', 'Up'),
        ('down', 'Down'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='predictions')
    user_prediction = models.CharField(max_length=4, choices=DIRECTION_CHOICES)
    ai_prediction = models.CharField(max_length=4, choices=DIRECTION_CHOICES)
    ai_confidence = models.DecimalField(max_digits=5, decimal_places=2, default=70.00)
    ai_explanation = models.TextField(blank=True)
    actual_result = models.CharField(max_length=4, choices=DIRECTION_CHOICES, blank=True, null=True)
    is_correct = models.BooleanField(null=True, blank=True)
    price_at_prediction = models.DecimalField(max_digits=15, decimal_places=2)
    predicted_for_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'prediction_predictions'
        ordering = ['-created_at']
        verbose_name = 'Prediction'
        verbose_name_plural = 'Predictions'
    
    def __str__(self):
        return f"{self.user.username} - {self.stock.symbol} - {self.user_prediction}"
    
    def resolve(self, actual_price):
        """Resolve prediction with actual price"""
        self.actual_result = 'up' if actual_price >= self.price_at_prediction else 'down'
        self.is_correct = self.user_prediction == self.actual_result
        self.resolved_at = timezone.now()
        self.save(update_fields=['actual_result', 'is_correct', 'resolved_at'])

        # Update user profile: only correct_predictions (total already incremented at create)
        profile = getattr(self.user, 'profile', None)
        if profile is not None and self.is_correct:
            profile.correct_predictions = (profile.correct_predictions or 0) + 1
            profile.save(update_fields=['correct_predictions'])


class StockPriceHistory(models.Model):
    """Historical stock prices"""
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='price_history')
    date = models.DateField()
    open_price = models.DecimalField(max_digits=15, decimal_places=2)
    high_price = models.DecimalField(max_digits=15, decimal_places=2)
    low_price = models.DecimalField(max_digits=15, decimal_places=2)
    close_price = models.DecimalField(max_digits=15, decimal_places=2)
    volume = models.BigIntegerField()
    
    class Meta:
        db_table = 'prediction_price_history'
        unique_together = ['stock', 'date']
        ordering = ['-date']
        verbose_name = 'Stock Price History'
        verbose_name_plural = 'Stock Price Histories'
    
    def __str__(self):
        return f"{self.stock.symbol} - {self.date}"


class AIPredictionModel(models.Model):
    """AI prediction model settings and performance"""
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=20)
    description = models.TextField()
    accuracy_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_predictions = models.IntegerField(default=0)
    correct_predictions = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'prediction_ai_models'
        ordering = ['-created_at']
        verbose_name = 'AI Prediction Model'
        verbose_name_plural = 'AI Prediction Models'
    
    def __str__(self):
        return f"{self.name} v{self.version}"
    
    @property
    def accuracy_percentage(self):
        if self.total_predictions == 0:
            return 0
        return round((self.correct_predictions / self.total_predictions) * 100, 2)


class MarketIndicator(models.Model):
    """Market indicators for AI predictions"""
    INDICATOR_TYPES = [
        ('rsi', 'RSI'),
        ('macd', 'MACD'),
        ('sma', 'Simple Moving Average'),
        ('ema', 'Exponential Moving Average'),
        ('volume', 'Volume'),
        ('sentiment', 'Sentiment'),
    ]
    
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='indicators')
    indicator_type = models.CharField(max_length=20, choices=INDICATOR_TYPES)
    value = models.DecimalField(max_digits=15, decimal_places=4)
    period = models.PositiveIntegerField(default=14, help_text='Period for the indicator')
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'prediction_market_indicators'
        ordering = ['-calculated_at']
        verbose_name = 'Market Indicator'
        verbose_name_plural = 'Market Indicators'
    
    def __str__(self):
        return f"{self.stock.symbol} - {self.indicator_type}"
