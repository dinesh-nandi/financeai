"""
Prediction serializers for FinanceAI
"""
from rest_framework import serializers
from .models import Stock, Prediction, StockPriceHistory, AIPredictionModel, MarketIndicator


class StockSerializer(serializers.ModelSerializer):
    """Serializer for stocks"""
    price_change = serializers.ReadOnlyField()
    
    class Meta:
        model = Stock
        fields = [
            'id', 'symbol', 'name', 'sector', 'current_price',
            'previous_close', 'price_change', 'market_cap',
            'volume', 'pe_ratio', 'last_updated'
        ]


class StockPriceHistorySerializer(serializers.ModelSerializer):
    """Serializer for stock price history"""
    
    class Meta:
        model = StockPriceHistory
        fields = ['date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume']


class PredictionSerializer(serializers.ModelSerializer):
    """Serializer for predictions"""
    stock_symbol = serializers.CharField(source='stock.symbol', read_only=True)
    stock_name = serializers.CharField(source='stock.name', read_only=True)
    
    class Meta:
        model = Prediction
        fields = [
            'id', 'stock', 'stock_symbol', 'stock_name',
            'user_prediction', 'ai_prediction', 'ai_confidence',
            'ai_explanation', 'actual_result', 'is_correct',
            'price_at_prediction', 'predicted_for_date',
            'created_at', 'resolved_at'
        ]
        read_only_fields = ['ai_prediction', 'ai_confidence', 'ai_explanation', 'actual_result', 'is_correct']


class MakePredictionSerializer(serializers.Serializer):
    """Serializer for making a prediction"""
    stock_symbol = serializers.CharField(required=True)
    prediction = serializers.ChoiceField(choices=['up', 'down'])
    horizon = serializers.IntegerField(default=1, min_value=1, max_value=30)  # days
    model_type = serializers.ChoiceField(
        choices=[('linear', 'Linear Regression'), ('lstm', 'LSTM'), ('arima', 'ARIMA'), ('rf', 'Random Forest')],
        default='linear'
    )


class AIPredictionModelSerializer(serializers.ModelSerializer):
    """Serializer for AI prediction models"""
    accuracy_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = AIPredictionModel
        fields = [
            'id', 'name', 'version', 'description',
            'accuracy_score', 'accuracy_percentage',
            'total_predictions', 'correct_predictions',
            'is_active', 'created_at'
        ]


class MarketIndicatorSerializer(serializers.ModelSerializer):
    """Serializer for market indicators"""
    stock_symbol = serializers.CharField(source='stock.symbol', read_only=True)
    
    class Meta:
        model = MarketIndicator
        fields = ['id', 'stock_symbol', 'indicator_type', 'value', 'period', 'calculated_at']


class PredictionResultSerializer(serializers.Serializer):
    """Serializer for prediction results"""
    user_prediction = serializers.CharField()
    ai_prediction = serializers.CharField()
    ai_confidence = serializers.FloatField()
    ai_explanation = serializers.CharField()
    actual_result = serializers.CharField(required=False, allow_null=True)
    is_correct = serializers.BooleanField(required=False, allow_null=True)


class PredictionStatsSerializer(serializers.Serializer):
    """Serializer for prediction statistics"""
    total_predictions = serializers.IntegerField()
    correct_predictions = serializers.IntegerField()
    accuracy_percentage = serializers.FloatField()
    recent_predictions = PredictionSerializer(many=True)
    ai_accuracy = serializers.FloatField()
