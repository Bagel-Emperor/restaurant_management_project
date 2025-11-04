"""Tests for get_distinct_cuisines utility."""
from django.test import TestCase
from home.models import Restaurant, MenuCategory, MenuItem
from home.utils import get_distinct_cuisines


class GetDistinctCuisinesTests(TestCase):
    """Test get_distinct_cuisines function."""
    
    def setUp(self):
        """Set up test data."""
        self.restaurant = Restaurant.objects.create(name='Test Restaurant')
        self.cat1 = MenuCategory.objects.create(name='Appetizers')
        self.cat2 = MenuCategory.objects.create(name='Main Course')
        self.cat3 = MenuCategory.objects.create(name='Desserts')
    
    def test_distinct_cuisines(self):
        """Test getting distinct categories."""
        MenuItem.objects.create(name='Item1', price=10, restaurant=self.restaurant, category=self.cat1)
        MenuItem.objects.create(name='Item2', price=15, restaurant=self.restaurant, category=self.cat1)
        MenuItem.objects.create(name='Item3', price=20, restaurant=self.restaurant, category=self.cat2)
        
        result = get_distinct_cuisines()
        
        self.assertEqual(len(result), 2)
        self.assertIn('Appetizers', result)
        self.assertIn('Main Course', result)
    
    def test_empty_result(self):
        """Test with no menu items."""
        result = get_distinct_cuisines()
        self.assertEqual(result, [])
