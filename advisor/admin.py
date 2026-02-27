"""
Advisor admin configuration
"""
from django.contrib import admin
from .models import ChatSession, ChatMessage, InvestmentRecommendation, PortfolioReport, AIModelConfig, SuggestedPrompt


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ['created_at']


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_type', 'title', 'is_active', 'created_at']
    list_filter = ['session_type', 'is_active']
    search_fields = ['user__username', 'title']
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'sender', 'content_preview', 'created_at']
    list_filter = ['sender']
    search_fields = ['content']
    
    def content_preview(self, obj):
        return obj.content[:100]
    content_preview.short_description = 'Content'


@admin.register(InvestmentRecommendation)
class InvestmentRecommendationAdmin(admin.ModelAdmin):
    list_display = ['user', 'stock', 'recommendation_type', 'risk_level', 'confidence_score', 'created_at']
    list_filter = ['recommendation_type', 'risk_level', 'is_active']
    search_fields = ['user__username', 'title']


@admin.register(PortfolioReport)
class PortfolioReportAdmin(admin.ModelAdmin):
    list_display = ['user', 'report_type', 'title', 'created_at']
    list_filter = ['report_type']
    search_fields = ['user__username', 'title']


@admin.register(AIModelConfig)
class AIModelConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'model_version', 'provider', 'is_active']
    list_filter = ['provider', 'is_active']


@admin.register(SuggestedPrompt)
class SuggestedPromptAdmin(admin.ModelAdmin):
    list_display = ['prompt_preview', 'category', 'order', 'is_active']
    list_filter = ['category', 'is_active']
    list_editable = ['order', 'is_active']
    
    def prompt_preview(self, obj):
        return obj.prompt[:80]
    prompt_preview.short_description = 'Prompt'
