"""
Learning models for FinanceAI
"""
from django.db import models
from django.contrib.auth.models import User


class Topic(models.Model):
    """Learning topic/category"""
    
    CATEGORY_CHOICES = [
        ('basics', 'Investing Basics'),
        ('technical', 'Technical Analysis'),
        ('portfolio', 'Portfolio Management'),
        ('risk', 'Risk Management'),
        ('fundamental', 'Fundamental Analysis'),
        ('advanced', 'Advanced Strategies'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField()
    content = models.TextField()
    icon = models.CharField(max_length=50, default='📚')
    order = models.PositiveIntegerField(default=0)
    estimated_duration = models.PositiveIntegerField(help_text='Duration in minutes', default=15)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'learning_topics'
        ordering = ['category', 'order', 'title']
        verbose_name = 'Topic'
        verbose_name_plural = 'Topics'
    
    def __str__(self):
        return self.title


class QuizQuestion(models.Model):
    """Quiz questions for topics"""
    
    QUESTION_TYPES = [
        ('single', 'Single Choice'),
        ('multiple', 'Multiple Choice'),
        ('true_false', 'True/False'),
    ]
    
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='questions')
    question = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='single')
    options = models.JSONField(help_text='List of options')
    correct_answer = models.PositiveIntegerField(help_text='Index of correct answer')
    explanation = models.TextField(blank=True)
    points = models.PositiveIntegerField(default=10)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'learning_quiz_questions'
        ordering = ['order']
        verbose_name = 'Quiz Question'
        verbose_name_plural = 'Quiz Questions'
    
    def __str__(self):
        return f"{self.topic.title} - Q{self.order}"


class UserProgress(models.Model):
    """Track user learning progress"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_progress')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='user_progress')
    is_completed = models.BooleanField(default=False)
    completion_date = models.DateTimeField(null=True, blank=True)
    quiz_score = models.PositiveIntegerField(default=0)
    quiz_attempts = models.PositiveIntegerField(default=0)
    time_spent = models.PositiveIntegerField(help_text='Time spent in minutes', default=0)
    last_accessed = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'learning_user_progress'
        unique_together = ['user', 'topic']
        ordering = ['-last_accessed']
        verbose_name = 'User Progress'
        verbose_name_plural = 'User Progress'
    
    def __str__(self):
        return f"{self.user.username} - {self.topic.title}"


class QuizAttempt(models.Model):
    """Track individual quiz attempts"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='attempts')
    score = models.PositiveIntegerField()
    total_questions = models.PositiveIntegerField()
    correct_answers = models.PositiveIntegerField()
    answers = models.JSONField(help_text='User answers')
    completed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'learning_quiz_attempts'
        ordering = ['-completed_at']
        verbose_name = 'Quiz Attempt'
        verbose_name_plural = 'Quiz Attempts'
    
    def __str__(self):
        return f"{self.user.username} - {self.topic.title} - {self.score}%"
    
    @property
    def percentage(self):
        if self.total_questions == 0:
            return 0
        return round((self.correct_answers / self.total_questions) * 100, 2)


class Course(models.Model):
    """Course containing multiple topics"""
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    topics = models.ManyToManyField(Topic, related_name='courses')
    difficulty = models.CharField(
        max_length=20,
        choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')],
        default='beginner'
    )
    estimated_duration = models.PositiveIntegerField(help_text='Total duration in minutes', default=60)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'learning_courses'
        ordering = ['difficulty', 'title']
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
    
    def __str__(self):
        return self.title
