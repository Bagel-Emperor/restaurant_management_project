"""
Tests for the Restaurant Opening Hours API endpoint.

This module tests the /api/opening-hours/ endpoint which returns
the restaurant's opening hours in a structured format.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from home.models import Restaurant


class RestaurantOpeningHoursAPITests(TestCase):
    """Test suite for Restaurant Opening Hours API endpoint."""
    
    def setUp(self):
        """Set up test client and test data."""
        self.client = APIClient()
        self.url = reverse('opening-hours')
        
        # Create a restaurant with complete opening hours
        self.restaurant = Restaurant.objects.create(
            name='Perpex Bistro',
            owner_name='John Doe',
            email='contact@perpexbistro.com',
            phone_number='555-0123',
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
        """Test successful retrieval of opening hours."""
        response = self.client.get(self.url)
        
        # Assert response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Assert response structure
        self.assertIn('restaurant_name', response.data)
        self.assertIn('opening_hours', response.data)
        
        # Assert restaurant name
        self.assertEqual(response.data['restaurant_name'], 'Perpex Bistro')
        
        # Assert opening hours structure
        opening_hours = response.data['opening_hours']
        self.assertIsInstance(opening_hours, dict)
        
        # Assert all days are present
        expected_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 
                        'Friday', 'Saturday', 'Sunday']
        for day in expected_days:
            self.assertIn(day, opening_hours)
    
    def test_opening_hours_format(self):
        """Test that opening hours are in correct format."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        opening_hours = response.data['opening_hours']
        
        # Verify specific day hours
        self.assertEqual(opening_hours['Monday'], '9:00 AM - 10:00 PM')
        self.assertEqual(opening_hours['Thursday'], '9:00 AM - 11:00 PM')
        self.assertEqual(opening_hours['Sunday'], '10:00 AM - 9:00 PM')
    
    def test_opening_hours_with_closed_days(self):
        """Test opening hours when restaurant is closed on certain days."""
        # Update restaurant to be closed on Sunday
        self.restaurant.opening_hours = {
            'Monday': '9:00 AM - 10:00 PM',
            'Tuesday': '9:00 AM - 10:00 PM',
            'Wednesday': '9:00 AM - 10:00 PM',
            'Thursday': '9:00 AM - 11:00 PM',
            'Friday': '9:00 AM - 11:00 PM',
            'Saturday': '10:00 AM - 11:00 PM',
            'Sunday': 'Closed'
        }
        self.restaurant.save()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['opening_hours']['Sunday'], 'Closed')
    
    def test_opening_hours_with_empty_hours(self):
        """Test API response when restaurant has empty opening hours."""
        # Update restaurant with empty hours
        self.restaurant.opening_hours = {}
        self.restaurant.save()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('opening_hours', response.data)
        self.assertEqual(response.data['opening_hours'], {})
    
    def test_opening_hours_no_authentication_required(self):
        """Test that opening hours endpoint is publicly accessible."""
        # Ensure no authentication is set
        self.client.force_authenticate(user=None)
        
        response = self.client.get(self.url)
        
        # Should still be accessible
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('opening_hours', response.data)
    
    def test_opening_hours_returns_first_restaurant(self):
        """Test that endpoint returns the first restaurant when multiple exist."""
        # Create a second restaurant
        Restaurant.objects.create(
            name='Second Restaurant',
            owner_name='Jane Smith',
            email='contact@secondrestaurant.com',
            phone_number='555-0456',
            opening_hours={'Monday': '8:00 AM - 9:00 PM'}
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return the first restaurant (Perpex Bistro)
        self.assertEqual(response.data['restaurant_name'], 'Perpex Bistro')
    
    def test_opening_hours_404_when_no_restaurant_exists(self):
        """Test that 404 is returned when no restaurant exists in database."""
        # Delete the restaurant
        Restaurant.objects.all().delete()
        
        response = self.client.get(self.url)
        
        # Should return 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_opening_hours_response_structure(self):
        """Test that response has exactly the expected fields."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Assert only expected fields are present
        expected_fields = {'restaurant_name', 'opening_hours'}
        actual_fields = set(response.data.keys())
        
        self.assertEqual(expected_fields, actual_fields)
    
    def test_opening_hours_with_varying_formats(self):
        """Test opening hours with different time formats."""
        # Update with different formats (as they might be stored)
        self.restaurant.opening_hours = {
            'Monday': '9am-10pm',
            'Tuesday': '09:00-22:00',
            'Wednesday': '9:00 AM - 10:00 PM',
            'Thursday': 'Open 24 hours',
            'Friday': '9:00 AM - 11:00 PM',
            'Saturday': '10:00 AM - 11:00 PM',
            'Sunday': 'Closed'
        }
        self.restaurant.save()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        opening_hours = response.data['opening_hours']
        
        # Assert various formats are preserved
        self.assertEqual(opening_hours['Monday'], '9am-10pm')
        self.assertEqual(opening_hours['Tuesday'], '09:00-22:00')
        self.assertEqual(opening_hours['Thursday'], 'Open 24 hours')
        self.assertEqual(opening_hours['Sunday'], 'Closed')
    
    def test_opening_hours_method_not_allowed(self):
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
        
        # Try PATCH
        response = self.client.patch(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_opening_hours_read_only(self):
        """Test that opening hours are read-only."""
        response = self.client.get(self.url)
        original_hours = response.data['opening_hours'].copy()
        
        # Verify data hasn't changed
        response = self.client.get(self.url)
        self.assertEqual(response.data['opening_hours'], original_hours)
    
    def test_opening_hours_with_special_characters(self):
        """Test opening hours with special characters."""
        self.restaurant.opening_hours = {
            'Monday': '9:00 AM - 10:00 PM (EST)',
            'Tuesday': '9:00 AM - 10:00 PM',
            'Wednesday': 'Closed for maintenance',
            'Thursday': '9:00 AM - 11:00 PM',
            'Friday': '9:00 AM - 11:00 PM',
            'Saturday': '10:00 AM - 11:00 PM',
            'Sunday': 'Closed'
        }
        self.restaurant.save()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['opening_hours']['Monday'], 
            '9:00 AM - 10:00 PM (EST)'
        )
        self.assertEqual(
            response.data['opening_hours']['Wednesday'],
            'Closed for maintenance'
        )
    
    def test_opening_hours_json_field_type(self):
        """Test that opening_hours is returned as a dict/JSON object."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify it's a dict, not a string
        opening_hours = response.data['opening_hours']
        self.assertIsInstance(opening_hours, dict)
        self.assertNotIsInstance(opening_hours, str)
    
    def test_opening_hours_restaurant_name_field(self):
        """Test that restaurant_name field is included and correct."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('restaurant_name', response.data)
        self.assertEqual(response.data['restaurant_name'], self.restaurant.name)
    
    def test_opening_hours_with_null_hours(self):
        """Test handling of null opening hours (should not happen but defensive)."""
        # Try to set null (JSONField default prevents this, but test the API)
        self.restaurant.opening_hours = {}
        self.restaurant.save()
        
        response = self.client.get(self.url)
        
        # Should handle gracefully
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data['opening_hours'], dict)
