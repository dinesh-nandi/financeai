"""
Users models for FinanceAI
"""
from django.contrib.auth.models import User
from django.db import models


class WalletAddress(models.Model):
    """Link a Web3 wallet address (e.g. MetaMask) to a user."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    address = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_wallet_addresses'
        verbose_name = 'Wallet Address'
        verbose_name_plural = 'Wallet Addresses'

    def __str__(self):
        return f"{self.address[:10]}... -> {self.user.username}"


class WalletLoginNonce(models.Model):
    """One-time nonce for wallet sign-in (reuse or create per address)."""
    address = models.CharField(max_length=64, unique=True, db_index=True)
    nonce = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_wallet_login_nonces'
        verbose_name = 'Wallet Login Nonce'
        verbose_name_plural = 'Wallet Login Nonces'


class UserProfile(models.Model):
    """Extended user profile with financial preferences"""
    
    RISK_CHOICES = [
        ('conservative', 'Conservative - Safety First'),
        ('moderate', 'Moderate - Balanced Approach'),
        ('aggressive', 'Aggressive - High Risk, High Reward'),
    ]
    
    EXPERIENCE_CHOICES = [
        ('beginner', 'Beginner - Just Starting'),
        ('intermediate', 'Intermediate - Some Experience'),
        ('advanced', 'Advanced - Experienced Trader'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    risk_appetite = models.CharField(max_length=20, choices=RISK_CHOICES, default='moderate')
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='beginner')
    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Statistics
    total_predictions = models.IntegerField(default=0)
    correct_predictions = models.IntegerField(default=0)
    learning_progress = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    @property
    def prediction_accuracy(self):
        """Calculate prediction accuracy percentage"""
        if self.total_predictions == 0:
            return 0
        return round((self.correct_predictions / self.total_predictions) * 100, 2)
    
    @property
    def full_name(self):
        """Return user's full name"""
        return f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username


class UserActivity(models.Model):
    """Track user activities"""
    
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('prediction', 'Made Prediction'),
        ('quiz_complete', 'Completed Quiz'),
        ('portfolio_update', 'Portfolio Update'),
        ('chat', 'AI Chat'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_activities'
        ordering = ['-created_at']
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
    
    def __str__(self):
        return f"{self.user.username} - {self.activity_type}"
