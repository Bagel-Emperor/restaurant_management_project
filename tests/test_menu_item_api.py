"""
Django unit tests for the MenuItemViewSet API
Following Django testing best practices instead of custom test scripts
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from home.models import Restaurant, MenuItem
import json


class MenuItemViewSetTestCase(TestCase):
    """Test case for MenuItemViewSet functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create test restaurant
        self.restaurant = Restaurant.objects.create(
            name="Test Restaurant",
            owner_name="Test Owner", 
            email="test@restaurant.com",
            phone_number="555-1234"
        )
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='testuser',
            email='user@test.com', 
            password='testpass123'
        )
        
        # Create test menu item
        self.menu_item = MenuItem.objects.create(
            name="Test Pizza",
            description="A delicious test pizza",
            price=15.99,
            restaurant=self.restaurant,
            is_available=True
        )
        
        self.client = APIClient()
    
    def test_list_menu_items_public_access(self):
        """Test that anyone can list menu items"""
        url = reverse('menuitem-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Test Pizza')
    
    def test_create_menu_item_requires_admin(self):
        """Test that creating menu items requires admin privileges"""
        url = reverse('menuitem-list')
        data = {
            'name': 'New Pizza',
            'description': 'A new pizza',
            'price': 18.99,
            'restaurant': self.restaurant.id,
            'is_available': True
        }
        
        # Test without authentication - should be 401 UNAUTHORIZED (not authenticated)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test with regular user
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test with admin user
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Pizza')
    
    def test_update_menu_item_requires_admin(self):
        """Test that updating menu items requires admin privileges"""
        url = reverse('menuitem-detail', kwargs={'pk': self.menu_item.pk})
        data = {
            'name': 'Updated Pizza',
            'description': 'Updated description',
            'price': 20.99,
            'restaurant': self.restaurant.id,
            'is_available': True
        }
        
        # Test without authentication - should be 401 UNAUTHORIZED (not authenticated)
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test with admin user
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Pizza')
    
    def test_price_validation(self):
        """Test price validation (must be positive)"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('menuitem-list')
        data = {
            'name': 'Invalid Pizza',
            'description': 'Pizza with negative price',
            'price': -5.99,
            'restaurant': self.restaurant.id,
            'is_available': True
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('price', response.data)
        self.assertIn('positive', str(response.data['price'][0]).lower())
    
    def test_name_validation(self):
        """Test name validation (cannot be empty)"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('menuitem-list')
        data = {
            'name': '   ',  # Empty name
            'description': 'Pizza with empty name',
            'price': 15.99,
            'restaurant': self.restaurant.id,
            'is_available': True
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
    
    def test_filter_by_restaurant(self):
        """Test filtering menu items by restaurant"""
        url = reverse('menuitem-list')
        response = self.client.get(url, {'restaurant': self.restaurant.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
    
    def test_invalid_restaurant_filter(self):
        """Test invalid restaurant ID in filter"""
        url = reverse('menuitem-list')
        response = self.client.get(url, {'restaurant': 'invalid'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('restaurant', response.data)
    
    def test_toggle_availability_action(self):
        """Test custom toggle_availability action"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('menuitem-toggle-availability', kwargs={'pk': self.menu_item.pk})
        
        # Item starts as available
        self.assertTrue(self.menu_item.is_available)
        
        # Toggle to unavailable
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('unavailable', response.data['message'])
        
        # Refresh from database
        self.menu_item.refresh_from_db()
        self.assertFalse(self.menu_item.is_available)
    
    def test_delete_menu_item_requires_admin(self):
        """Test that deleting menu items requires admin privileges"""
        url = reverse('menuitem-detail', kwargs={'pk': self.menu_item.pk})
        
        # Test without authentication - should be 401 UNAUTHORIZED (not authenticated)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test with admin user
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify item is deleted
        self.assertFalse(MenuItem.objects.filter(pk=self.menu_item.pk).exists())