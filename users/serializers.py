"""
Users serializers for FinanceAI
"""
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import UserProfile, UserActivity


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    prediction_accuracy = serializers.ReadOnlyField()
    
    class Meta:
        model = UserProfile
        fields = [
            'risk_appetite', 'experience_level', 'phone', 'avatar',
            'total_predictions', 'correct_predictions', 'prediction_accuracy',
            'learning_progress', 'created_at', 'updated_at'
        ]


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user with profile"""
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']
        read_only_fields = ['id']


def validate_password_strength(value):
    """Require min 8 chars, at least one letter and one number."""
    if len(value) < 8:
        raise serializers.ValidationError('Password must be at least 8 characters.')
    if not any(c.isalpha() for c in value):
        raise serializers.ValidationError('Password must contain at least one letter.')
    if not any(c.isdigit() for c in value):
        raise serializers.ValidationError('Password must contain at least one number.')
    return value


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration with stronger password rules"""
    password = serializers.CharField(write_only=True, min_length=8, validators=[validate_password_strength])
    risk_appetite = serializers.ChoiceField(
        choices=UserProfile.RISK_CHOICES,
        default='moderate'
    )
    experience_level = serializers.ChoiceField(
        choices=UserProfile.EXPERIENCE_CHOICES,
        default='beginner'
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'risk_appetite', 'experience_level']
    
    def create(self, validated_data):
        risk_appetite = validated_data.pop('risk_appetite', 'moderate')
        experience_level = validated_data.pop('experience_level', 'beginner')

        email = (validated_data.get('email') or '').strip().lower()
        if email:
            validated_data['email'] = email

        user = User.objects.create_user(
            username=validated_data['username'],
            email=email or validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        # Signal may have already created profile; use get_or_create and update
        profile, _ = UserProfile.objects.get_or_create(
            user=user,
            defaults={'risk_appetite': risk_appetite, 'experience_level': experience_level}
        )
        if not _:
            profile.risk_appetite = risk_appetite
            profile.experience_level = experience_level
            profile.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class UserActivitySerializer(serializers.ModelSerializer):
    """Serializer for user activities"""
    
    class Meta:
        model = UserActivity
        fields = ['id', 'activity_type', 'description', 'metadata', 'created_at']
        read_only_fields = ['id', 'created_at']


class AuthResponseSerializer(serializers.Serializer):
    """Standard authentication response serializer"""
    status = serializers.CharField()
    data = serializers.DictField()
