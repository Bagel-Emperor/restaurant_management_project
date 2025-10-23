"""
Tests for Restaurant Opening Hours API

Tests the opening hours endpoint to ensure:
- Proper retrieval of opening hours
- Correct response format
- Public access (no authentication required)
- Error handling for missing restaurant
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from home.models import Restaurant


class RestaurantOpeningHoursAPITest(TestCase):
    """Test cases for the restaurant opening hours API endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.url = reverse('opening-hours')
        
        # Create a restaurant with opening hours
        self.restaurant = Restaurant.objects.create(
            name='Perpex Bistro',
            owner_name='John Doe',
            email='contact@perpexbistro.com',
            phone_number='555-0100',
            opening_hours={
                'Monday': '9:00 AM - 10:00 PM',
                'Tuesday': '9:00 AM - 10:00 PM',
                'Wednesday': '9:00 AM - 10:00 PM',
                'Thursday': '9:00 AM - 11:00 PM',
                'Friday': '9:00 AM - 11:00 PM',
                'Saturday': '10:00 AM - 11:00 PM',
                'Sunday': '10:00 AM - 9:00 PM'
            }
        )
    
    def test_get_opening_hours_success(self):
        """Test successfully retrieving opening hours."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('restaurant_name', response.data)
        self.assertIn('opening_hours', response.data)
        self.assertEqual(response.data['restaurant_name'], 'Perpex Bistro')
    
    def test_opening_hours_contains_all_days(self):
        """Test that opening hours contains all 7 days of the week."""
        response = self.client.get(self.url)
        
        opening_hours = response.data['opening_hours']
        expected_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 
                        'Friday', 'Saturday', 'Sunday']
        
        for day in expected_days:
            self.assertIn(day, opening_hours)
    
    def test_opening_hours_format(self):
        """Test that opening hours are properly formatted strings."""
        response = self.client.get(self.url)
        
        opening_hours = response.data['opening_hours']
        
        # Check Monday's format
        self.assertEqual(opening_hours['Monday'], '9:00 AM - 10:00 PM')
        
        # Check that all values are strings
        for day, hours in opening_hours.items():
            self.assertIsInstance(hours, str)
    
    def test_public_access_no_authentication(self):
        """Test that the endpoint is accessible without authentication."""
        # Don't authenticate
        response = self.client.get(self.url)
        
        # Should still work
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_response_structure(self):
        """Test that response has correct structure."""
        response = self.client.get(self.url)
        
        # Should have exactly these two fields
        self.assertEqual(len(response.data), 2)
        self.assertIn('restaurant_name', response.data)
        self.assertIn('opening_hours', response.data)
    
    def test_opening_hours_is_dict(self):
        """Test that opening_hours is returned as a dictionary."""
        response = self.client.get(self.url)
        
        self.assertIsInstance(response.data['opening_hours'], dict)
    
    def test_no_restaurant_returns_404(self):
        """Test that 404 is returned when no restaurant exists."""
        # Delete the restaurant
        Restaurant.objects.all().delete()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # DRF's exception handler returns 'detail' field for Http404
        self.assertIn('detail', response.data)
        self.assertEqual(
            response.data['detail'],
            'Restaurant not found. Please contact support.'
        )
    
    def test_empty_opening_hours(self):
        """Test handling of restaurant with empty opening hours."""
        # Update restaurant with empty opening hours
        self.restaurant.opening_hours = {}
        self.restaurant.save()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['opening_hours'], {})
    
    def test_partial_opening_hours(self):
        """Test restaurant with opening hours for only some days."""
        # Update restaurant with partial opening hours
        partial_hours = {
            'Monday': '9:00 AM - 5:00 PM',
            'Tuesday': '9:00 AM - 5:00 PM',
            'Wednesday': 'Closed'
        }
        self.restaurant.opening_hours = partial_hours
        self.restaurant.save()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['opening_hours'], partial_hours)
    
    def test_get_method_only(self):
        """Test that only GET method is allowed."""
        # Try POST
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Try PUT
        response = self.client.put(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Try DELETE
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # GET should work
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RestaurantOpeningHoursSerializerTest(TestCase):
    """Test cases for the RestaurantOpeningHoursSerializer."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.url = reverse('opening-hours')
        
        self.restaurant = Restaurant.objects.create(
            name='Test Bistro',
            owner_name='Jane Doe',
            email='test@bistro.com',
            phone_number='555-9999',
            opening_hours={
                'Monday': '8:00 AM - 9:00 PM',
                'Friday': '8:00 AM - 11:00 PM'
            }
        )
    
    def test_serializer_includes_restaurant_name(self):
        """Test that serializer includes restaurant name."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.data['restaurant_name'], 'Test Bistro')
    
    def test_serializer_includes_opening_hours(self):
        """Test that serializer includes opening hours."""
        response = self.client.get(self.url)
        
        expected_hours = {
            'Monday': '8:00 AM - 9:00 PM',
            'Friday': '8:00 AM - 11:00 PM'
        }
        self.assertEqual(response.data['opening_hours'], expected_hours)
    
    def test_read_only_fields(self):
        """Test that fields are read-only (no PUT/POST)."""
        # Attempt to POST
        data = {
            'restaurant_name': 'Hacker Restaurant',
            'opening_hours': {'Monday': 'Hacked'}
        }
        response = self.client.post(self.url, data, format='json')
        
        # Should not be allowed
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Original data should remain unchanged
        self.restaurant.refresh_from_db()
        self.assertEqual(self.restaurant.name, 'Test Bistro')


class MultipleRestaurantsTest(TestCase):
    """Test opening hours with multiple restaurants in database."""
    
    def setUp(self):
        """Set up multiple restaurants."""
        self.client = APIClient()
        self.url = reverse('opening-hours')
        
        # Create multiple restaurants
        self.restaurant1 = Restaurant.objects.create(
            name='First Restaurant',
            owner_name='Owner 1',
            email='first@restaurant.com',
            phone_number='555-0001',
            opening_hours={'Monday': '9:00 AM - 5:00 PM'}
        )
        
        self.restaurant2 = Restaurant.objects.create(
            name='Second Restaurant',
            owner_name='Owner 2',
            email='second@restaurant.com',
            phone_number='555-0002',
            opening_hours={'Monday': '10:00 AM - 6:00 PM'}
        )
    
    def test_returns_first_restaurant(self):
        """Test that endpoint returns the first restaurant."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return the first restaurant
        self.assertEqual(response.data['restaurant_name'], 'First Restaurant')
        self.assertEqual(
            response.data['opening_hours']['Monday'], 
            '9:00 AM - 5:00 PM'
        )
