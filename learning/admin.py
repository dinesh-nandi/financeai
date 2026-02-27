"""
Learning admin configuration
"""
from django.contrib import admin
from .models import Topic, QuizQuestion, UserProgress, QuizAttempt, Course


class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 1


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'order', 'estimated_duration', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [QuizQuestionInline]


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ['topic', 'question', 'question_type', 'points', 'order']
    list_filter = ['topic', 'question_type']
    search_fields = ['question']


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'topic', 'is_completed', 'quiz_score', 'last_accessed']
    list_filter = ['is_completed', 'topic']
    search_fields = ['user__username', 'topic__title']


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'topic', 'score', 'completed_at']
    list_filter = ['topic']
    search_fields = ['user__username']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'difficulty', 'estimated_duration', 'is_active']
    list_filter = ['difficulty', 'is_active']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['topics']
