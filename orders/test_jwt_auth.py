"""
JWT Authentication Tests for Ride-Sharing Platform

This module provides comprehensive tests for JWT authentication functionality
including token generation, refresh, user login/logout, and protected endpoint access.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import json


class JWTAuthenticationTestCase(APITestCase):
    """
    Test cases for JWT authentication endpoints and functionality.
    """
    
    def setUp(self):
        """
        Set up test data for JWT authentication tests.
        """
        self.client = APIClient()
        
        # Create test users
        self.test_user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword123',
            first_name='Test',
            last_name='User'
        )
        
        self.inactive_user = User.objects.create_user(
            username='inactiveuser',
            email='inactive@example.com',
            password='testpassword123',
            is_active=False
        )
        
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpassword123',
            is_staff=True
        )
        
        # Test data
        self.valid_credentials = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        
        self.invalid_credentials = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        self.inactive_credentials = {
            'username': 'inactiveuser',
            'password': 'testpassword123'
        }

    def test_jwt_token_obtain_success(self):
        """
        Test successful JWT token generation with valid credentials.
        """
        url = '/api/token/'
        response = self.client.post(url, self.valid_credentials, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Test if using custom serializer that includes user data
        if 'user' in response.data:
            user_data = response.data['user']
            self.assertEqual(user_data['username'], 'testuser')
            self.assertEqual(user_data['email'], 'testuser@example.com')
            self.assertEqual(user_data['first_name'], 'Test')
            self.assertEqual(user_data['last_name'], 'User')

    def test_jwt_token_obtain_invalid_credentials(self):
        """
        Test JWT token generation failure with invalid credentials.
        """
        url = '/api/token/'
        response = self.client.post(url, self.invalid_credentials, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('access', response.data)
        self.assertNotIn('refresh', response.data)

    def test_jwt_token_obtain_inactive_user(self):
        """
        Test JWT token generation failure for inactive user.
        """
        url = '/api/token/'
        response = self.client.post(url, self.inactive_credentials, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_jwt_token_refresh_success(self):
        """
        Test successful JWT token refresh with valid refresh token.
        """
        # First get tokens
        url = '/api/token/'
        response = self.client.post(url, self.valid_credentials, format='json')
        refresh_token = response.data['refresh']
        
        # Test token refresh
        refresh_url = '/api/token/refresh/'
        refresh_data = {'refresh': refresh_token}
        refresh_response = self.client.post(refresh_url, refresh_data, format='json')
        
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)

    def test_jwt_token_refresh_invalid_token(self):
        """
        Test JWT token refresh failure with invalid refresh token.
        """
        url = '/api/token/refresh/'
        invalid_data = {'refresh': 'invalid.refresh.token'}
        response = self.client.post(url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_custom_jwt_login_success(self):
        """
        Test successful login using custom JWT login endpoint.
        """
        url = '/PerpexBistro/orders/auth/login/'
        response = self.client.post(url, self.valid_credentials, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertIn('message', response.data)
        
        user_data = response.data['user']
        self.assertEqual(user_data['username'], 'testuser')
        self.assertEqual(user_data['email'], 'testuser@example.com')

    def test_custom_jwt_login_invalid_credentials(self):
        """
        Test custom JWT login failure with invalid credentials.
        """
        url = '/PerpexBistro/orders/auth/login/'
        response = self.client.post(url, self.invalid_credentials, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertIn('message', response.data)

    def test_custom_jwt_login_inactive_user(self):
        """
        Test custom JWT login failure for inactive user.
        """
        url = '/PerpexBistro/orders/auth/login/'
        response = self.client.post(url, self.inactive_credentials, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Account disabled')

    def test_custom_jwt_login_validation_errors(self):
        """
        Test custom JWT login with validation errors.
        """
        url = '/PerpexBistro/orders/auth/login/'
        
        # Test empty username
        invalid_data = {'username': '', 'password': 'testpassword123'}
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test short password
        invalid_data = {'username': 'testuser', 'password': '123'}
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_jwt_logout_success(self):
        """
        Test successful JWT logout with valid refresh token.
        """
        # First login to get tokens
        login_url = '/PerpexBistro/orders/auth/login/'
        login_response = self.client.post(login_url, self.valid_credentials, format='json')
        refresh_token = login_response.data['refresh']
        access_token = login_response.data['access']
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Test logout
        logout_url = '/PerpexBistro/orders/auth/logout/'
        logout_data = {'refresh': refresh_token}
        logout_response = self.client.post(logout_url, logout_data, format='json')
        
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        self.assertIn('message', logout_response.data)

    def test_jwt_logout_missing_token(self):
        """
        Test JWT logout failure with missing refresh token.
        """
        # First login to get access token
        login_url = '/PerpexBistro/orders/auth/login/'
        login_response = self.client.post(login_url, self.valid_credentials, format='json')
        access_token = login_response.data['access']
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Test logout without refresh token
        logout_url = '/PerpexBistro/orders/auth/logout/'
        logout_response = self.client.post(logout_url, {}, format='json')
        
        self.assertEqual(logout_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', logout_response.data)

    def test_jwt_user_profile_success(self):
        """
        Test successful user profile retrieval with valid JWT token.
        """
        # First login to get access token
        login_url = '/PerpexBistro/orders/auth/login/'
        login_response = self.client.post(login_url, self.valid_credentials, format='json')
        access_token = login_response.data['access']
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Test profile retrieval
        profile_url = '/PerpexBistro/orders/auth/profile/'
        profile_response = self.client.get(profile_url)
        
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertIn('user', profile_response.data)
        
        user_data = profile_response.data['user']
        self.assertEqual(user_data['username'], 'testuser')
        self.assertEqual(user_data['email'], 'testuser@example.com')

    def test_jwt_user_profile_unauthorized(self):
        """
        Test user profile retrieval failure without authentication.
        """
        profile_url = '/PerpexBistro/orders/auth/profile/'
        profile_response = self.client.get(profile_url)
        
        self.assertEqual(profile_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_protected_endpoint_with_jwt(self):
        """
        Test accessing protected endpoint with valid JWT token.
        """
        # First login to get access token
        login_url = '/PerpexBistro/orders/auth/login/'
        login_response = self.client.post(login_url, self.valid_credentials, format='json')
        access_token = login_response.data['access']
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Test accessing user order history (protected endpoint)
        orders_url = '/PerpexBistro/orders/orders/history/'
        orders_response = self.client.get(orders_url)
        
        # Should not return 401 unauthorized
        self.assertNotEqual(orders_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_protected_endpoint_without_jwt(self):
        """
        Test accessing protected endpoint without JWT token.
        """
        # Test accessing user order history without authentication
        orders_url = '/PerpexBistro/orders/orders/history/'
        orders_response = self.client.get(orders_url)
        
        # Should return 401 unauthorized
        self.assertEqual(orders_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_jwt_token_expiry_handling(self):
        """
        Test JWT token expiry and refresh functionality.
        """
        # Create a refresh token
        refresh_token = RefreshToken.for_user(self.test_user)
        
        # Test that we can generate an access token
        access_token = refresh_token.access_token
        self.assertIsNotNone(str(access_token))
        
        # Test token refresh endpoint
        refresh_url = '/api/token/refresh/'
        refresh_data = {'refresh': str(refresh_token)}
        refresh_response = self.client.post(refresh_url, refresh_data, format='json')
        
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)

    def test_custom_token_obtain_view(self):
        """
        Test custom token obtain view with enhanced features.
        """
        url = '/PerpexBistro/orders/auth/token/'
        response = self.client.post(url, self.valid_credentials, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Should include user data if using custom serializer
        if 'user' in response.data:
            user_data = response.data['user']
            self.assertEqual(user_data['username'], 'testuser')

    def test_custom_token_refresh_view(self):
        """
        Test custom token refresh view with enhanced error handling.
        """
        # First get tokens
        obtain_url = '/PerpexBistro/orders/auth/token/'
        obtain_response = self.client.post(obtain_url, self.valid_credentials, format='json')
        refresh_token = obtain_response.data['refresh']
        
        # Test custom refresh view
        refresh_url = '/PerpexBistro/orders/auth/token/refresh/'
        refresh_data = {'refresh': refresh_token}
        refresh_response = self.client.post(refresh_url, refresh_data, format='json')
        
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)

    def tearDown(self):
        """
        Clean up after tests.
        """
        User.objects.all().delete()


class JWTIntegrationTestCase(APITestCase):
    """
    Integration tests for JWT authentication with existing endpoints.
    """
    
    def setUp(self):
        """
        Set up test data for integration tests.
        """
        self.client = APIClient()
        self.test_user = User.objects.create_user(
            username='integrationuser',
            email='integration@example.com',
            password='testpassword123'
        )
        
        self.credentials = {
            'username': 'integrationuser',
            'password': 'testpassword123'
        }

    def test_jwt_with_registration_endpoints(self):
        """
        Test that registration endpoints work independently of JWT authentication.
        """
        # Test rider registration without JWT (should work)
        rider_data = {
            'username': 'newrider',
            'email': 'rider@example.com',
            'password': 'newpassword123',
            'first_name': 'New',
            'last_name': 'Rider'
        }
        
        rider_url = '/PerpexBistro/orders/register/rider/'
        rider_response = self.client.post(rider_url, rider_data, format='json')
        
        # Should not require authentication
        self.assertNotEqual(rider_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_jwt_with_existing_token_auth(self):
        """
        Test that JWT authentication works alongside existing token authentication.
        """
        # Login with JWT
        login_url = '/PerpexBistro/orders/auth/login/'
        login_response = self.client.post(login_url, self.credentials, format='json')
        
        if login_response.status_code == 200:
            access_token = login_response.data['access']
            
            # Use JWT token for protected endpoint
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
            
            # Test accessing a protected endpoint
            profile_url = '/PerpexBistro/orders/auth/profile/'
            profile_response = self.client.get(profile_url)
            
            self.assertEqual(profile_response.status_code, status.HTTP_200_OK)

    def tearDown(self):
        """
        Clean up after integration tests.
        """
        User.objects.all().delete()