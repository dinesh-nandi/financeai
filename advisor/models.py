"""
Advisor models for FinanceAI
"""
from django.db import models
from django.contrib.auth.models import User


class ChatSession(models.Model):
    """AI chat sessions"""
    
    SESSION_TYPES = [
        ('general', 'General Advice'),
        ('portfolio', 'Portfolio Analysis'),
        ('stock', 'Stock Analysis'),
        ('strategy', 'Investment Strategy'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=200, blank=True)
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default='general')
    context_data = models.JSONField(default=dict, blank=True, help_text='Context data for the session')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'advisor_chat_sessions'
        ordering = ['-updated_at']
        verbose_name = 'Chat Session'
        verbose_name_plural = 'Chat Sessions'
    
    def __str__(self):
        return f"{self.user.username} - {self.session_type} - {self.created_at}"


class ChatMessage(models.Model):
    """Individual chat messages"""
    
    SENDER_CHOICES = [
        ('user', 'User'),
        ('ai', 'AI'),
    ]
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True, help_text='Additional metadata')
    tokens_used = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'advisor_chat_messages'
        ordering = ['created_at']
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'
    
    def __str__(self):
        return f"{self.session.user.username} - {self.sender} - {self.created_at}"


class InvestmentRecommendation(models.Model):
    """AI-generated investment recommendations"""
    
    RECOMMENDATION_TYPES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
        ('hold', 'Hold'),
        ('watch', 'Watch'),
    ]
    
    RISK_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    stock = models.ForeignKey('prediction.Stock', on_delete=models.CASCADE, related_name='recommendations', null=True, blank=True)
    recommendation_type = models.CharField(max_length=10, choices=RECOMMENDATION_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    reasoning = models.TextField()
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS, default='medium')
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=70)
    target_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    stop_loss = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    timeframe = models.CharField(max_length=50, default='3-6 months')
    is_active = models.BooleanField(default=True)
    was_successful = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'advisor_recommendations'
        ordering = ['-created_at']
        verbose_name = 'Investment Recommendation'
        verbose_name_plural = 'Investment Recommendations'
    
    def __str__(self):
        return f"{self.user.username} - {self.recommendation_type} - {self.title[:50]}"


class PortfolioReport(models.Model):
    """AI-generated portfolio reports"""
    
    REPORT_TYPES = [
        ('daily', 'Daily Summary'),
        ('weekly', 'Weekly Analysis'),
        ('monthly', 'Monthly Review'),
        ('custom', 'Custom Report'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolio_reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    title = models.CharField(max_length=200)
    summary = models.TextField()
    content = models.JSONField(default=dict, help_text='Structured report content')
    key_metrics = models.JSONField(default=dict)
    recommendations = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'advisor_portfolio_reports'
        ordering = ['-created_at']
        verbose_name = 'Portfolio Report'
        verbose_name_plural = 'Portfolio Reports'
    
    def __str__(self):
        return f"{self.user.username} - {self.report_type} - {self.created_at}"


class AIModelConfig(models.Model):
    """AI model configuration"""
    
    name = models.CharField(max_length=100)
    model_version = models.CharField(max_length=50)
    provider = models.CharField(max_length=50, default='openai')
    config = models.JSONField(default=dict, help_text='Model configuration parameters')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'advisor_ai_model_configs'
        verbose_name = 'AI Model Config'
        verbose_name_plural = 'AI Model Configs'
    
    def __str__(self):
        return f"{self.name} v{self.model_version}"


class SuggestedPrompt(models.Model):
    """Suggested prompts for users"""
    
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('portfolio', 'Portfolio'),
        ('stock', 'Stock Analysis'),
        ('learning', 'Learning'),
        ('strategy', 'Strategy'),
    ]
    
    prompt = models.CharField(max_length=500)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='💬')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'advisor_suggested_prompts'
        ordering = ['category', 'order']
        verbose_name = 'Suggested Prompt'
        verbose_name_plural = 'Suggested Prompts'
    
    def __str__(self):
        return self.prompt[:100]
