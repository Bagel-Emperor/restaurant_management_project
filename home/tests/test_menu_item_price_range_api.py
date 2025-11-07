"""
Comprehensive tests for MenuItemPriceRangeView API endpoint.

Tests the API endpoint that filters menu items by price range using
min_price and max_price query parameters.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from home.models import MenuItem, MenuCategory, Restaurant


class MenuItemPriceRangeAPITests(TestCase):
    """Test suite for MenuItemPriceRangeView API endpoint."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all test methods."""
        # Create a restaurant
        cls.restaurant = Restaurant.objects.create(
            name="Test Restaurant",
            owner_name="Test Owner",
            email="test@restaurant.com",
            phone_number="555-1234"
        )
        
        # Create a category
        cls.category = MenuCategory.objects.create(
            name="Main Course",
            description="Main dishes"
        )
        
        # Create menu items with various prices
        cls.item1 = MenuItem.objects.create(
            name="Budget Burger",
            description="Affordable burger",
            price=Decimal('5.99'),
            restaurant=cls.restaurant,
            category=cls.category,
            is_available=True
        )
        
        cls.item2 = MenuItem.objects.create(
            name="Classic Pizza",
            description="Standard pizza",
            price=Decimal('12.50'),
            restaurant=cls.restaurant,
            category=cls.category,
            is_available=True
        )
        
        cls.item3 = MenuItem.objects.create(
            name="Premium Steak",
            description="High-end steak",
            price=Decimal('45.00'),
            restaurant=cls.restaurant,
            category=cls.category,
            is_available=True
        )
        
        cls.item4 = MenuItem.objects.create(
            name="Gourmet Lobster",
            description="Luxury lobster dish",
            price=Decimal('89.99'),
            restaurant=cls.restaurant,
            category=cls.category,
            is_available=True
        )
        
        cls.item5 = MenuItem.objects.create(
            name="Side Salad",
            description="Fresh salad",
            price=Decimal('3.50'),
            restaurant=cls.restaurant,
            category=cls.category,
            is_available=True
        )
        
        cls.item6 = MenuItem.objects.create(
            name="Mid-range Pasta",
            description="Pasta dish",
            price=Decimal('18.75'),
            restaurant=cls.restaurant,
            category=cls.category,
            is_available=True
        )
        
        cls.url = reverse('menuitem-price-range')
    
    def setUp(self):
        """Set up test client for each test."""
        self.client = APIClient()
    
    # Basic Filtering Tests
    
    def test_filter_by_min_price_only(self):
        """Test filtering with only min_price parameter."""
        response = self.client.get(self.url, {'min_price': '10.00'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
        # Should return items >= 10.00 (item2, item3, item4, item6)
        results = response.data['results']
        result_ids = [item['id'] for item in results]
        
        self.assertIn(self.item2.id, result_ids)
        self.assertIn(self.item3.id, result_ids)
        self.assertIn(self.item4.id, result_ids)
        self.assertIn(self.item6.id, result_ids)
        self.assertNotIn(self.item1.id, result_ids)  # 5.99
        self.assertNotIn(self.item5.id, result_ids)  # 3.50
    
    def test_filter_by_max_price_only(self):
        """Test filtering with only max_price parameter."""
        response = self.client.get(self.url, {'max_price': '20.00'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
        # Should return items <= 20.00 (item1, item2, item5, item6)
        results = response.data['results']
        result_ids = [item['id'] for item in results]
        
        self.assertIn(self.item1.id, result_ids)  # 5.99
        self.assertIn(self.item2.id, result_ids)  # 12.50
        self.assertIn(self.item5.id, result_ids)  # 3.50
        self.assertIn(self.item6.id, result_ids)  # 18.75
        self.assertNotIn(self.item3.id, result_ids)  # 45.00
        self.assertNotIn(self.item4.id, result_ids)  # 89.99
    
    def test_filter_by_both_min_and_max_price(self):
        """Test filtering with both min_price and max_price."""
        response = self.client.get(self.url, {
            'min_price': '10.00',
            'max_price': '50.00'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
        # Should return items between 10.00 and 50.00 (item2, item3, item6)
        results = response.data['results']
        result_ids = [item['id'] for item in results]
        
        self.assertIn(self.item2.id, result_ids)  # 12.50
        self.assertIn(self.item3.id, result_ids)  # 45.00
        self.assertIn(self.item6.id, result_ids)  # 18.75
        self.assertNotIn(self.item1.id, result_ids)  # 5.99
        self.assertNotIn(self.item4.id, result_ids)  # 89.99
        self.assertNotIn(self.item5.id, result_ids)  # 3.50
    
    def test_no_parameters_returns_all_items(self):
        """Test that no parameters returns all menu items."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
        # Should return all items
        results = response.data['results']
        self.assertEqual(len(results), 6)
    
    def test_exact_price_match_min(self):
        """Test that items at exact min_price are included."""
        response = self.client.get(self.url, {'min_price': '12.50'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        result_ids = [item['id'] for item in results]
        
        # Should include item with price exactly 12.50
        self.assertIn(self.item2.id, result_ids)
    
    def test_exact_price_match_max(self):
        """Test that items at exact max_price are included."""
        response = self.client.get(self.url, {'max_price': '45.00'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        result_ids = [item['id'] for item in results]
        
        # Should include item with price exactly 45.00
        self.assertIn(self.item3.id, result_ids)
    
    def test_narrow_price_range(self):
        """Test a narrow price range."""
        response = self.client.get(self.url, {
            'min_price': '12.00',
            'max_price': '13.00'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        
        # Should only return item2 (12.50)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.item2.id)
    
    def test_no_items_in_range(self):
        """Test price range with no matching items."""
        response = self.client.get(self.url, {
            'min_price': '60.00',
            'max_price': '80.00'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        
        # Should return empty list
        self.assertEqual(len(results), 0)
    
    # Results Ordering Tests
    
    def test_results_ordered_by_price_ascending(self):
        """Test that results are ordered by price (ascending)."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        
        # Extract prices from results
        prices = [Decimal(item['price']) for item in results]
        
        # Verify prices are in ascending order
        self.assertEqual(prices, sorted(prices))
        
        # Verify specific order
        self.assertEqual(prices[0], Decimal('3.50'))  # item5
        self.assertEqual(prices[-1], Decimal('89.99'))  # item4
    
    # Error Handling Tests
    
    def test_invalid_min_price_non_numeric(self):
        """Test error when min_price is not a valid number."""
        response = self.client.get(self.url, {'min_price': 'abc'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('must be a valid decimal', response.data['error'])
    
    def test_invalid_max_price_non_numeric(self):
        """Test error when max_price is not a valid number."""
        response = self.client.get(self.url, {'max_price': 'xyz'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('must be a valid decimal', response.data['error'])
    
    def test_negative_min_price(self):
        """Test error when min_price is negative."""
        response = self.client.get(self.url, {'min_price': '-10.00'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('non-negative', response.data['error'])
    
    def test_negative_max_price(self):
        """Test error when max_price is negative."""
        response = self.client.get(self.url, {'max_price': '-5.00'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('non-negative', response.data['error'])
    
    def test_min_price_greater_than_max_price(self):
        """Test error when min_price > max_price."""
        response = self.client.get(self.url, {
            'min_price': '50.00',
            'max_price': '20.00'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('cannot be greater than', response.data['error'])
    
    def test_empty_string_min_price(self):
        """Test error when min_price is empty string."""
        response = self.client.get(self.url, {'min_price': ''})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_empty_string_max_price(self):
        """Test error when max_price is empty string."""
        response = self.client.get(self.url, {'max_price': ''})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    # Edge Cases
    
    def test_zero_min_price(self):
        """Test that min_price of 0 is valid."""
        response = self.client.get(self.url, {'min_price': '0'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return all items (all are >= 0)
        self.assertEqual(len(response.data['results']), 6)
    
    def test_zero_max_price(self):
        """Test that max_price of 0 returns no items."""
        response = self.client.get(self.url, {'max_price': '0'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return no items (all are > 0)
        self.assertEqual(len(response.data['results']), 0)
    
    def test_very_large_max_price(self):
        """Test with very large max_price."""
        response = self.client.get(self.url, {'max_price': '99999.99'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return all items
        self.assertEqual(len(response.data['results']), 6)
    
    def test_decimal_precision(self):
        """Test that decimal prices work correctly."""
        response = self.client.get(self.url, {
            'min_price': '5.50',
            'max_price': '12.75'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        result_ids = [item['id'] for item in results]
        
        # Should include item1 (5.99) and item2 (12.50)
        self.assertIn(self.item1.id, result_ids)
        self.assertIn(self.item2.id, result_ids)
        # Should NOT include item5 (3.50) or item6 (18.75)
        self.assertNotIn(self.item5.id, result_ids)
        self.assertNotIn(self.item6.id, result_ids)
    
    # Response Format Tests
    
    def test_response_has_pagination_fields(self):
        """Test that response includes pagination fields."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)
    
    def test_response_item_structure(self):
        """Test that each item in results has expected fields."""
        response = self.client.get(self.url, {'max_price': '10.00'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        
        self.assertGreater(len(results), 0)
        
        # Check first item has all expected fields
        item = results[0]
        self.assertIn('id', item)
        self.assertIn('name', item)
        self.assertIn('description', item)
        self.assertIn('price', item)
        self.assertIn('restaurant', item)
        self.assertIn('category', item)
        self.assertIn('category_name', item)
        self.assertIn('is_available', item)
        self.assertIn('created_at', item)
    
    def test_count_field_accuracy(self):
        """Test that count field matches actual number of results."""
        response = self.client.get(self.url, {
            'min_price': '10.00',
            'max_price': '50.00'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Count should match the actual number of items
        expected_count = 3  # item2, item3, item6
        self.assertEqual(response.data['count'], expected_count)
    
    # Public Access Tests
    
    def test_public_access_no_authentication_required(self):
        """Test that endpoint is accessible without authentication."""
        # Using unauthenticated client
        response = self.client.get(self.url, {'min_price': '5.00'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should NOT return 401 or 403
    
    # Multiple Query Parameters Tests
    
    def test_multiple_same_parameter(self):
        """Test behavior when same parameter provided multiple times."""
        # Django typically takes the last value
        response = self.client.get(f"{self.url}?min_price=10&min_price=20")
        
        # Should use the last value (20)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        result_ids = [item['id'] for item in results]
        
        # Should not include items < 20
        self.assertNotIn(self.item2.id, result_ids)  # 12.50
    
    def test_extra_query_parameters_ignored(self):
        """Test that extra unrelated query parameters are ignored."""
        response = self.client.get(self.url, {
            'min_price': '10.00',
            'max_price': '50.00',
            'random_param': 'ignored',
            'another_param': '123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should work normally, ignoring extra params
        results = response.data['results']
        self.assertEqual(len(results), 3)  # item2, item3, item6
    
    # Integration Tests
    
    def test_filter_with_multiple_restaurants(self):
        """Test filtering works across multiple restaurants."""
        # Create second restaurant
        restaurant2 = Restaurant.objects.create(
            name="Another Restaurant",
            owner_name="Another Owner",
            email="another@restaurant.com",
            phone_number="555-5678"
        )
        
        # Create item in second restaurant
        item7 = MenuItem.objects.create(
            name="Restaurant 2 Item",
            description="From another restaurant",
            price=Decimal('15.00'),
            restaurant=restaurant2,
            category=self.category,
            is_available=True
        )
        
        response = self.client.get(self.url, {
            'min_price': '12.00',
            'max_price': '20.00'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        result_ids = [item['id'] for item in results]
        
        # Should include items from both restaurants
        self.assertIn(self.item2.id, result_ids)  # Restaurant 1
        self.assertIn(item7.id, result_ids)  # Restaurant 2
    
    def test_unavailable_items_included(self):
        """Test that unavailable items are still included in results."""
        # Create unavailable item
        unavailable_item = MenuItem.objects.create(
            name="Unavailable Item",
            description="Not available",
            price=Decimal('15.00'),
            restaurant=self.restaurant,
            category=self.category,
            is_available=False
        )
        
        response = self.client.get(self.url, {
            'min_price': '14.00',
            'max_price': '16.00'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        result_ids = [item['id'] for item in results]
        
        # Unavailable item should be included (API doesn't filter by availability)
        self.assertIn(unavailable_item.id, result_ids)
