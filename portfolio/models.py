"""
Portfolio models for FinanceAI
"""
from django.db import models
from django.contrib.auth.models import User


class Portfolio(models.Model):
    """User's portfolio holdings"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolio_items')
    stock = models.ForeignKey('prediction.Stock', on_delete=models.CASCADE, related_name='portfolio_entries')
    shares = models.DecimalField(max_digits=15, decimal_places=4)
    average_buy_price = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Tracking
    first_buy_date = models.DateField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'portfolio_holdings'
        unique_together = ['user', 'stock']
        ordering = ['-last_updated']
        verbose_name = 'Portfolio Holding'
        verbose_name_plural = 'Portfolio Holdings'
    
    def __str__(self):
        return f"{self.user.username} - {self.stock.symbol} ({self.shares} shares)"
    
    @property
    def current_value(self):
        """Calculate current value of holding"""
        return self.shares * self.stock.current_price
    
    @property
    def cost_basis(self):
        """Calculate total cost basis"""
        return self.shares * self.average_buy_price
    
    @property
    def gain_loss(self):
        """Calculate gain/loss"""
        return self.current_value - self.cost_basis
    
    @property
    def gain_loss_percentage(self):
        """Calculate gain/loss percentage"""
        if self.cost_basis == 0:
            return 0
        return round(((self.current_value - self.cost_basis) / self.cost_basis) * 100, 2)
    
    @property
    def day_change(self):
        """Calculate day's change"""
        return self.shares * (self.stock.current_price - self.stock.previous_close)


class PortfolioTransaction(models.Model):
    """Portfolio buy/sell transactions"""
    
    TRANSACTION_TYPES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
        ('dividend', 'Dividend'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolio_transactions')
    stock = models.ForeignKey('prediction.Stock', on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    shares = models.DecimalField(max_digits=15, decimal_places=4)
    price_per_share = models.DecimalField(max_digits=15, decimal_places=2)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'portfolio_transactions'
        ordering = ['-transaction_date']
        verbose_name = 'Portfolio Transaction'
        verbose_name_plural = 'Portfolio Transactions'
    
    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} {self.shares} {self.stock.symbol}"
    
    def save(self, *args, **kwargs):
        # Calculate total amount
        self.total_amount = (self.shares * self.price_per_share) + self.fees
        super().save(*args, **kwargs)


class PortfolioAnalytics(models.Model):
    """Portfolio analytics and performance metrics"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='portfolio_analytics')
    
    # Risk metrics
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=50)
    volatility = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    beta = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    sharpe_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Diversification
    sector_allocation = models.JSONField(default=dict, blank=True)
    diversification_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Performance
    total_return = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    annualized_return = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Calculated at
    calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'portfolio_analytics'
        verbose_name = 'Portfolio Analytics'
        verbose_name_plural = 'Portfolio Analytics'
    
    def __str__(self):
        return f"{self.user.username}'s Portfolio Analytics"


class Watchlist(models.Model):
    """User's stock watchlist"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlists')
    name = models.CharField(max_length=100, default='My Watchlist')
    stocks = models.ManyToManyField('prediction.Stock', related_name='watchlists')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'portfolio_watchlists'
        ordering = ['-created_at']
        verbose_name = 'Watchlist'
        verbose_name_plural = 'Watchlists'
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"


class PortfolioHistory(models.Model):
    """Daily portfolio value history"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolio_history')
    date = models.DateField()
    total_value = models.DecimalField(max_digits=15, decimal_places=2)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2)
    day_gain_loss = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'portfolio_history'
        unique_together = ['user', 'date']
        ordering = ['-date']
        verbose_name = 'Portfolio History'
        verbose_name_plural = 'Portfolio Histories'
    
    def __str__(self):
        return f"{self.user.username} - {self.date} - ${self.total_value}"
    
    @property
    def total_gain_loss(self):
        return self.total_value - self.total_cost
