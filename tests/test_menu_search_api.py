"""
Django unit tests for Menu Item Search API functionality.
Tests comprehensive search, filtering, and pagination features.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from home.models import MenuCategory, MenuItem, Restaurant
from decimal import Decimal


class MenuItemSearchAPITestCase(TestCase):
    """Test comprehensive menu item search API functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test user for admin operations
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create test restaurant
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner_name='Test Owner',
            email='test@restaurant.com',
            phone_number='123-456-7890'
        )
        
        # Create test categories
        self.appetizers = MenuCategory.objects.create(name='Appetizers')
        self.main_courses = MenuCategory.objects.create(name='Main Courses')
        self.desserts = MenuCategory.objects.create(name='Desserts')
        
        # Create diverse test menu items for search testing
        self.caesar_salad = MenuItem.objects.create(
            name='Caesar Salad',
            description='Fresh romaine lettuce with caesar dressing and croutons',
            price=Decimal('12.99'),
            restaurant=self.restaurant,
            category=self.appetizers,
            is_available=True
        )
        
        self.chicken_caesar = MenuItem.objects.create(
            name='Chicken Caesar Wrap',
            description='Grilled chicken with caesar salad in a tortilla wrap',
            price=Decimal('15.99'),
            restaurant=self.restaurant,
            category=self.main_courses,
            is_available=True
        )
        
        self.grilled_salmon = MenuItem.objects.create(
            name='Grilled Salmon',
            description='Fresh salmon grilled to perfection with herbs',
            price=Decimal('24.99'),
            restaurant=self.restaurant,
            category=self.main_courses,
            is_available=True
        )
        
        self.chocolate_cake = MenuItem.objects.create(
            name='Chocolate Cake',
            description='Rich chocolate cake with chocolate frosting',
            price=Decimal('8.99'),
            restaurant=self.restaurant,
            category=self.desserts,
            is_available=False
        )
        
        self.pizza_margherita = MenuItem.objects.create(
            name='Pizza Margherita',
            description='Classic pizza with tomato sauce, mozzarella, and basil',
            price=Decimal('18.99'),
            restaurant=self.restaurant,
            category=self.main_courses,
            is_available=True
        )
        
        self.expensive_steak = MenuItem.objects.create(
            name='Premium Ribeye Steak',
            description='Aged ribeye steak cooked to your preference',
            price=Decimal('45.99'),
            restaurant=self.restaurant,
            category=self.main_courses,
            is_available=True
        )
    
    def test_search_by_name(self):
        """Test searching menu items by name"""
        url = reverse('menuitem-list')
        response = self.client.get(url, {'search': 'caesar'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 2)  # Caesar Salad and Chicken Caesar Wrap
        
        names = [item['name'] for item in results]
        self.assertIn('Caesar Salad', names)
        self.assertIn('Chicken Caesar Wrap', names)
    
    def test_search_by_description(self):
        """Test searching menu items by description"""
        url = reverse('menuitem-list')
        response = self.client.get(url, {'search': 'chocolate'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Chocolate Cake')
    
    def test_search_case_insensitive(self):
        """Test that search is case-insensitive"""
        url = reverse('menuitem-list')
        response = self.client.get(url, {'search': 'GRILLED'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 2)  # Grilled Salmon and Chicken Caesar (has grilled in description)
    
    def test_search_partial_match(self):
        """Test partial text matching"""
        url = reverse('menuitem-list')
        response = self.client.get(url, {'search': 'choc'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Chocolate Cake')
    
    def test_search_no_results(self):
        """Test search with no matching results"""
        url = reverse('menuitem-list')
        response = self.client.get(url, {'search': 'nonexistent'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 0)
    
    def test_search_empty_query(self):
        """Test search with empty query returns all items"""
        url = reverse('menuitem-list')
        response = self.client.get(url, {'search': ''})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 6)  # All menu items
    
    def test_price_range_filtering(self):
        """Test filtering by price range"""
        url = reverse('menuitem-list')
        
        # Test minimum price filter
        response = self.client.get(url, {'min_price': '20.00'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        expensive_items = [item for item in results if float(item['price']) >= 20.00]
        self.assertEqual(len(results), len(expensive_items))
        
        # Test maximum price filter
        response = self.client.get(url, {'max_price': '15.00'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        cheap_items = [item for item in results if float(item['price']) <= 15.00]
        self.assertEqual(len(results), len(cheap_items))
        
        # Test price range (min and max)
        response = self.client.get(url, {'min_price': '10.00', 'max_price': '20.00'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        for item in results:
            price = float(item['price'])
            self.assertGreaterEqual(price, 10.00)
            self.assertLessEqual(price, 20.00)
    
    def test_invalid_price_filters(self):
        """Test invalid price filter values"""
        url = reverse('menuitem-list')
        
        # Invalid min_price
        response = self.client.get(url, {'min_price': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Invalid max_price
        response = self.client.get(url, {'max_price': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_combined_search_and_filters(self):
        """Test combining search with other filters"""
        url = reverse('menuitem-list')
        
        # Search + category filter
        response = self.client.get(url, {
            'search': 'caesar',
            'category': self.main_courses.id
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Chicken Caesar Wrap')
        
        # Search + availability filter
        response = self.client.get(url, {
            'search': 'cake',
            'available': 'false'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Chocolate Cake')
        
        # Search + price range + category
        response = self.client.get(url, {
            'search': 'grilled',
            'min_price': '20.00',
            'category': self.main_courses.id
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Grilled Salmon')
    
    def test_ordering_functionality(self):
        """Test ordering of search results"""
        url = reverse('menuitem-list')
        
        # Order by price ascending
        response = self.client.get(url, {'ordering': 'price'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        prices = [float(item['price']) for item in results]
        self.assertEqual(prices, sorted(prices))
        
        # Order by price descending
        response = self.client.get(url, {'ordering': '-price'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        prices = [float(item['price']) for item in results]
        self.assertEqual(prices, sorted(prices, reverse=True))
        
        # Order by name ascending
        response = self.client.get(url, {'ordering': 'name'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        names = [item['name'] for item in results]
        self.assertEqual(names, sorted(names))
    
    def test_search_with_ordering(self):
        """Test search combined with ordering"""
        url = reverse('menuitem-list')
        response = self.client.get(url, {
            'search': 'a',  # Items containing 'a'
            'ordering': 'price'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertGreater(len(results), 0)
        
        # Verify ordering is applied to search results
        prices = [float(item['price']) for item in results]
        self.assertEqual(prices, sorted(prices))
    
    def test_pagination_response_structure(self):
        """Test that pagination is working and response structure is correct"""
        url = reverse('menuitem-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if pagination is enabled (should have 'results' key if paginated)
        if 'results' in response.data:
            self.assertIn('count', response.data)
            self.assertIn('next', response.data)
            self.assertIn('previous', response.data)
            self.assertIn('results', response.data)
        else:
            # If not paginated, should be a list directly
            self.assertIsInstance(response.data, list)
    
    def test_search_performance_with_select_related(self):
        """Test that search uses optimized queries with select_related"""
        url = reverse('menuitem-list')
        
        # This test ensures our queryset uses select_related for performance
        # With pagination, we expect 2 queries: COUNT + SELECT with joins
        with self.assertNumQueries(2):  # COUNT query + SELECT with select_related
            response = self.client.get(url, {'search': 'caesar'})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            results = response.data.get('results', response.data)
            
            # Access related data to ensure it doesn't trigger additional queries
            for item in results:
                category_name = item.get('category_name')  # Should not trigger query