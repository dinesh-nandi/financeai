"""
Portfolio serializers for FinanceAI
"""
from rest_framework import serializers
from .models import Portfolio, PortfolioTransaction, PortfolioAnalytics, Watchlist, PortfolioHistory


class PortfolioSerializer(serializers.ModelSerializer):
    """Serializer for portfolio holdings"""
    stock_symbol = serializers.CharField(source='stock.symbol', read_only=True)
    stock_name = serializers.CharField(source='stock.name', read_only=True)
    current_price = serializers.DecimalField(source='stock.current_price', max_digits=15, decimal_places=2, read_only=True)
    current_value = serializers.ReadOnlyField()
    cost_basis = serializers.ReadOnlyField()
    gain_loss = serializers.ReadOnlyField()
    gain_loss_percentage = serializers.ReadOnlyField()
    day_change = serializers.ReadOnlyField()
    
    class Meta:
        model = Portfolio
        fields = [
            'id', 'stock', 'stock_symbol', 'stock_name',
            'shares', 'average_buy_price', 'current_price',
            'current_value', 'cost_basis', 'gain_loss',
            'gain_loss_percentage', 'day_change',
            'first_buy_date', 'last_updated'
        ]


class AddPortfolioSerializer(serializers.Serializer):
    """Serializer for adding stock to portfolio"""
    stock_symbol = serializers.CharField(required=True)
    shares = serializers.DecimalField(max_digits=15, decimal_places=4, min_value=0.01)
    purchase_price = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=0.01)


class PortfolioTransactionSerializer(serializers.ModelSerializer):
    """Serializer for portfolio transactions"""
    stock_symbol = serializers.CharField(source='stock.symbol', read_only=True)
    
    class Meta:
        model = PortfolioTransaction
        fields = [
            'id', 'stock_symbol', 'transaction_type',
            'shares', 'price_per_share', 'total_amount',
            'fees', 'notes', 'transaction_date'
        ]


class PortfolioAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for portfolio analytics"""
    
    class Meta:
        model = PortfolioAnalytics
        fields = [
            'risk_score', 'volatility', 'beta', 'sharpe_ratio',
            'sector_allocation', 'diversification_score',
            'total_return', 'annualized_return', 'calculated_at'
        ]


class PortfolioSummarySerializer(serializers.Serializer):
    """Serializer for portfolio summary"""
    total_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_cost = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_gain_loss = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_gain_loss_percentage = serializers.FloatField()
    day_gain_loss = serializers.DecimalField(max_digits=15, decimal_places=2)
    day_gain_loss_percentage = serializers.FloatField()
    number_of_holdings = serializers.IntegerField()
    risk_level = serializers.CharField()
    risk_score = serializers.FloatField()


class WatchlistSerializer(serializers.ModelSerializer):
    """Serializer for watchlists"""
    stocks = serializers.SerializerMethodField()
    
    class Meta:
        model = Watchlist
        fields = ['id', 'name', 'stocks', 'created_at']
    
    def get_stocks(self, obj):
        from prediction.serializers import StockSerializer
        return StockSerializer(obj.stocks.all(), many=True).data


class PortfolioHistorySerializer(serializers.ModelSerializer):
    """Serializer for portfolio history"""
    total_gain_loss = serializers.ReadOnlyField()
    
    class Meta:
        model = PortfolioHistory
        fields = ['date', 'total_value', 'total_cost', 'day_gain_loss', 'total_gain_loss']


class AllocationDataSerializer(serializers.Serializer):
    """Serializer for allocation data"""
    labels = serializers.ListField(child=serializers.CharField())
    data = serializers.ListField(child=serializers.FloatField())
    colors = serializers.ListField(child=serializers.CharField())


class PortfolioPerformanceSerializer(serializers.Serializer):
    """Serializer for portfolio performance"""
    labels = serializers.ListField(child=serializers.CharField())
    values = serializers.ListField(child=serializers.FloatField())
