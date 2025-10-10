"""
Django TestCase for Daily Specials API endpoint.

This test suite uses Django's TestCase class with proper database transactions
to ensure test isolation and avoid side effects on existing database records.

Tests:
1. API endpoint returns correct HTTP status
2. Filtering works correctly (only daily specials with is_daily_special=True)
3. Availability filtering (only is_available=True items)
4. Response format matches DailySpecialSerializer
5. Public access without authentication
"""

from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
import json

from home.models import MenuItem, MenuCategory, Restaurant


class DailySpecialsAPITestCase(TestCase):
    """
    Test case for Daily Specials API endpoint.
    Uses Django TestCase with automatic database rollback after each test.
    """
    
    @classmethod
    def setUpTestData(cls):
        """
        Set up test data once for all test methods.
        This data is not modified during tests, so it's created once.
        """
        # Create test restaurant
        cls.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner_name='Test Owner',
            email='test@restaurant.com',
            phone_number='555-0123',
            opening_hours={'Monday': '9am-10pm'}
        )
        
        # Create test category
        cls.category = MenuCategory.objects.create(
            name='Test Category'
        )
    
    def setUp(self):
        """
        Set up test fixtures before each test method.
        Creates fresh test data that can be modified without side effects.
        """
        self.client = Client()
        
        # Create daily special items (available)
        self.special1 = MenuItem.objects.create(
            name='Test Daily Special 1',
            description='Test daily special item 1',
            price=Decimal('15.99'),
            category=self.category,
            restaurant=self.restaurant,
            is_available=True,
            is_daily_special=True
        )
        
        self.special2 = MenuItem.objects.create(
            name='Test Daily Special 2',
            description='Test daily special item 2',
            price=Decimal('22.50'),
            category=self.category,
            restaurant=self.restaurant,
            is_available=True,
            is_daily_special=True
        )
        
        # Create daily special that's NOT available (should be filtered out)
        self.special3_unavailable = MenuItem.objects.create(
            name='Test Daily Special 3 (Unavailable)',
            description='Test daily special item 3 - not available',
            price=Decimal('18.00'),
            category=self.category,
            restaurant=self.restaurant,
            is_available=False,
            is_daily_special=True
        )
        
        # Create regular item (NOT a daily special - should be filtered out)
        self.regular_item = MenuItem.objects.create(
            name='Test Regular Item',
            description='Test regular menu item',
            price=Decimal('12.99'),
            category=self.category,
            restaurant=self.restaurant,
            is_available=True,
            is_daily_special=False
        )
    
    def test_api_endpoint_returns_200_ok(self):
        """Test that the API endpoint returns HTTP 200 OK status."""
        response = self.client.get('/api/daily-specials/')
        self.assertEqual(
            response.status_code, 
            200, 
            f"Expected 200 OK, got {response.status_code}"
        )
    
    def test_response_contains_only_available_daily_specials(self):
        """
        Test that response contains only items that are:
        - Marked as daily specials (is_daily_special=True)
        - Currently available (is_available=True)
        """
        response = self.client.get('/api/daily-specials/')
        data = response.json()
        
        # Handle both list and paginated dict responses
        if isinstance(data, dict) and 'results' in data:
            items = data['results']
        else:
            items = data
        
        # Should return exactly 2 items (special1 and special2)
        # NOT special3_unavailable (unavailable) or regular_item (not a special)
        self.assertEqual(
            len(items), 
            2, 
            f"Expected 2 daily specials, got {len(items)}"
        )
        
        # Verify the correct items are returned
        item_names = {item['name'] for item in items}
        expected_names = {'Test Daily Special 1', 'Test Daily Special 2'}
        self.assertEqual(
            item_names,
            expected_names,
            f"Expected items {expected_names}, got {item_names}"
        )
    
    def test_response_format_matches_serializer(self):
        """Test that the response format matches DailySpecialSerializer fields."""
        response = self.client.get('/api/daily-specials/')
        data = response.json()
        
        # Handle both list and paginated dict responses
        if isinstance(data, dict) and 'results' in data:
            items = data['results']
        else:
            items = data
        
        self.assertGreater(len(items), 0, "No items returned")
        
        # Check that all expected fields are present
        expected_fields = {
            'id', 'name', 'description', 'price', 
            'category_name', 'restaurant_name', 'image', 'is_available'
        }
        
        item = items[0]
        actual_fields = set(item.keys())
        
        self.assertEqual(
            expected_fields,
            actual_fields,
            f"Field mismatch. Expected: {expected_fields}, Got: {actual_fields}"
        )
    
    def test_all_returned_items_have_correct_flags(self):
        """
        Test that all returned items have:
        - is_daily_special=True
        - is_available=True
        """
        response = self.client.get('/api/daily-specials/')
        data = response.json()
        
        # Handle both list and paginated dict responses
        if isinstance(data, dict) and 'results' in data:
            items = data['results']
        else:
            items = data
        
        for item in items:
            # Fetch the actual menu item from database
            menu_item = MenuItem.objects.get(id=item['id'])
            
            self.assertTrue(
                menu_item.is_daily_special,
                f"Item {item['name']} (ID: {item['id']}) should have is_daily_special=True"
            )
            
            self.assertTrue(
                menu_item.is_available,
                f"Item {item['name']} (ID: {item['id']}) should have is_available=True"
            )
    
    def test_endpoint_is_publicly_accessible(self):
        """Test that the endpoint is accessible without authentication."""
        # Test without any authentication
        response = self.client.get('/api/daily-specials/')
        
        self.assertEqual(
            response.status_code,
            200,
            "Endpoint should be publicly accessible without authentication"
        )
    
    def test_response_includes_computed_fields(self):
        """Test that response includes computed fields from serializer."""
        response = self.client.get('/api/daily-specials/')
        data = response.json()
        
        # Handle both list and paginated dict responses
        if isinstance(data, dict) and 'results' in data:
            items = data['results']
        else:
            items = data
        
        self.assertGreater(len(items), 0, "No items returned")
        
        item = items[0]
        
        # Verify computed fields are present and have correct values
        self.assertIsNotNone(
            item.get('category_name'),
            "category_name field should be present"
        )
        self.assertEqual(
            item['category_name'],
            self.category.name,
            "category_name should match the category name"
        )
        
        self.assertIsNotNone(
            item.get('restaurant_name'),
            "restaurant_name field should be present"
        )
        self.assertEqual(
            item['restaurant_name'],
            self.restaurant.name,
            "restaurant_name should match the restaurant name"
        )
    
    def test_unavailable_specials_not_returned(self):
        """Test that daily specials marked as unavailable are not returned."""
        response = self.client.get('/api/daily-specials/')
        data = response.json()
        
        # Handle both list and paginated dict responses
        if isinstance(data, dict) and 'results' in data:
            items = data['results']
        else:
            items = data
        
        # Check that special3_unavailable is NOT in the results
        item_ids = {item['id'] for item in items}
        self.assertNotIn(
            self.special3_unavailable.id,
            item_ids,
            "Unavailable daily special should not be returned"
        )
    
    def test_non_special_items_not_returned(self):
        """Test that regular items (not marked as daily specials) are not returned."""
        response = self.client.get('/api/daily-specials/')
        data = response.json()
        
        # Handle both list and paginated dict responses
        if isinstance(data, dict) and 'results' in data:
            items = data['results']
        else:
            items = data
        
        # Check that regular_item is NOT in the results
        item_ids = {item['id'] for item in items}
        self.assertNotIn(
            self.regular_item.id,
            item_ids,
            "Regular menu items should not be returned"
        )


# Run tests with: python manage.py test home.tests.test_daily_specials
