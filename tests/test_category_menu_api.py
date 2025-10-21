"""
Django unit tests for Category-based Menu Item API endpoints.
Tests the new category filtering functionality.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from home.models import MenuCategory, MenuItem, Restaurant


class CategoryMenuItemAPITestCase(TestCase):
    """Test category-based menu item filtering API endpoints"""
    
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
        
        # Create test menu items with categories
        self.appetizer_item = MenuItem.objects.create(
            name='Caesar Salad',
            description='Fresh romaine lettuce with caesar dressing',
            price=12.99,
            restaurant=self.restaurant,
            category=self.appetizers,
            is_available=True
        )
        
        self.main_course_item = MenuItem.objects.create(
            name='Grilled Salmon',
            description='Fresh salmon with herbs',
            price=24.99,
            restaurant=self.restaurant,
            category=self.main_courses,
            is_available=True
        )
        
        self.dessert_item = MenuItem.objects.create(
            name='Chocolate Cake',
            description='Rich chocolate cake',
            price=8.99,
            restaurant=self.restaurant,
            category=self.desserts,
            is_available=False
        )
        
        # Menu item without category
        self.uncategorized_item = MenuItem.objects.create(
            name='Special Item',
            description='No category assigned',
            price=15.99,
            restaurant=self.restaurant,
            is_available=True
        )
    
    def test_menu_categories_list(self):
        """Test listing all menu categories"""
        url = reverse('menu-category-list')  # Using reverse to get correct URL
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 3)
        
        category_names = [cat['name'] for cat in results]
        self.assertIn('Appetizers', category_names)
        self.assertIn('Main Courses', category_names)
        self.assertIn('Desserts', category_names)
    
    def test_menu_items_include_category_data(self):
        """Test that menu items include category information"""
        url = reverse('menuitem-list')  # ViewSet list endpoint
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 4)  # 4 menu items created
        
        # Check that category data is included
        for item in results:
            self.assertIn('category', item)
            self.assertIn('category_name', item)
    
    def test_filter_menu_items_by_category_id(self):
        """Test filtering menu items by category ID"""
        url = reverse('menuitem-list')
        response = self.client.get(url, {'category': self.appetizers.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Caesar Salad')
        self.assertEqual(results[0]['category_name'], 'Appetizers')
    
    def test_filter_menu_items_by_category_name(self):
        """Test filtering menu items by category name (case-insensitive)"""
        url = reverse('menuitem-list')
        response = self.client.get(url, {'category': 'main courses'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Grilled Salmon')
        self.assertEqual(results[0]['category_name'], 'Main Courses')
    
    def test_filter_menu_items_by_partial_category_name(self):
        """Test filtering menu items by partial category name"""
        url = reverse('menuitem-list')
        response = self.client.get(url, {'category': 'app'})  # Should match 'Appetizers'
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Caesar Salad')
    
    def test_combined_filtering_category_and_availability(self):
        """Test filtering by both category and availability"""
        url = reverse('menuitem-list')
        response = self.client.get(url, {
            'category': self.desserts.id,
            'available': 'false'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Chocolate Cake')
        self.assertEqual(results[0]['is_available'], False)
    
    def test_combined_filtering_category_and_restaurant(self):
        """Test filtering by category and restaurant"""
        url = reverse('menuitem-list')
        response = self.client.get(url, {
            'category': self.main_courses.id,
            'restaurant': self.restaurant.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Grilled Salmon')
    
    def test_filter_nonexistent_category(self):
        """Test filtering by non-existent category returns empty results"""
        url = reverse('menuitem-list')
        response = self.client.get(url, {'category': 'nonexistent'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 0)
    
    def test_filter_nonexistent_category_id(self):
        """Test filtering by non-existent category ID returns empty results"""
        url = reverse('menuitem-list')
        response = self.client.get(url, {'category': '999'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 0)
    
    def test_filter_negative_category_id(self):
        """Test filtering by negative category ID returns empty results (not treated as name)"""
        url = reverse('menuitem-list')
        response = self.client.get(url, {'category': '-1'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 0)
    
    def test_filter_invalid_category_id_falls_back_to_name(self):
        """Test that invalid category ID formats fall back to name filtering"""
        url = reverse('menuitem-list')
        response = self.client.get(url, {'category': 'abc123'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 0)  # No category named 'abc123'
    
    def test_menu_item_serializer_includes_category_fields(self):
        """Test that menu item serializer includes both category ID and name"""
        url = reverse('menuitem-detail', kwargs={'pk': self.appetizer_item.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['category'], self.appetizers.id)
        self.assertEqual(response.data['category_name'], 'Appetizers')
    
    def test_menu_item_without_category(self):
        """Test menu item without assigned category"""
        url = reverse('menuitem-detail', kwargs={'pk': self.uncategorized_item.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['category'])
        self.assertIsNone(response.data['category_name'])