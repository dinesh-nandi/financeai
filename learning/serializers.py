"""
Learning serializers for FinanceAI
"""
from rest_framework import serializers
from .models import Topic, QuizQuestion, UserProgress, QuizAttempt, Course


class QuizQuestionSerializer(serializers.ModelSerializer):
    """Serializer for quiz questions"""
    
    class Meta:
        model = QuizQuestion
        fields = ['id', 'question', 'question_type', 'options', 'explanation', 'points', 'order']


class TopicSerializer(serializers.ModelSerializer):
    """Serializer for learning topics"""
    question_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Topic
        fields = [
            'id', 'title', 'slug', 'category', 'description', 
            'icon', 'order', 'estimated_duration', 'question_count',
            'created_at'
        ]
    
    def get_question_count(self, obj):
        return obj.questions.count()


class TopicDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for topics including content and questions"""
    questions = QuizQuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Topic
        fields = [
            'id', 'title', 'slug', 'category', 'description',
            'content', 'icon', 'order', 'estimated_duration',
            'questions', 'created_at'
        ]


class UserProgressSerializer(serializers.ModelSerializer):
    """Serializer for user progress"""
    topic_title = serializers.CharField(source='topic.title', read_only=True)
    topic_category = serializers.CharField(source='topic.category', read_only=True)
    
    class Meta:
        model = UserProgress
        fields = [
            'id', 'topic', 'topic_title', 'topic_category',
            'is_completed', 'completion_date', 'quiz_score',
            'quiz_attempts', 'time_spent', 'last_accessed'
        ]


class QuizAttemptSerializer(serializers.ModelSerializer):
    """Serializer for quiz attempts"""
    topic_title = serializers.CharField(source='topic.title', read_only=True)
    percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = QuizAttempt
        fields = [
            'id', 'topic', 'topic_title', 'score',
            'total_questions', 'correct_answers', 'percentage',
            'answers', 'completed_at'
        ]


class QuizSubmitSerializer(serializers.Serializer):
    """Serializer for quiz submission"""
    topic_id = serializers.IntegerField(required=True)
    answers = serializers.DictField(
        child=serializers.IntegerField(),
        help_text='Dictionary of question_id: answer_index'
    )


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for courses"""
    topic_count = serializers.SerializerMethodField()
    topics = TopicSerializer(many=True, read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description',
            'topics', 'topic_count', 'difficulty',
            'estimated_duration', 'is_active', 'created_at'
        ]
    
    def get_topic_count(self, obj):
        return obj.topics.count()


class LearningStatsSerializer(serializers.Serializer):
    """Serializer for learning statistics"""
    total_topics = serializers.IntegerField()
    completed_topics = serializers.IntegerField()
    completion_percentage = serializers.FloatField()
    total_quiz_attempts = serializers.IntegerField()
    average_quiz_score = serializers.FloatField()
    total_time_spent = serializers.IntegerField()
    recent_activity = serializers.ListField()
