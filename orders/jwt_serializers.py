"""
JWT Authentication Serializers for Ride-Sharing Platform

This module provides custom JWT serializers that extend the default
simplejwt serializers to include additional user information in the
authentication response.
"""

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth.models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer that includes additional user information
    in the token response.
    
    Extends the default TokenObtainPairSerializer to include:
    - User profile information (first_name, last_name, email)
    - User type information (is_staff, is_superuser)
    - Account status (is_active)
    """
    
    def validate(self, attrs):
        """
        Validate credentials and return tokens with additional user data.
        
        Args:
            attrs (dict): Username/password credentials
            
        Returns:
            dict: Token data with additional user information
        """
        data = super().validate(attrs)
        
        # Add user information to the response
        user = self.user
        data.update({
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
        })
        
        return data

    @classmethod
    def get_token(cls, user):
        """
        Generate token with custom claims.
        
        Args:
            user: User instance
            
        Returns:
            Token with custom claims
        """
        token = super().get_token(user)
        
        # Add custom claims to the token
        token['username'] = user.username
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['is_staff'] = user.is_staff
        
        return token


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login validation.
    
    Provides additional validation for login credentials
    with detailed error messages.
    """
    
    username = serializers.CharField(
        max_length=150,
        help_text="Username for authentication"
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="Password for authentication"
    )
    
    def validate_username(self, value):
        """
        Validate username field.
        
        Args:
            value (str): Username value
            
        Returns:
            str: Validated username
            
        Raises:
            ValidationError: If username is invalid
        """
        if not value.strip():
            raise serializers.ValidationError("Username cannot be empty.")
        
        return value.strip()
    
    def validate_password(self, value):
        """
        Validate password field.
        
        Args:
            value (str): Password value
            
        Returns:
            str: Validated password
            
        Raises:
            ValidationError: If password is invalid
        """
        if not value:
            raise serializers.ValidationError("Password cannot be empty.")
        
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long."
            )
        
        return value