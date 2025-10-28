"""
Django TestCase for Featured Menu Items Feature.

This test suite uses Django's TestCase class with proper database transactions
to ensure test isolation and avoid side effects on existing database records.

Tests:
1. Model field (is_featured) default behavior and validation
2. Filtering logic for featured items
3. API endpoint authentication and permissions
4. Response structure and data accuracy
5. Edge cases (no featured items, unavailable items)
6. Ordering by creation date (newest first)

Run with: python manage.py test home.tests.test_featured_menu_items
"""

from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
import json

from home.models import MenuItem, MenuCategory, Restaurant


class FeaturedMenuItemsModelTests(TestCase):
    """Test cases for the is_featured field on MenuItem model."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all test methods."""
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
            name='Test Category',
            description='Test category description'
        )
    
    def test_is_featured_defaults_to_false(self):
        """Test that is_featured field defaults to False when not specified."""
        menu_item = MenuItem.objects.create(
            name='Regular Item',
            description='A regular menu item',
            price=Decimal('10.00'),
            restaurant=self.restaurant,
            category=self.category
        )
        
        self.assertFalse(menu_item.is_featured)
        self.assertEqual(menu_item.is_featured, False)
    
    def test_is_featured_can_be_set_to_true(self):
        """Test that is_featured can be explicitly set to True."""
        menu_item = MenuItem.objects.create(
            name='Featured Item',
            description='A featured menu item',
            price=Decimal('15.00'),
            restaurant=self.restaurant,
            category=self.category,
            is_featured=True
        )
        
        self.assertTrue(menu_item.is_featured)
        self.assertEqual(menu_item.is_featured, True)
    
    def test_is_featured_is_boolean_field(self):
        """Test that is_featured is a boolean field."""
        # Create item with is_featured=True
        menu_item = MenuItem.objects.create(
            name='Featured Item',
            description='A featured menu item',
            price=Decimal('15.00'),
            restaurant=self.restaurant,
            category=self.category,
            is_featured=True
        )
        
        # Verify the field is stored as boolean
        field = MenuItem._meta.get_field('is_featured')
        self.assertEqual(field.get_internal_type(), 'BooleanField')
        
        # Verify the value is boolean
        self.assertIsInstance(menu_item.is_featured, bool)
    
    def test_featured_items_can_be_filtered(self):
        """Test that featured items can be filtered using Django ORM."""
        # Create a mix of featured and non-featured items
        MenuItem.objects.create(
            name='Featured Item 1',
            description='Featured',
            price=Decimal('15.00'),
            restaurant=self.restaurant,
            category=self.category,
            is_featured=True
        )
        
        MenuItem.objects.create(
            name='Regular Item 1',
            description='Not featured',
            price=Decimal('10.00'),
            restaurant=self.restaurant,
            category=self.category,
            is_featured=False
        )
        
        MenuItem.objects.create(
            name='Featured Item 2',
            description='Also featured',
            price=Decimal('20.00'),
            restaurant=self.restaurant,
            category=self.category,
            is_featured=True
        )
        
        # Test filtering
        featured_items = MenuItem.objects.filter(is_featured=True)
        self.assertEqual(featured_items.count(), 2)
        
        non_featured_items = MenuItem.objects.filter(is_featured=False)
        self.assertEqual(non_featured_items.count(), 1)


