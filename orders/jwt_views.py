"""
JWT Authentication Views for Ride-Sharing Platform

This module provides custom JWT authentication views with enhanced
error handling, logging, and user experience features.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
import logging

from .jwt_serializers import CustomTokenObtainPairSerializer, UserLoginSerializer

# Configure logging
logger = logging.getLogger(__name__)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token obtain view with enhanced error handling and logging.
    
    Provides JWT tokens with additional user information and proper
    error responses for failed authentication attempts.
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        """
        Handle POST request for token generation.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: JWT tokens with user data or error message
        """
        try:
            response = super().post(request, *args, **kwargs)
            
            if response.status_code == 200:
                logger.info(
                    f"Successful JWT login for user: {request.data.get('username', 'Unknown')}"
                )
            
            return response
            
        except Exception as e:
            logger.error(f"JWT token generation failed: {str(e)}")
            return Response({
                'error': 'Authentication failed',
                'message': 'Invalid credentials provided'
            }, status=status.HTTP_401_UNAUTHORIZED)


class CustomTokenRefreshView(TokenRefreshView):
    """
    Custom JWT token refresh view with enhanced error handling.
    
    Provides token refresh functionality with proper error responses
    for invalid or expired refresh tokens.
    """
    
    def post(self, request, *args, **kwargs):
        """
        Handle POST request for token refresh.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: New access token or error message
        """
        try:
            response = super().post(request, *args, **kwargs)
            
            if response.status_code == 200:
                logger.info("Successful JWT token refresh")
            
            return response
            
        except TokenError as e:
            logger.warning(f"Token refresh failed: {str(e)}")
            return Response({
                'error': 'Token refresh failed',
                'message': 'Invalid or expired refresh token'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {str(e)}")
            return Response({
                'error': 'Token refresh failed',
                'message': 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def jwt_login(request):
    """
    Custom JWT login endpoint with detailed validation.
    
    Args:
        request: HTTP request with username and password
        
    Returns:
        Response: JWT tokens with user data or detailed error messages
    """
    try:
        serializer = UserLoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'error': 'Validation failed',
                'message': 'Invalid input data',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        
        if user is None:
            logger.warning(f"Failed login attempt for username: {username}")
            return Response({
                'error': 'Authentication failed',
                'message': 'Invalid username or password'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {username}")
            return Response({
                'error': 'Account disabled',
                'message': 'Your account has been disabled. Please contact support.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        # Add custom claims
        access_token['username'] = user.username
        access_token['email'] = user.email
        access_token['first_name'] = user.first_name
        access_token['last_name'] = user.last_name
        access_token['is_staff'] = user.is_staff
        
        logger.info(f"Successful JWT login for user: {username}")
        
        return Response({
            'access': str(access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'is_active': user.is_active,
                'date_joined': user.date_joined,
                'last_login': user.last_login,
            },
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Unexpected error during JWT login: {str(e)}")
        return Response({
            'error': 'Login failed',
            'message': 'An unexpected error occurred during login'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def jwt_logout(request):
    """
    JWT logout endpoint that blacklists the refresh token.
    
    Args:
        request: HTTP request with refresh token
        
    Returns:
        Response: Success message or error
    """
    try:
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response({
                'error': 'Missing token',
                'message': 'Refresh token is required for logout'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            logger.info(f"Successful JWT logout for user: {request.user.username}")
            
            return Response({
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
            
        except TokenError:
            return Response({
                'error': 'Invalid token',
                'message': 'Invalid or expired refresh token'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Unexpected error during JWT logout: {str(e)}")
        return Response({
            'error': 'Logout failed',
            'message': 'An unexpected error occurred during logout'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def jwt_user_profile(request):
    """
    Get current user profile information from JWT token.
    
    Args:
        request: HTTP request with JWT token
        
    Returns:
        Response: User profile data
    """
    try:
        user = request.user
        
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'is_active': user.is_active,
                'date_joined': user.date_joined,
                'last_login': user.last_login,
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error retrieving user profile: {str(e)}")
        return Response({
            'error': 'Profile retrieval failed',
            'message': 'Unable to retrieve user profile'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)