"""
Advisor serializers for FinanceAI
"""
from rest_framework import serializers
from .models import ChatSession, ChatMessage, InvestmentRecommendation, PortfolioReport, SuggestedPrompt


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages"""
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'content', 'created_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    """Serializer for chat sessions"""
    messages = ChatMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = [
            'id', 'title', 'session_type', 'context_data',
            'is_active', 'message_count', 'messages',
            'created_at', 'updated_at'
        ]
    
    def get_message_count(self, obj):
        return obj.messages.count()


class CreateChatSessionSerializer(serializers.Serializer):
    """Serializer for creating chat session"""
    session_type = serializers.ChoiceField(
        choices=ChatSession.SESSION_TYPES,
        default='general'
    )
    title = serializers.CharField(required=False, allow_blank=True)


class ChatRequestSerializer(serializers.Serializer):
    """Serializer for chat request"""
    message = serializers.CharField(required=True)
    session_id = serializers.IntegerField(required=False, allow_null=True)


class ChatResponseSerializer(serializers.Serializer):
    """Serializer for chat response"""
    response = serializers.CharField()
    session_id = serializers.IntegerField()
    suggested_followups = serializers.ListField(child=serializers.CharField())


class InvestmentRecommendationSerializer(serializers.ModelSerializer):
    """Serializer for investment recommendations"""
    stock_symbol = serializers.CharField(source='stock.symbol', read_only=True)
    stock_name = serializers.CharField(source='stock.name', read_only=True)
    
    class Meta:
        model = InvestmentRecommendation
        fields = [
            'id', 'stock_symbol', 'stock_name', 'recommendation_type',
            'title', 'description', 'reasoning', 'risk_level',
            'confidence_score', 'target_price', 'stop_loss',
            'timeframe', 'is_active', 'created_at'
        ]


class PortfolioReportSerializer(serializers.ModelSerializer):
    """Serializer for portfolio reports"""
    
    class Meta:
        model = PortfolioReport
        fields = [
            'id', 'report_type', 'title', 'summary',
            'content', 'key_metrics', 'recommendations', 'created_at'
        ]


class SuggestedPromptSerializer(serializers.ModelSerializer):
    """Serializer for suggested prompts"""
    
    class Meta:
        model = SuggestedPrompt
        fields = ['id', 'prompt', 'category', 'description', 'icon']


class AdvisorStatsSerializer(serializers.Serializer):
    """Serializer for advisor statistics"""
    total_sessions = serializers.IntegerField()
    total_messages = serializers.IntegerField()
    active_recommendations = serializers.IntegerField()
    average_response_time = serializers.FloatField()
    user_satisfaction = serializers.FloatField()


class PortfolioContextSerializer(serializers.Serializer):
    """Serializer for portfolio context sent to AI"""
    total_value = serializers.FloatField()
    total_gain_loss = serializers.FloatField()
    risk_score = serializers.FloatField()
    holdings = serializers.ListField()
    sector_allocation = serializers.DictField()


class AIAnalysisRequestSerializer(serializers.Serializer):
    """Serializer for AI analysis request"""
    analysis_type = serializers.ChoiceField(
        choices=['portfolio', 'stock', 'market', 'strategy']
    )
    stock_symbol = serializers.CharField(required=False, allow_blank=True)
    additional_context = serializers.DictField(required=False)
