"""
Tests for Menu Item Search API Endpoint (Frontend Optimized).

This module tests the frontend-optimized menu search endpoint at /api/menu-search/
which returns lightweight responses containing only essential menu item details
(id, name, image) for search functionality.

This is different from the full MenuItemViewSet search which returns complete
menu item data. This endpoint is specifically designed for frontend search bars
and autocomplete features where minimal data is needed.

Test Coverage:
- Basic search functionality
- Case-insensitive search
- Empty/missing query parameter handling
- Available items filtering
- Image URL handling
- Public access verification
- HTTP method restrictions
"""

import unittest
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from home.models import Restaurant, MenuItem
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io


class MenuItemSearchFrontendAPITest(TestCase):
    """Test suite for frontend-optimized Menu Item Search API endpoint."""
    
    def setUp(self):
        """
        Set up test data before each test.
        Creates a restaurant and multiple menu items for testing.
        """
        self.client = APIClient()
        self.url = '/PerpexBistro/api/menu-search/'
        
        # Create a test restaurant
        self.restaurant = Restaurant.objects.create(
            name='Test Bistro',
            owner_name='Test Owner',
            email='owner@testbistro.com',
            phone_number='555-0100'
        )
        
        # Create menu items with various names
        self.item1 = MenuItem.objects.create(
            name='Margherita Pizza',
            description='Classic Italian pizza',
            price=12.99,
            restaurant=self.restaurant,
            is_available=True
        )
        
        self.item2 = MenuItem.objects.create(
            name='Pepperoni Pizza',
            description='Pizza with pepperoni',
            price=14.99,
            restaurant=self.restaurant,
            is_available=True
        )
        
        self.item3 = MenuItem.objects.create(
            name='Caesar Salad',
            description='Fresh salad with Caesar dressing',
            price=8.99,
            restaurant=self.restaurant,
            is_available=True
        )
        
        self.item4 = MenuItem.objects.create(
            name='Greek Pizza',
            description='Pizza with feta and olives',
            price=13.99,
            restaurant=self.restaurant,
            is_available=False  # Not available
        )
        
        self.item5 = MenuItem.objects.create(
            name='Pasta Carbonara',
            description='Creamy pasta dish',
            price=11.99,
            restaurant=self.restaurant,
            is_available=True
        )
    
    def test_successful_search(self):
        """Test successful search returns matching items."""
        response = self.client.get(self.url, {'q': 'pizza'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        # Should return 2 items (Margherita and Pepperoni, not Greek since it's unavailable)
        self.assertEqual(len(response.data['results']), 2)
        
        # Verify response contains correct fields
        item_names = [item['name'] for item in response.data['results']]
        self.assertIn('Margherita Pizza', item_names)
        self.assertIn('Pepperoni Pizza', item_names)
        self.assertNotIn('Greek Pizza', item_names)  # Unavailable item should not appear
        
        # Verify pagination metadata
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 2)
    
    def test_case_insensitive_search(self):
        """Test that search is case-insensitive."""
        # Test with uppercase
        response1 = self.client.get(self.url, {'q': 'PIZZA'})
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response1.data['results']), 2)
        
        # Test with mixed case
        response2 = self.client.get(self.url, {'q': 'PiZzA'})
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response2.data['results']), 2)
        
        # Test with lowercase
        response3 = self.client.get(self.url, {'q': 'pizza'})
        self.assertEqual(response3.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response3.data['results']), 2)
    
    def test_partial_match_search(self):
        """Test that search matches partial strings."""
        response = self.client.get(self.url, {'q': 'sal'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Caesar Salad')
    
    def test_no_matches_returns_empty_list(self):
        """Test that search with no matches returns empty results."""
        response = self.client.get(self.url, {'q': 'nonexistent'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 0)
        self.assertEqual(response.data['count'], 0)
    
    def test_missing_query_parameter(self):
        """Test that missing 'q' parameter returns 400 error."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('required', response.data['error'].lower())
    
    def test_empty_query_parameter(self):
        """Test that empty 'q' parameter returns 400 error."""
        response = self.client.get(self.url, {'q': ''})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_whitespace_only_query(self):
        """Test that whitespace-only query returns 400 error."""
        response = self.client.get(self.url, {'q': '   '})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_response_structure(self):
        """Test that response has correct structure with required fields."""
        response = self.client.get(self.url, {'q': 'pizza'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check paginated response structure
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        
        self.assertGreater(len(response.data['results']), 0)
        
        # Check first item has required fields
        item = response.data['results'][0]
        self.assertIn('id', item)
        self.assertIn('name', item)
        self.assertIn('image', item)
        
        # Check that only these fields are present (lightweight response)
        self.assertEqual(len(item.keys()), 3)
    
    def test_only_available_items_returned(self):
        """Test that only available items (is_available=True) are returned."""
        # Search for 'pizza' - should not include Greek Pizza (unavailable)
        response = self.client.get(self.url, {'q': 'pizza'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item_names = [item['name'] for item in response.data['results']]
        
        # Available items should be included
        self.assertIn('Margherita Pizza', item_names)
        self.assertIn('Pepperoni Pizza', item_names)
        
        # Unavailable item should not be included
        self.assertNotIn('Greek Pizza', item_names)
    
    def test_public_access_no_authentication(self):
        """Test that endpoint is publicly accessible without authentication."""
        # Make request without authentication
        response = self.client.get(self.url, {'q': 'pasta'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Pasta Carbonara')
    
    def test_image_url_when_image_exists(self):
        """Test that image URL is returned when image exists."""
        # Create a simple test image
        image = Image.new('RGB', (100, 100), color='red')
        image_file = io.BytesIO()
        image.save(image_file, 'JPEG')
        image_file.seek(0)
        
        # Create menu item with image
        item_with_image = MenuItem.objects.create(
            name='Burger with Image',
            description='Delicious burger',
            price=9.99,
            restaurant=self.restaurant,
            is_available=True,
            image=SimpleUploadedFile(
                'burger.jpg',
                image_file.read(),
                content_type='image/jpeg'
            )
        )
        
        response = self.client.get(self.url, {'q': 'burger'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Image URL should not be None
        self.assertIsNotNone(response.data['results'][0]['image'])
        # Check that the URL contains 'burger' and '.jpg' (Django may add suffix)
        self.assertIn('burger', response.data['results'][0]['image'])
        self.assertIn('.jpg', response.data['results'][0]['image'])
    
    def test_image_null_when_no_image(self):
        """Test that image is None when menu item has no image."""
        response = self.client.get(self.url, {'q': 'pizza'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
        
        # Items without images should have None for image field
        for item in response.data['results']:
            self.assertIsNone(item['image'])
    
    def test_search_multiple_words(self):
        """Test search with multiple words."""
        response = self.client.get(self.url, {'q': 'margherita'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Margherita Pizza')
    
    def test_special_characters_in_search(self):
        """Test search handles special characters gracefully."""
        response = self.client.get(self.url, {'q': 'pizza@#$'})
        
        # Should not crash, just return empty results
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
    
    def test_post_method_not_allowed(self):
        """Test that POST method is not allowed."""
        response = self.client.post(self.url, {'q': 'pizza'})
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_put_method_not_allowed(self):
        """Test that PUT method is not allowed."""
        response = self.client.put(self.url, {'q': 'pizza'})
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_delete_method_not_allowed(self):
        """Test that DELETE method is not allowed."""
        response = self.client.delete(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_search_returns_correct_ids(self):
        """Test that returned items have correct database IDs."""
        response = self.client.get(self.url, {'q': 'caesar'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Verify ID matches the created item
        self.assertEqual(response.data['results'][0]['id'], self.item3.id)
        self.assertEqual(response.data['results'][0]['name'], 'Caesar Salad')
    
    def test_error_response_includes_example(self):
        """Test that error response includes usage example."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('example', response.data)
        self.assertIn('q=', response.data['example'])


class MenuItemSearchFrontendIntegrationTest(TestCase):
    """Integration tests for menu search with multiple restaurants."""
    
    def setUp(self):
        """Set up test data with multiple restaurants."""
        self.client = APIClient()
        self.url = '/PerpexBistro/api/menu-search/'
        
        # Create two restaurants
        self.restaurant1 = Restaurant.objects.create(
            name='Italian Bistro',
            owner_name='Owner 1',
            email='owner1@test.com',
            phone_number='555-0001'
        )
        
        self.restaurant2 = Restaurant.objects.create(
            name='Mexican Grill',
            owner_name='Owner 2',
            email='owner2@test.com',
            phone_number='555-0002'
        )
        
        # Create items in both restaurants
        MenuItem.objects.create(
            name='Italian Pizza',
            description='From Italian Bistro',
            price=12.99,
            restaurant=self.restaurant1,
            is_available=True
        )
        
        MenuItem.objects.create(
            name='Mexican Pizza',
            description='From Mexican Grill',
            price=11.99,
            restaurant=self.restaurant2,
            is_available=True
        )
    
    def test_search_across_multiple_restaurants(self):
        """Test that search returns items from all restaurants."""
        response = self.client.get(self.url, {'q': 'pizza'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        item_names = [item['name'] for item in response.data['results']]
        self.assertIn('Italian Pizza', item_names)
        self.assertIn('Mexican Pizza', item_names)
    
    def test_pagination_with_page_size(self):
        """Test that pagination works with custom page_size parameter."""
        # Create additional menu items
        for i in range(10):
            MenuItem.objects.create(
                name=f'Test Item {i}',
                description='Test',
                price=9.99,
                restaurant=self.restaurant1,
                is_available=True
            )
        
        # Request with page_size=5
        response = self.client.get(self.url, {'q': 'test', 'page_size': 5})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        self.assertEqual(response.data['count'], 10)
        self.assertIsNotNone(response.data['next'])  # Should have next page
        self.assertIsNone(response.data['previous'])  # First page, no previous
