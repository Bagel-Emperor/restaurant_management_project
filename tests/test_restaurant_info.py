"""
Test suite for restaurant-info API endpoint.
Tests retrieval of comprehensive restaurant information.
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from home.models import Restaurant, RestaurantLocation


class RestaurantInfoAPITestCase(TestCase):
    """Test cases for the restaurant-info endpoint."""
    
    def setUp(self):
        """Set up test data."""
        # Create test restaurant
        self.restaurant = Restaurant.objects.create(
            name='Perpex Bistro',
            owner_name='John Doe',
            email='contact@perpexbistro.com',
            phone_number='555-0100',
            opening_hours={
                'Monday': '9:00 AM - 10:00 PM',
                'Tuesday': '9:00 AM - 10:00 PM',
                'Wednesday': '9:00 AM - 10:00 PM',
                'Thursday': '9:00 AM - 10:00 PM',
                'Friday': '9:00 AM - 11:00 PM',
                'Saturday': '10:00 AM - 11:00 PM',
                'Sunday': '10:00 AM - 9:00 PM'
            }
        )
        
        # Create location for the restaurant
        self.location = RestaurantLocation.objects.create(
            restaurant=self.restaurant,
            address='123 Main Street',
            city='New York',
            state='NY',
            zip_code='10001'
        )
        
        # Set up API client
        self.client = APIClient()
        self.url = reverse('restaurant-info')
    
    def test_get_restaurant_info_success(self):
        """Test successful retrieval of restaurant information."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('restaurant', response.data)
    
    def test_restaurant_info_has_all_fields(self):
        """Test that response includes all expected fields."""
        response = self.client.get(self.url)
        restaurant_data = response.data['restaurant']
        
        # Check all required fields are present
        expected_fields = [
            'id', 'name', 'owner_name', 'email', 'phone_number',
            'opening_hours', 'address', 'city', 'state', 'zip_code',
            'full_address', 'created_at'
        ]
        
        for field in expected_fields:
            self.assertIn(field, restaurant_data, f"Field '{field}' missing from response")
    
    def test_restaurant_info_correct_values(self):
        """Test that response contains correct values."""
        response = self.client.get(self.url)
        restaurant_data = response.data['restaurant']
        
        self.assertEqual(restaurant_data['name'], 'Perpex Bistro')
        self.assertEqual(restaurant_data['owner_name'], 'John Doe')
        self.assertEqual(restaurant_data['email'], 'contact@perpexbistro.com')
        self.assertEqual(restaurant_data['phone_number'], '555-0100')
        self.assertEqual(restaurant_data['address'], '123 Main Street')
        self.assertEqual(restaurant_data['city'], 'New York')
        self.assertEqual(restaurant_data['state'], 'NY')
        self.assertEqual(restaurant_data['zip_code'], '10001')
    
    def test_restaurant_info_full_address_format(self):
        """Test that full_address is properly formatted."""
        response = self.client.get(self.url)
        restaurant_data = response.data['restaurant']
        
        expected_address = '123 Main Street, New York, NY 10001'
        self.assertEqual(restaurant_data['full_address'], expected_address)
    
    def test_restaurant_info_opening_hours(self):
        """Test that opening_hours is included and correct."""
        response = self.client.get(self.url)
        restaurant_data = response.data['restaurant']
        
        self.assertIn('opening_hours', restaurant_data)
        opening_hours = restaurant_data['opening_hours']
        
        # Check it's a dictionary
        self.assertIsInstance(opening_hours, dict)
        
        # Check specific days
        self.assertEqual(opening_hours['Monday'], '9:00 AM - 10:00 PM')
        self.assertEqual(opening_hours['Friday'], '9:00 AM - 11:00 PM')
        self.assertEqual(opening_hours['Sunday'], '10:00 AM - 9:00 PM')
    
    def test_restaurant_info_without_location(self):
        """Test response when restaurant has no location."""
        # Delete the location
        self.location.delete()
        
        response = self.client.get(self.url)
        restaurant_data = response.data['restaurant']
        
        # Location fields should be None
        self.assertIsNone(restaurant_data['address'])
        self.assertIsNone(restaurant_data['city'])
        self.assertIsNone(restaurant_data['state'])
        self.assertIsNone(restaurant_data['zip_code'])
        self.assertIsNone(restaurant_data['full_address'])
        
        # Other fields should still be present
        self.assertEqual(restaurant_data['name'], 'Perpex Bistro')
        self.assertEqual(restaurant_data['phone_number'], '555-0100')
    
    def test_restaurant_info_no_restaurant_exists(self):
        """Test response when no restaurant exists in database."""
        # Delete all restaurants
        Restaurant.objects.all().delete()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('error', response.data)
        self.assertIn('not found', response.data['error'].lower())
    
    def test_restaurant_info_public_access(self):
        """Test that endpoint is publicly accessible (no auth required)."""
        # No authentication
        response = self.client.get(self.url)
        
        # Should succeed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_restaurant_info_multiple_restaurants(self):
        """Test that endpoint returns first restaurant when multiple exist."""
        # Create another restaurant
        Restaurant.objects.create(
            name='Another Restaurant',
            owner_name='Jane Smith',
            email='contact@another.com',
            phone_number='555-0200',
            opening_hours={}
        )
        
        response = self.client.get(self.url)
        restaurant_data = response.data['restaurant']
        
        # Should return the first restaurant (Perpex Bistro)
        self.assertEqual(restaurant_data['name'], 'Perpex Bistro')
    
    def test_restaurant_info_response_structure(self):
        """Test that response has correct structure."""
        response = self.client.get(self.url)
        
        # Check top-level structure
        self.assertIn('success', response.data)
        self.assertIn('restaurant', response.data)
        self.assertIsInstance(response.data['success'], bool)
        self.assertIsInstance(response.data['restaurant'], dict)
    
    def test_restaurant_info_empty_opening_hours(self):
        """Test response when opening_hours is empty dict."""
        self.restaurant.opening_hours = {}
        self.restaurant.save()
        
        response = self.client.get(self.url)
        restaurant_data = response.data['restaurant']
        
        self.assertEqual(restaurant_data['opening_hours'], {})
    
    def test_restaurant_info_json_format(self):
        """Test that response is valid JSON."""
        response = self.client.get(self.url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
    
    def test_restaurant_info_multiple_requests(self):
        """Test that multiple requests return consistent data."""
        response1 = self.client.get(self.url)
        response2 = self.client.get(self.url)
        
        self.assertEqual(response1.data, response2.data)
    
    def test_restaurant_info_id_field(self):
        """Test that id field is included and correct."""
        response = self.client.get(self.url)
        restaurant_data = response.data['restaurant']
        
        self.assertEqual(restaurant_data['id'], self.restaurant.id)
    
    def test_restaurant_info_created_at_field(self):
        """Test that created_at field is included."""
        response = self.client.get(self.url)
        restaurant_data = response.data['restaurant']
        
        self.assertIn('created_at', restaurant_data)
        self.assertIsNotNone(restaurant_data['created_at'])
