"""
Users views for FinanceAI
"""
import re
import secrets
from datetime import timedelta
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserProfile, UserActivity, WalletAddress, WalletLoginNonce
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    UserProfileSerializer,
    UserActivitySerializer
)


def get_tokens_for_user(user):
    """Generate JWT tokens for user"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def normalize_address(addr):
    """Normalize Ethereum address to lowercase for comparison."""
    if not addr:
        return ""
    return addr.lower().strip()


# ----- Web3 wallet auth -----

# Nonce valid for 5 minutes; one-time use (deleted after successful verify).
WALLET_NONCE_VALID_SECONDS = 300

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([])  # Do not throttle wallet nonce requests (handled by one-time, time-bound nonce)
def wallet_nonce_view(request):
    """Return a fresh one-time nonce for the given wallet address (sign-in challenge)."""
    address = request.query_params.get('address')
    address = normalize_address(address)
    if not address or len(address) != 42 or not address.startswith('0x'):
        return Response(
            {'status': 'error', 'message': 'Valid Ethereum address required (0x...).'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    nonce = f"FinanceAI sign-in: {secrets.token_hex(24)}"
    WalletLoginNonce.objects.update_or_create(
        address=address,
        defaults={'nonce': nonce},
    )
    return Response({'status': 'success', 'data': {'nonce': nonce}})


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([])  # Do not throttle wallet verify (protected by signature + nonce)
def wallet_verify_view(request):
    """Verify wallet signature and return JWT tokens (create or get user)."""
    address = request.data.get('address')
    signature = request.data.get('signature')
    address = normalize_address(address)
    if not address or len(address) != 42 or not address.startswith('0x'):
        return Response(
            {'status': 'error', 'message': 'Valid Ethereum address required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not signature or not isinstance(signature, str):
        return Response(
            {'status': 'error', 'message': 'Signature required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        from eth_account import Account
        from eth_account.messages import encode_defunct
    except ImportError:
        return Response(
            {'status': 'error', 'message': 'Wallet auth not configured.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    try:
        nonce_row = WalletLoginNonce.objects.get(address=address)
        nonce = nonce_row.nonce
        # Reject expired nonces (one-time use, time-bound).
        if timezone.now() - nonce_row.created_at > timedelta(seconds=WALLET_NONCE_VALID_SECONDS):
            nonce_row.delete()
            return Response(
                {'status': 'error', 'message': 'Sign-in challenge expired. Please connect again.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except WalletLoginNonce.DoesNotExist:
        return Response(
            {'status': 'error', 'message': 'Request a nonce first (GET /api/auth/wallet/nonce/).'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    message = encode_defunct(text=nonce)
    try:
        recovered = Account.recover_message(message, signature=signature)
        recovered = normalize_address(recovered)
    except Exception:
        return Response(
            {'status': 'error', 'message': 'Invalid signature.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    if recovered != address:
        return Response(
            {'status': 'error', 'message': 'Signature does not match address.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    # One-time use: delete nonce so it cannot be replayed.
    nonce_row.delete()
    # Get or create user for this wallet (allow first-time sign-in).
    try:
        wallet = WalletAddress.objects.get(address=address)
        user = wallet.user
    except WalletAddress.DoesNotExist:
        # First-time wallet sign-in: create user and link wallet.
        username = f"wallet_{address[2:12]}_{address[-6:]}"
        if User.objects.filter(username=username).exists():
            username = f"wallet_{address[2:].lower()}"  # fallback: use full address sans 0x
        user = User.objects.create_user(
            username=username,
            email=f"{address.lower()}@wallet.local",
            password=User.objects.make_random_password(length=64),
            first_name="",
            last_name="",
        )
        UserProfile.objects.get_or_create(user=user, defaults={"risk_appetite": "moderate", "experience_level": "beginner"})
        WalletAddress.objects.create(user=user, address=address)
    tokens = get_tokens_for_user(user)
    UserActivity.objects.create(user=user, activity_type='login', description='Wallet sign-in')
    needs_username = user.username.startswith('wallet_')
    return Response({
        'status': 'success',
        'data': {
            'access': tokens['access'],
            'refresh': tokens['refresh'],
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'name': user.get_full_name() or user.username,
                'wallet_address': address,
            },
            'needs_username': needs_username,
        },
    })


@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(generics.CreateAPIView):
    """User registration view - always returns JSON."""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    throttle_classes = []  # Disable global anon throttling for registration

    def create(self, request, *args, **kwargs):
        def json_error(message, status_code=status.HTTP_400_BAD_REQUEST, errors=None):
            return Response(
                {'status': 'error', 'message': message, **({'errors': errors} if errors else {})},
                status=status_code,
                content_type='application/json',
            )

        try:
            data = request.data.copy()
            base_username = data.get('username')
            if not base_username:
                email = data.get('email') or ''
                base_username = (email.split('@')[0] or 'user').strip() or 'user'
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            data['username'] = username

            serializer = self.get_serializer(data=data)
            try:
                serializer.is_valid(raise_exception=True)
            except ValidationError as exc:
                errors = exc.detail
                first_msg = None
                if isinstance(errors, dict):
                    for field_errors in errors.values():
                        if isinstance(field_errors, (list, tuple)) and field_errors:
                            first_msg = str(field_errors[0])
                            break
                if not first_msg:
                    first_msg = 'Registration failed.'
                return json_error(first_msg, status.HTTP_400_BAD_REQUEST, errors=errors)

            user = serializer.save()
            user.refresh_from_db()

            tokens = get_tokens_for_user(user)

            UserActivity.objects.create(
                user=user,
                activity_type='login',
                description='User registered and logged in'
            )

            user_data = UserSerializer(user).data
            return Response(
                {
                    'status': 'success',
                    'data': {
                        'access': tokens['access'],
                        'refresh': tokens['refresh'],
                        'user': user_data,
                    }
                },
                status=status.HTTP_201_CREATED,
                content_type='application/json',
            )
        except Exception as e:
            msg = 'Registration failed. Please try again.'
            if hasattr(e, 'messages') and e.messages:
                msg = e.messages[0] if isinstance(e.messages[0], str) else str(e.messages[0])
            elif str(e):
                msg = str(e)
            return json_error(msg, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(generics.GenericAPIView):
    """User login view"""
    permission_classes = [AllowAny]
    throttle_classes = []  # Disable global anon throttling for login
    
    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        password = request.data.get('password')

        if not email or not password:
            return Response({
                'status': 'error',
                'message': 'Email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST, content_type='application/json')

        # Find user by email (case-insensitive)
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED, content_type='application/json')

        # Authenticate
        user = authenticate(username=user.username, password=password)

        if user is None:
            return Response({
                'status': 'error',
                'message': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED, content_type='application/json')

        tokens = get_tokens_for_user(user)

        # Log activity
        UserActivity.objects.create(
            user=user,
            activity_type='login',
            description='User logged in'
        )

        return Response({
            'status': 'success',
            'data': {
                'access': tokens['access'],
                'refresh': tokens['refresh'],
                'user': UserSerializer(user).data
            }
        }, content_type='application/json')


class ProfileView(generics.RetrieveUpdateAPIView):
    """User profile view"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        return Response({
            'status': 'success',
            'data': UserSerializer(user).data
        })
    
    def update(self, request, *args, **kwargs):
        user = self.get_object()

        # Update username if provided (e.g. wallet user setting display name)
        new_username = request.data.get('username')
        if new_username is not None:
            new_username = (new_username or '').strip()
            if len(new_username) < 3:
                return Response(
                    {'status': 'error', 'message': 'Username must be at least 3 characters.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if len(new_username) > 30:
                return Response(
                    {'status': 'error', 'message': 'Username must be 30 characters or fewer.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not re.match(r'^[a-zA-Z0-9_]+$', new_username):
                return Response(
                    {'status': 'error', 'message': 'Username can only contain letters, numbers, and underscores.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
                return Response(
                    {'status': 'error', 'message': 'This username is already taken.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.username = new_username

        # Update other user fields
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.email = request.data.get('email', user.email)
        user.save()

        # Update profile fields
        profile_data = request.data.get('profile', {})
        if profile_data:
            profile = user.profile
            profile.risk_appetite = profile_data.get('risk_appetite', profile.risk_appetite)
            profile.experience_level = profile_data.get('experience_level', profile.experience_level)
            profile.phone = profile_data.get('phone', profile.phone)
            profile.save()

        return Response({
            'status': 'success',
            'data': UserSerializer(user).data
        })


class UserActivityListView(generics.ListAPIView):
    """List user activities"""
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserActivity.objects.filter(user=self.request.user)[:50]
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Logout view - blacklist refresh token"""
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        # Log activity
        UserActivity.objects.create(
            user=request.user,
            activity_type='logout',
            description='User logged out'
        )
        
        return Response({
            'status': 'success',
            'message': 'Successfully logged out'
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_stats_view(request):
    """Get user statistics"""
    user = request.user
    profile = user.profile
    
    return Response({
        'status': 'success',
        'data': {
            'total_predictions': profile.total_predictions,
            'correct_predictions': profile.correct_predictions,
            'prediction_accuracy': profile.prediction_accuracy,
            'learning_progress': profile.learning_progress,
            'risk_appetite': profile.risk_appetite,
            'experience_level': profile.experience_level
        }
    })
