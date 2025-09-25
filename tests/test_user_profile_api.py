"""
Test cases for UserProfile API endpoints.

This module contains comprehensive tests for:
- UserProfile serializer validation
- UserProfile viewset authentication and authorization
- Profile creation, retrieval, and updates
- Email validation and uniqueness
- Permission enforcement
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from orders.models import UserProfile
from orders.serializers import UserProfileSerializer


class UserProfileSerializerTest(TestCase):
    """Test cases for UserProfileSerializer"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='John',
            last_name='Doe'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            name='John Doe',
            phone='123-456-7890'
        )
    
    def test_serializer_representation(self):
        """Test serializer output includes all expected fields"""
        serializer = UserProfileSerializer(instance=self.profile)
        data = serializer.data
        
        expected_fields = ['id', 'username', 'first_name', 'last_name', 'email', 'name', 'phone', 'full_name']
        for field in expected_fields:
            self.assertIn(field, data)
        
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['first_name'], 'John')
        self.assertEqual(data['last_name'], 'Doe')
        self.assertEqual(data['name'], 'John Doe')
        self.assertEqual(data['phone'], '123-456-7890')
        self.assertEqual(data['full_name'], 'John Doe')
    
    def test_serializer_update_user_fields(self):
        """Test that serializer can update both User and UserProfile fields"""
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@example.com',
            'name': 'Jane Smith',
            'phone': '987-654-3210'
        }
        
        serializer = UserProfileSerializer(instance=self.profile, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_profile = serializer.save()
        
        # Refresh from database
        updated_profile.refresh_from_db()
        updated_profile.user.refresh_from_db()
        
        # Check User fields were updated
        self.assertEqual(updated_profile.user.first_name, 'Jane')
        self.assertEqual(updated_profile.user.last_name, 'Smith')
        self.assertEqual(updated_profile.user.email, 'jane.smith@example.com')
        
        # Check UserProfile fields were updated
        self.assertEqual(updated_profile.name, 'Jane Smith')
        self.assertEqual(updated_profile.phone, '987-654-3210')
    
    def test_email_validation_invalid_format(self):
        """Test email validation rejects invalid email formats"""
        data = {'email': 'invalid-email'}
        serializer = UserProfileSerializer(instance=self.profile, data=data, partial=True)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
    
    def test_email_uniqueness_validation(self):
        """Test email validation prevents duplicate emails"""
        # Create another user with a different email
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com'
        )
        
        # Try to update our profile with the other user's email
        data = {'email': 'other@example.com'}
        serializer = UserProfileSerializer(instance=self.profile, data=data, partial=True)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        self.assertIn('already exists', str(serializer.errors['email'][0]))
    
    def test_partial_update(self):
        """Test partial updates work correctly"""
        data = {'phone': '555-1234'}
        serializer = UserProfileSerializer(instance=self.profile, data=data, partial=True)
        
        self.assertTrue(serializer.is_valid())
        updated_profile = serializer.save()
        
        # Only phone should be updated
        self.assertEqual(updated_profile.phone, '555-1234')
        self.assertEqual(updated_profile.name, 'John Doe')  # Unchanged
        self.assertEqual(updated_profile.user.email, 'test@example.com')  # Unchanged


