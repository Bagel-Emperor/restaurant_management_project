"""
Tests for the Menu Item Availability Check API endpoint.

This module tests the MenuItemAvailabilityView which provides a lightweight
endpoint for checking menu item availability status without returning full item data.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from home.models import Restaurant, MenuItem, MenuCategory


class MenuItemAvailabilityAPITests(TestCase):
    """Test cases for the menu item availability check API endpoint."""
    
    def setUp(self):
        """Set up test data for availability API tests."""
        self.client = APIClient()
        
        # Create restaurant
        self.restaurant = Restaurant.objects.create(
            owner_name='Test Restaurant Owner',
            email='owner@testrestaurant.com',
            phone_number='555-1234'
        )
        
        # Create category
        self.category = MenuCategory.objects.create(
            name='Main Dishes',
            description='Delicious main course options'
        )
        
        # Create available menu item
        self.available_item = MenuItem.objects.create(
            name='Pepperoni Pizza',
            description='Classic pizza with pepperoni',
            price='15.99',
            restaurant=self.restaurant,
            category=self.category,
            is_available=True
        )
        
        # Create unavailable menu item
        self.unavailable_item = MenuItem.objects.create(
            name='Seasonal Soup',
            description='Special seasonal soup (out of season)',
            price='8.99',
            restaurant=self.restaurant,
            category=self.category,
            is_available=False
        )
    
    def test_check_available_item(self):
        """Test checking availability of an available menu item."""
        url = reverse('menuitem-availability', kwargs={'pk': self.available_item.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify response structure
        self.assertIn('id', response.data)
        self.assertIn('name', response.data)
        self.assertIn('available', response.data)
        
        # Verify values
        self.assertEqual(response.data['id'], self.available_item.id)
        self.assertEqual(response.data['name'], 'Pepperoni Pizza')
        self.assertTrue(response.data['available'])
    
    def test_check_unavailable_item(self):
        """Test checking availability of an unavailable menu item."""
        url = reverse('menuitem-availability', kwargs={'pk': self.unavailable_item.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify response structure
        self.assertIn('id', response.data)
        self.assertIn('name', response.data)
        self.assertIn('available', response.data)
        
        # Verify values
        self.assertEqual(response.data['id'], self.unavailable_item.id)
        self.assertEqual(response.data['name'], 'Seasonal Soup')
        self.assertFalse(response.data['available'])
    
    def test_nonexistent_menu_item(self):
        """Test checking availability of a non-existent menu item."""
        url = reverse('menuitem-availability', kwargs={'pk': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', response.data)
    
    def test_public_access(self):
        """Test that the endpoint is publicly accessible without authentication."""
        # Explicitly ensure no authentication
        self.client.force_authenticate(user=None)
        
        url = reverse('menuitem-availability', kwargs={'pk': self.available_item.id})
        response = self.client.get(url)
        
        # Should still be accessible
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['available'])
    
    def test_response_only_has_required_fields(self):
        """Test that response contains only id, name, and available fields."""
        url = reverse('menuitem-availability', kwargs={'pk': self.available_item.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should have exactly 3 fields
        self.assertEqual(len(response.data), 3)
        self.assertIn('id', response.data)
        self.assertIn('name', response.data)
        self.assertIn('available', response.data)
        
        # Should NOT include full menu item fields
        self.assertNotIn('description', response.data)
        self.assertNotIn('price', response.data)
        self.assertNotIn('restaurant', response.data)
        self.assertNotIn('category', response.data)
    
    def test_available_field_is_boolean(self):
        """Test that the available field is returned as a boolean."""
        url = reverse('menuitem-availability', kwargs={'pk': self.available_item.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data['available'], bool)
        self.assertTrue(response.data['available'])
        
        # Test with unavailable item
        url = reverse('menuitem-availability', kwargs={'pk': self.unavailable_item.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data['available'], bool)
        self.assertFalse(response.data['available'])
    
    def test_only_get_method_allowed(self):
        """Test that only GET method is allowed."""
        url = reverse('menuitem-availability', kwargs={'pk': self.available_item.id})
        
        # GET should work
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # POST should not be allowed
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # PUT should not be allowed
        response = self.client.put(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # PATCH should not be allowed
        response = self.client.patch(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # DELETE should not be allowed
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_multiple_items_availability(self):
        """Test checking availability for multiple menu items."""
        # Create additional items with different availability
        item3 = MenuItem.objects.create(
            name='Caesar Salad',
            price='10.99',
            restaurant=self.restaurant,
            category=self.category,
            is_available=True
        )
        
        item4 = MenuItem.objects.create(
            name='Lobster Special',
            price='35.99',
            restaurant=self.restaurant,
            category=self.category,
            is_available=False
        )
        
        # Check each item
        items_to_check = [
            (self.available_item.id, True),
            (self.unavailable_item.id, False),
            (item3.id, True),
            (item4.id, False),
        ]
        
        for item_id, expected_availability in items_to_check:
            url = reverse('menuitem-availability', kwargs={'pk': item_id})
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['available'], expected_availability)
    
    def test_invalid_id_format(self):
        """Test handling of invalid ID format (non-numeric)."""
        # Django URL routing will catch this, but test the behavior
        url = '/api/menu-items/invalid/check-availability/'
        response = self.client.get(url)
        
        # Should return 404 as the URL won't match
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_zero_id(self):
        """Test checking availability with ID of 0."""
        url = reverse('menuitem-availability', kwargs={'pk': 0})
        response = self.client.get(url)
        
        # Should return 404 as ID 0 doesn't exist
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_negative_id(self):
        """Test checking availability with negative ID."""
        # Django URL pattern doesn't accept negative numbers, so manually construct URL
        url = '/api/menu-items/-1/check-availability/'
        response = self.client.get(url)
        
        # Should return 404 as the URL pattern won't match
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_response_content_type(self):
        """Test that response content type is JSON."""
        url = reverse('menuitem-availability', kwargs={'pk': self.available_item.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
    
    def test_availability_reflects_database_state(self):
        """Test that availability check reflects current database state."""
        # Initially available
        url = reverse('menuitem-availability', kwargs={'pk': self.available_item.id})
        response = self.client.get(url)
        self.assertTrue(response.data['available'])
        
        # Change to unavailable
        self.available_item.is_available = False
        self.available_item.save()
        
        # Check again
        response = self.client.get(url)
        self.assertFalse(response.data['available'])
        
        # Change back to available
        self.available_item.is_available = True
        self.available_item.save()
        
        # Check again
        response = self.client.get(url)
        self.assertTrue(response.data['available'])
    
    def test_id_field_matches_request(self):
        """Test that returned ID matches the requested ID."""
        url = reverse('menuitem-availability', kwargs={'pk': self.available_item.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.available_item.id)
    
    def test_name_field_accuracy(self):
        """Test that returned name matches the menu item name."""
        url = reverse('menuitem-availability', kwargs={'pk': self.available_item.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Pepperoni Pizza')
        
        # Test with unavailable item
        url = reverse('menuitem-availability', kwargs={'pk': self.unavailable_item.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Seasonal Soup')
    
    def test_concurrent_availability_checks(self):
        """Test multiple concurrent availability checks."""
        # Simulate multiple clients checking availability simultaneously
        urls = [
            reverse('menuitem-availability', kwargs={'pk': self.available_item.id}),
            reverse('menuitem-availability', kwargs={'pk': self.unavailable_item.id}),
            reverse('menuitem-availability', kwargs={'pk': self.available_item.id}),
        ]
        
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('available', response.data)