class FeaturedMenuItemsAPITests(TestCase):
    """Test cases for the Featured Menu Items API endpoint."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all test methods."""
        # Create test restaurant
        cls.restaurant = Restaurant.objects.create(
            name='La Bistro',
            owner_name='Bistro Owner',
            email='bistro@restaurant.com',
            phone_number='555-9876',
            opening_hours={'Monday': '11am-11pm'}
        )
        
        # Create test category
        cls.category = MenuCategory.objects.create(
            name='Main Courses',
            description='Main course dishes'
        )
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.client = Client()
        
        # Create featured items (available)
        self.featured_item1 = MenuItem.objects.create(
            name='Featured Special Pasta',
            description='Our signature pasta',
            price=Decimal('18.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_available=True,
            is_featured=True
        )
        
        self.featured_item2 = MenuItem.objects.create(
            name='Featured Grilled Salmon',
            description='Fresh salmon',
            price=Decimal('24.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_available=True,
            is_featured=True
        )
        
        # Create featured but unavailable item
        self.featured_unavailable = MenuItem.objects.create(
            name='Featured Unavailable Dish',
            description='Currently unavailable',
            price=Decimal('15.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_available=False,
            is_featured=True
        )
        
        # Create regular (not featured) item
        self.regular_item = MenuItem.objects.create(
            name='Regular Burger',
            description='Standard burger',
            price=Decimal('12.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_available=True,
            is_featured=False
        )
    
    def test_endpoint_accessible_without_authentication(self):
        """Test that the endpoint is publicly accessible."""
        response = self.client.get(reverse('featured-menu-items'))
        self.assertEqual(response.status_code, 200)
    
    def test_returns_only_featured_and_available_items(self):
        """Test that endpoint returns only items that are both featured and available."""
        response = self.client.get(reverse('featured-menu-items'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        
        # Handle paginated response
        if isinstance(data, dict) and 'results' in data:
            items = data['results']
            count = data['count']
        else:
            items = data
            count = len(data)
        
        # Should return exactly 2 items (only featured AND available)
        self.assertEqual(count, 2)
        self.assertEqual(len(items), 2)
        
        # Verify the items returned are the correct ones
        returned_names = [item['name'] for item in items]
        self.assertIn('Featured Special Pasta', returned_names)
        self.assertIn('Featured Grilled Salmon', returned_names)
        
        # Verify unavailable featured item is NOT included
        self.assertNotIn('Featured Unavailable Dish', returned_names)
        
        # Verify regular (non-featured) item is NOT included
        self.assertNotIn('Regular Burger', returned_names)
    
    def test_response_structure(self):
        """Test that response has correct structure with all expected fields."""
        response = self.client.get(reverse('featured-menu-items'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        
        # Handle paginated response
        if isinstance(data, dict) and 'results' in data:
            items = data['results']
        else:
            items = data
        
        # Check that we got at least one item
        self.assertGreater(len(items), 0)
        
        # Verify each item has the expected fields (using DailySpecialSerializer field names)
        for item in items:
            self.assertIn('id', item)
            self.assertIn('name', item)
            self.assertIn('description', item)
            self.assertIn('price', item)
            self.assertIn('category_name', item)
            self.assertIn('restaurant_name', item)
    
    def test_response_data_accuracy(self):
        """Test that returned data matches database values."""
        response = self.client.get(reverse('featured-menu-items'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        
        # Handle paginated response
        if isinstance(data, dict) and 'results' in data:
            items = data['results']
        else:
            items = data
        
        # Find the first featured item in response
        pasta_data = next((item for item in items if item['name'] == 'Featured Special Pasta'), None)
        self.assertIsNotNone(pasta_data)
        
        # Verify field values match database (using DailySpecialSerializer field names)
        self.assertEqual(pasta_data['name'], 'Featured Special Pasta')
        self.assertEqual(pasta_data['description'], 'Our signature pasta')
        self.assertEqual(Decimal(pasta_data['price']), Decimal('18.99'))
        self.assertEqual(pasta_data['category_name'], 'Main Courses')
        self.assertEqual(pasta_data['restaurant_name'], 'La Bistro')
    
    def test_empty_result_when_no_featured_items(self):
        """Test that endpoint returns empty list when no featured items exist."""
        # Remove all featured flags
        MenuItem.objects.all().update(is_featured=False)
        
        response = self.client.get(reverse('featured-menu-items'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        
        # Handle paginated response
        if isinstance(data, dict) and 'results' in data:
            items = data['results']
            count = data['count']
        else:
            items = data
            count = len(data)
        
        self.assertEqual(count, 0)
        self.assertEqual(len(items), 0)
    
    def test_empty_result_when_all_featured_unavailable(self):
        """Test that endpoint returns empty list when all featured items are unavailable."""
        # Mark all featured items as unavailable
        MenuItem.objects.filter(is_featured=True).update(is_available=False)
        
        response = self.client.get(reverse('featured-menu-items'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        
        # Handle paginated response
        if isinstance(data, dict) and 'results' in data:
            items = data['results']
            count = data['count']
        else:
            items = data
            count = len(data)
        
        self.assertEqual(count, 0)
        self.assertEqual(len(items), 0)
    
    def test_items_ordered_by_newest_first(self):
        """Test that featured items are ordered by creation date (newest first)."""
        response = self.client.get(reverse('featured-menu-items'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        
        # Handle paginated response
        if isinstance(data, dict) and 'results' in data:
            items = data['results']
        else:
            items = data
        
        # The newest item should be featured_item2 (created last in setUp)
        self.assertEqual(items[0]['name'], 'Featured Grilled Salmon')
        self.assertEqual(items[1]['name'], 'Featured Special Pasta')
    
    def test_content_type_is_json(self):
        """Test that response content type is JSON."""
        response = self.client.get(reverse('featured-menu-items'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
    
    def test_get_method_allowed(self):
        """Test that GET method is allowed."""
        response = self.client.get(reverse('featured-menu-items'))
        self.assertEqual(response.status_code, 200)
    
    def test_post_method_not_allowed(self):
        """Test that POST method is not allowed (read-only endpoint)."""
        response = self.client.post(reverse('featured-menu-items'), {})
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
    
    def test_put_method_not_allowed(self):
        """Test that PUT method is not allowed."""
        response = self.client.put(reverse('featured-menu-items'), {})
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
    
    def test_delete_method_not_allowed(self):
        """Test that DELETE method is not allowed."""
        response = self.client.delete(reverse('featured-menu-items'))
        self.assertEqual(response.status_code, 405)  # Method Not Allowed


if __name__ == '__main__':
    print("=" * 80)
    print("FEATURED MENU ITEMS TEST SUITE")
    print("=" * 80)
    print("\nRun with: python manage.py test home.tests.test_featured_menu_items")
    print("\nThis test suite covers:")
    print("  ✓ Model field (is_featured) default behavior")
    print("  ✓ Field validation and filtering")
    print("  ✓ API endpoint permissions")
    print("  ✓ Response structure and data accuracy")
    print("  ✓ Edge cases and error handling")
    print("=" * 80)
