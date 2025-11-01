"""
Test cases for the Restaurant Info API endpoint.

This module provides comprehensive test coverage for the /api/restaurant-info/
endpoint, ensuring it correctly returns restaurant information and handles
various scenarios including missing data.
"""

from rest_framework.test import APITestCase
from rest_framework import status
from home.models import Restaurant


class RestaurantInfoAPITest(APITestCase):
    """Test cases for the Restaurant Info API endpoint."""
    
    def setUp(self):
        """Set up test data before each test."""
        # Clear any existing restaurants to ensure clean state
        Restaurant.objects.all().delete()
    
    def test_get_restaurant_info_success(self):
        """Test successful retrieval of restaurant information."""
        # Create a sample restaurant instance
        restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner_name='John Doe',
            email='test@restaurant.com',
            phone_number='555-0100',
            opening_hours={
                'Monday': '9:00 AM - 10:00 PM',
                'Tuesday': '9:00 AM - 10:00 PM',
                'Wednesday': '9:00 AM - 10:00 PM',
                'Thursday': '9:00 AM - 10:00 PM',
                'Friday': '9:00 AM - 11:00 PM',
                'Saturday': '9:00 AM - 11:00 PM',
                'Sunday': 'Closed'
            },
            has_delivery=True
        )
        
        # Make GET request to the restaurant info endpoint
        response = self.client.get('/PerpexBistro/api/restaurant-info/')
        
        # Assert response status is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Assert response structure
        self.assertIn('success', response.data)
        self.assertIn('restaurant', response.data)
        self.assertTrue(response.data['success'])
        
        # Assert restaurant data matches what we created
        restaurant_data = response.data['restaurant']
        self.assertEqual(restaurant_data['name'], 'Test Restaurant')
        self.assertEqual(restaurant_data['owner_name'], 'John Doe')
        self.assertEqual(restaurant_data['email'], 'test@restaurant.com')
        self.assertEqual(restaurant_data['phone_number'], '555-0100')
        self.assertEqual(restaurant_data['has_delivery'], True)
        
        # Assert opening hours are returned correctly
        self.assertIn('opening_hours', restaurant_data)
        self.assertEqual(restaurant_data['opening_hours']['Monday'], '9:00 AM - 10:00 PM')
        self.assertEqual(restaurant_data['opening_hours']['Sunday'], 'Closed')
        
        # Assert id and created_at fields exist
        self.assertIn('id', restaurant_data)
        self.assertIn('created_at', restaurant_data)
        self.assertEqual(restaurant_data['id'], restaurant.id)
    
    def test_get_restaurant_info_no_restaurant_exists(self):
        """Test API response when no restaurant exists in database."""
        # Ensure no restaurant exists (already cleared in setUp)
        self.assertEqual(Restaurant.objects.count(), 0)
        
        # Make GET request
        response = self.client.get('/PerpexBistro/api/restaurant-info/')
        
        # Assert response status is 404 NOT FOUND
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Assert error response structure
        self.assertIn('success', response.data)
        self.assertIn('error', response.data)
        self.assertFalse(response.data['success'])
        self.assertIn('not found', response.data['error'].lower())
    
    def test_get_restaurant_info_returns_first_restaurant(self):
        """Test that API returns the first restaurant when multiple exist."""
        # Create multiple restaurants
        restaurant1 = Restaurant.objects.create(
            name='First Restaurant',
            owner_name='Owner One',
            email='first@restaurant.com',
            phone_number='555-0001'
        )
        restaurant2 = Restaurant.objects.create(
            name='Second Restaurant',
            owner_name='Owner Two',
            email='second@restaurant.com',
            phone_number='555-0002'
        )
        
        # Make GET request
        response = self.client.get('/PerpexBistro/api/restaurant-info/')
        
        # Assert response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Assert it returns the first restaurant
        restaurant_data = response.data['restaurant']
        self.assertEqual(restaurant_data['name'], 'First Restaurant')
        self.assertEqual(restaurant_data['email'], 'first@restaurant.com')
    
    def test_get_restaurant_info_with_empty_opening_hours(self):
        """Test API response when restaurant has empty opening hours."""
        # Create restaurant with empty opening hours
        restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner_name='John Doe',
            email='test@restaurant.com',
            phone_number='555-0100',
            opening_hours={}  # Empty dict
        )
        
        # Make GET request
        response = self.client.get('/PerpexBistro/api/restaurant-info/')
        
        # Assert response is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Assert opening hours is an empty object
        restaurant_data = response.data['restaurant']
        self.assertEqual(restaurant_data['opening_hours'], {})
    
    def test_get_restaurant_info_response_format(self):
        """Test that response follows the expected format."""
        # Create a restaurant
        Restaurant.objects.create(
            name='Perpex Bistro',
            owner_name='Jane Smith',
            email='contact@perpexbistro.com',
            phone_number='555-1234'
        )
        
        # Make GET request
        response = self.client.get('/PerpexBistro/api/restaurant-info/')
        
        # Assert response is JSON
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Assert required top-level keys
        self.assertIn('success', response.data)
        self.assertIn('restaurant', response.data)
        
        # Assert required restaurant fields
        restaurant_data = response.data['restaurant']
        required_fields = ['id', 'name', 'owner_name', 'email', 'phone_number', 
                          'opening_hours', 'has_delivery', 'created_at']
        for field in required_fields:
            self.assertIn(field, restaurant_data, 
                         f"Required field '{field}' missing from response")
    
    def test_get_restaurant_info_only_get_method_allowed(self):
        """Test that the endpoint is decorated with @api_view(['GET'])."""
        # Create a restaurant
        Restaurant.objects.create(
            name='Test Restaurant',
            owner_name='John Doe',
            email='test@restaurant.com',
            phone_number='555-0100'
        )
        
        # GET request should work
        response = self.client.get('/PerpexBistro/api/restaurant-info/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # POST request should not be allowed (returns 405 or 401 depending on auth)
        response = self.client.post('/PerpexBistro/api/restaurant-info/', {})
        self.assertIn(response.status_code, 
                     [status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_401_UNAUTHORIZED])


class RestaurantInfoAPIFieldValidationTest(APITestCase):
    """Test cases for validating specific fields in the Restaurant Info API response."""
    
    def test_has_delivery_field_true(self):
        """Test that has_delivery field returns True when set."""
        Restaurant.objects.create(
            name='Delivery Restaurant',
            owner_name='Owner',
            email='delivery@test.com',
            phone_number='555-0000',
            has_delivery=True
        )
        
        response = self.client.get('/PerpexBistro/api/restaurant-info/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['restaurant']['has_delivery'])
    
    def test_has_delivery_field_false(self):
        """Test that has_delivery field returns False when not set."""
        Restaurant.objects.create(
            name='No Delivery Restaurant',
            owner_name='Owner',
            email='nodelivery@test.com',
            phone_number='555-0000',
            has_delivery=False
        )
        
        response = self.client.get('/PerpexBistro/api/restaurant-info/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['restaurant']['has_delivery'])
    
    def test_opening_hours_format(self):
        """Test that opening hours are returned as a JSON object."""
        Restaurant.objects.create(
            name='Test Restaurant',
            owner_name='Owner',
            email='test@test.com',
            phone_number='555-0000',
            opening_hours={
                'Monday': '9am-5pm',
                'Tuesday': '9am-5pm'
            }
        )
        
        response = self.client.get('/PerpexBistro/api/restaurant-info/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        opening_hours = response.data['restaurant']['opening_hours']
        
        # Assert it's a dictionary
        self.assertIsInstance(opening_hours, dict)
        
        # Assert specific days are present
        self.assertEqual(opening_hours['Monday'], '9am-5pm')
        self.assertEqual(opening_hours['Tuesday'], '9am-5pm')
