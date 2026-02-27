"""
Learning views for FinanceAI
"""
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Avg, Count, Sum

from .models import Topic, QuizQuestion, UserProgress, QuizAttempt, Course
from .serializers import (
    TopicSerializer, TopicDetailSerializer, UserProgressSerializer,
    QuizAttemptSerializer, QuizSubmitSerializer, CourseSerializer,
    LearningStatsSerializer
)


class TopicListView(generics.ListAPIView):
    """List all learning topics"""
    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Topic.objects.filter(is_active=True)
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Add user progress info
        topics_with_progress = []
        for topic in serializer.data:
            progress = UserProgress.objects.filter(
                user=request.user,
                topic_id=topic['id']
            ).first()
            
            topic_data = topic.copy()
            if progress:
                topic_data['user_progress'] = {
                    'is_completed': progress.is_completed,
                    'quiz_score': progress.quiz_score,
                    'quiz_attempts': progress.quiz_attempts
                }
            else:
                topic_data['user_progress'] = None
            
            topics_with_progress.append(topic_data)
        
        return Response({
            'status': 'success',
            'data': topics_with_progress
        })


class TopicDetailView(generics.RetrieveAPIView):
    """Get detailed topic information"""
    queryset = Topic.objects.filter(is_active=True)
    serializer_class = TopicDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Get or create user progress
        progress, created = UserProgress.objects.get_or_create(
            user=request.user,
            topic=instance,
            defaults={'time_spent': 0}
        )
        
        # Update last accessed
        progress.last_accessed = timezone.now()
        progress.save()
        
        data = serializer.data
        data['user_progress'] = UserProgressSerializer(progress).data
        
        return Response({
            'status': 'success',
            'data': data
        })


class SubmitQuizView(generics.CreateAPIView):
    """Submit quiz answers"""
    serializer_class = QuizSubmitSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        topic_id = serializer.validated_data['topic_id']
        answers = serializer.validated_data['answers']
        
        try:
            topic = Topic.objects.get(id=topic_id)
        except Topic.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Topic not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get questions for this topic
        questions = QuizQuestion.objects.filter(topic=topic)
        
        # Calculate score
        correct_count = 0
        total_points = 0
        earned_points = 0
        
        for question in questions:
            total_points += question.points
            user_answer = answers.get(str(question.id))
            if user_answer is not None and user_answer == question.correct_answer:
                correct_count += 1
                earned_points += question.points
        
        score_percentage = round((earned_points / total_points) * 100) if total_points > 0 else 0
        
        # Save quiz attempt
        quiz_attempt = QuizAttempt.objects.create(
            user=request.user,
            topic=topic,
            score=score_percentage,
            total_questions=questions.count(),
            correct_answers=correct_count,
            answers=answers
        )
        
        # Update user progress
        progress, _ = UserProgress.objects.get_or_create(
            user=request.user,
            topic=topic
        )
        progress.quiz_attempts += 1
        
        if score_percentage >= 70:  # Pass threshold
            progress.is_completed = True
            progress.completion_date = timezone.now()
        
        if score_percentage > progress.quiz_score:
            progress.quiz_score = score_percentage
        
        progress.save()
        
        return Response({
            'status': 'success',
            'data': {
                'score': score_percentage,
                'correct_answers': correct_count,
                'total_questions': questions.count(),
                'passed': score_percentage >= 70,
                'attempt': QuizAttemptSerializer(quiz_attempt).data
            }
        })


class UserProgressListView(generics.ListAPIView):
    """List user's learning progress"""
    serializer_class = UserProgressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserProgress.objects.filter(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data
        })


class CourseListView(generics.ListAPIView):
    """List all courses"""
    queryset = Course.objects.filter(is_active=True)
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def learning_stats_view(request):
    """Get user's learning statistics"""
    user = request.user
    
    # Get progress stats
    total_topics = Topic.objects.filter(is_active=True).count()
    completed_topics = UserProgress.objects.filter(
        user=user,
        is_completed=True
    ).count()
    
    completion_percentage = round((completed_topics / total_topics) * 100, 2) if total_topics > 0 else 0
    
    # Quiz stats
    quiz_stats = QuizAttempt.objects.filter(user=user).aggregate(
        total_attempts=Count('id'),
        avg_score=Avg('score')
    )
    
    # Time spent
    time_stats = UserProgress.objects.filter(user=user).aggregate(
        total_time=Sum('time_spent')
    )
    
    # Recent activity
    recent_attempts = QuizAttempt.objects.filter(
        user=user
    ).order_by('-completed_at')[:5]
    
    data = {
        'total_topics': total_topics,
        'completed_topics': completed_topics,
        'completion_percentage': completion_percentage,
        'total_quiz_attempts': quiz_stats['total_attempts'] or 0,
        'average_quiz_score': round(quiz_stats['avg_score'] or 0, 2),
        'total_time_spent': time_stats['total_time'] or 0,
        'recent_activity': QuizAttemptSerializer(recent_attempts, many=True).data
    }
    
    return Response({
        'status': 'success',
        'data': data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_progress_view(request):
    """Update user's progress for a topic"""
    topic_id = request.data.get('topic_id')
    time_spent = request.data.get('time_spent', 0)
    
    if not topic_id:
        return Response({
            'status': 'error',
            'message': 'Topic ID is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        topic = Topic.objects.get(id=topic_id)
    except Topic.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Topic not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    progress, created = UserProgress.objects.get_or_create(
        user=request.user,
        topic=topic,
        defaults={'time_spent': time_spent}
    )
    
    if not created:
        progress.time_spent += time_spent
        progress.save()
    
    return Response({
        'status': 'success',
        'data': UserProgressSerializer(progress).data
    })