class UserProfileViewSetTest(TestCase):
    """Test cases for UserProfileViewSet"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        # Create profiles
        self.profile1 = UserProfile.objects.create(
            user=self.user1,
            name='User One',
            phone='111-111-1111'
        )
        self.profile2 = UserProfile.objects.create(
            user=self.user2,
            name='User Two',
            phone='222-222-2222'
        )
        
        # Create tokens for authentication
        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)
        
        # URLs
        self.profile_list_url = reverse('userprofile-list')
        self.profile_detail_url = reverse('userprofile-detail', kwargs={'pk': 1})
        self.profile_me_url = reverse('userprofile-me')
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access profile endpoints"""
        response = self.client.get(self.profile_list_url)
        # Expect 403 because of IsAuthenticated permission in viewset
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
        
        response = self.client.get(self.profile_detail_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
        
        response = self.client.get(self.profile_me_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_authenticated_user_can_access_own_profile(self):
        """Test that authenticated users can access their own profile"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token1.key)
        
        # Test list endpoint (returns user's own profile)
        response = self.client.get(self.profile_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'user1')
        
        # Test me endpoint
        response = self.client.get(self.profile_me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'user1')
    
    def test_user_cannot_access_other_user_profile(self):
        """Test that users cannot access other users' profiles directly"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token1.key)
        
        # The viewset always returns the authenticated user's profile regardless of pk
        response = self.client.get(self.profile_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return user1's profile, not user2's
        self.assertEqual(response.data['username'], 'user1')
    
    def test_profile_update_put(self):
        """Test updating profile with PUT request"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token1.key)
        
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com',
            'name': 'Updated User',
            'phone': '999-999-9999'
        }
        
        response = self.client.put(self.profile_detail_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify updates
        self.profile1.refresh_from_db()
        self.user1.refresh_from_db()
        
        self.assertEqual(self.user1.first_name, 'Updated')
        self.assertEqual(self.user1.last_name, 'Name')
        self.assertEqual(self.user1.email, 'updated@example.com')
        self.assertEqual(self.profile1.name, 'Updated User')
        self.assertEqual(self.profile1.phone, '999-999-9999')
    
    def test_profile_partial_update_patch(self):
        """Test partially updating profile with PATCH request"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token1.key)
        
        update_data = {'phone': '555-5555'}
        
        response = self.client.patch(self.profile_detail_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify only phone was updated
        self.profile1.refresh_from_db()
        self.assertEqual(self.profile1.phone, '555-5555')
        self.assertEqual(self.profile1.name, 'User One')  # Unchanged
    
    def test_profile_auto_creation(self):
        """Test that profile is automatically created if it doesn't exist"""
        # Create a user without a profile
        user_no_profile = User.objects.create_user(
            username='noprofile',
            email='noprofile@example.com',
            password='testpass123'
        )
        token_no_profile = Token.objects.create(user=user_no_profile)
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token_no_profile.key)
        
        response = self.client.get(self.profile_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify profile was created
        self.assertTrue(UserProfile.objects.filter(user=user_no_profile).exists())
    
    def test_invalid_email_update(self):
        """Test that invalid email updates are rejected"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token1.key)
        
        update_data = {'email': 'invalid-email-format'}
        
        response = self.client.patch(self.profile_detail_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_duplicate_email_update(self):
        """Test that duplicate email updates are rejected"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token1.key)
        
        # Try to use user2's email
        update_data = {'email': 'user2@example.com'}
        
        response = self.client.patch(self.profile_detail_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('already exists', str(response.data['email'][0]))
    
    def test_delete_method_not_allowed(self):
        """Test that DELETE method is not allowed"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token1.key)
        
        response = self.client.delete(self.profile_detail_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_post_method_not_allowed(self):
        """Test that POST method is not allowed"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token1.key)
        
        response = self.client.post(self.profile_list_url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_session_authentication(self):
        """Test that session authentication works"""
        # Login using session authentication
        self.client.login(username='user1', password='testpass123')
        
        response = self.client.get(self.profile_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'user1')
    
    def test_response_includes_full_name(self):
        """Test that response includes computed full_name field"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token1.key)
        
        response = self.client.get(self.profile_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('full_name', response.data)
        
        # Update user to have first and last name
        self.user1.first_name = 'John'
        self.user1.last_name = 'Doe'
        self.user1.save()
        
        response = self.client.get(self.profile_list_url)
        self.assertEqual(response.data['full_name'], 'John Doe')


class UserProfileIntegrationTest(TestCase):
    """Integration tests for UserProfile API with real workflows"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
    
    def test_complete_profile_update_workflow(self):
        """Test a complete profile update workflow"""
        profile_list_url = reverse('userprofile-list')
        profile_detail_url = reverse('userprofile-detail', kwargs={'pk': 1})
        
        # 1. Get initial profile (should be auto-created)
        response = self.client.get(profile_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        initial_data = response.data
        
        # 2. Update profile information via detail URL
        update_data = {
            'first_name': 'Integration',
            'last_name': 'Test',
            'email': 'integration.updated@example.com',
            'name': 'Integration Test User',
            'phone': '123-456-7890'
        }
        
        response = self.client.put(profile_detail_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 3. Verify all fields were updated
        updated_data = response.data
        self.assertEqual(updated_data['first_name'], 'Integration')
        self.assertEqual(updated_data['last_name'], 'Test')
        self.assertEqual(updated_data['email'], 'integration.updated@example.com')
        self.assertEqual(updated_data['name'], 'Integration Test User')
        self.assertEqual(updated_data['phone'], '123-456-7890')
        self.assertEqual(updated_data['full_name'], 'Integration Test')
        
        # 4. Verify changes persisted in database
        self.user.refresh_from_db()
        profile = UserProfile.objects.get(user=self.user)
        
        self.assertEqual(self.user.first_name, 'Integration')
        self.assertEqual(self.user.last_name, 'Test')
        self.assertEqual(self.user.email, 'integration.updated@example.com')
        self.assertEqual(profile.name, 'Integration Test User')
        self.assertEqual(profile.phone, '123-456-7890')
    
    def test_me_endpoint_workflow(self):
        """Test the /me/ endpoint workflow"""
        me_url = reverse('userprofile-me')
        profile_detail_url = reverse('userprofile-detail', kwargs={'pk': 1})
        
        # Get profile via /me/ endpoint
        response = self.client.get(me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'integrationuser')
        
        # Update via detail endpoint
        update_data = {'name': 'Updated via API'}
        
        response = self.client.patch(profile_detail_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify change via /me/ endpoint
        response = self.client.get(me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated via API')