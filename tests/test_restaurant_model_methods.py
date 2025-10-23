"""
Tests for Restaurant Model Methods.

This module tests custom methods added to the Restaurant model,
particularly the get_total_menu_items() method which provides
summary information about the restaurant's menu.

Test Coverage:
- get_total_menu_items() with no items
- get_total_menu_items() with multiple items
- get_total_menu_items() counts all items (available and unavailable)
- get_total_menu_items() counts only items for specific restaurant
- Multiple restaurants with different item counts
"""

from django.test import TestCase
from home.models import Restaurant, MenuItem
from decimal import Decimal


class RestaurantModelMethodsTest(TestCase):
    """Test suite for Restaurant model methods."""
    
    def setUp(self):
        """Set up test data before each test."""
        # Create test restaurants
        self.restaurant1 = Restaurant.objects.create(
            name='Test Bistro',
            owner_name='Test Owner',
            email='owner@testbistro.com',
            phone_number='555-0100'
        )
        
        self.restaurant2 = Restaurant.objects.create(
            name='Second Restaurant',
            owner_name='Second Owner',
            email='owner@second.com',
            phone_number='555-0200'
        )
    
    def test_get_total_menu_items_with_no_items(self):
        """Test that get_total_menu_items returns 0 when restaurant has no items."""
        total = self.restaurant1.get_total_menu_items()
        
        self.assertEqual(total, 0)
        self.assertIsInstance(total, int)
    
    def test_get_total_menu_items_with_single_item(self):
        """Test that get_total_menu_items returns 1 when restaurant has one item."""
        MenuItem.objects.create(
            name='Test Item',
            description='Test description',
            price=Decimal('9.99'),
            restaurant=self.restaurant1,
            is_available=True
        )
        
        total = self.restaurant1.get_total_menu_items()
        
        self.assertEqual(total, 1)
    
    def test_get_total_menu_items_with_multiple_items(self):
        """Test that get_total_menu_items returns correct count with multiple items."""
        # Create 5 menu items
        for i in range(5):
            MenuItem.objects.create(
                name=f'Test Item {i}',
                description=f'Description {i}',
                price=Decimal('10.00') + Decimal(i),
                restaurant=self.restaurant1,
                is_available=True
            )
        
        total = self.restaurant1.get_total_menu_items()
        
        self.assertEqual(total, 5)
    
    def test_get_total_menu_items_counts_available_and_unavailable(self):
        """Test that get_total_menu_items counts both available and unavailable items."""
        # Create available items
        for i in range(3):
            MenuItem.objects.create(
                name=f'Available Item {i}',
                description='Available',
                price=Decimal('10.00'),
                restaurant=self.restaurant1,
                is_available=True
            )
        
        # Create unavailable items
        for i in range(2):
            MenuItem.objects.create(
                name=f'Unavailable Item {i}',
                description='Unavailable',
                price=Decimal('10.00'),
                restaurant=self.restaurant1,
                is_available=False
            )
        
        total = self.restaurant1.get_total_menu_items()
        
        # Should count all items (3 available + 2 unavailable = 5)
        self.assertEqual(total, 5)
    
    def test_get_total_menu_items_only_counts_own_items(self):
        """Test that get_total_menu_items only counts items for specific restaurant."""
        # Create items for restaurant1
        for i in range(3):
            MenuItem.objects.create(
                name=f'Restaurant1 Item {i}',
                description='For restaurant 1',
                price=Decimal('10.00'),
                restaurant=self.restaurant1,
                is_available=True
            )
        
        # Create items for restaurant2
        for i in range(5):
            MenuItem.objects.create(
                name=f'Restaurant2 Item {i}',
                description='For restaurant 2',
                price=Decimal('10.00'),
                restaurant=self.restaurant2,
                is_available=True
            )
        
        total1 = self.restaurant1.get_total_menu_items()
        total2 = self.restaurant2.get_total_menu_items()
        
        self.assertEqual(total1, 3)
        self.assertEqual(total2, 5)
    
    def test_get_total_menu_items_after_adding_items(self):
        """Test that get_total_menu_items updates correctly when items are added."""
        # Initially no items
        self.assertEqual(self.restaurant1.get_total_menu_items(), 0)
        
        # Add first item
        MenuItem.objects.create(
            name='First Item',
            description='First',
            price=Decimal('10.00'),
            restaurant=self.restaurant1,
            is_available=True
        )
        self.assertEqual(self.restaurant1.get_total_menu_items(), 1)
        
        # Add second item
        MenuItem.objects.create(
            name='Second Item',
            description='Second',
            price=Decimal('15.00'),
            restaurant=self.restaurant1,
            is_available=True
        )
        self.assertEqual(self.restaurant1.get_total_menu_items(), 2)
    
    def test_get_total_menu_items_after_deleting_items(self):
        """Test that get_total_menu_items updates correctly when items are deleted."""
        # Create 3 items
        items = []
        for i in range(3):
            item = MenuItem.objects.create(
                name=f'Item {i}',
                description='Test',
                price=Decimal('10.00'),
                restaurant=self.restaurant1,
                is_available=True
            )
            items.append(item)
        
        self.assertEqual(self.restaurant1.get_total_menu_items(), 3)
        
        # Delete one item
        items[0].delete()
        self.assertEqual(self.restaurant1.get_total_menu_items(), 2)
        
        # Delete another item
        items[1].delete()
        self.assertEqual(self.restaurant1.get_total_menu_items(), 1)
    
    def test_get_total_menu_items_return_type(self):
        """Test that get_total_menu_items returns an integer."""
        MenuItem.objects.create(
            name='Test Item',
            description='Test',
            price=Decimal('10.00'),
            restaurant=self.restaurant1,
            is_available=True
        )
        
        total = self.restaurant1.get_total_menu_items()
        
        self.assertIsInstance(total, int)
    
    def test_get_total_menu_items_with_large_number_of_items(self):
        """Test that get_total_menu_items works correctly with large numbers."""
        # Create 100 items
        MenuItem.objects.bulk_create([
            MenuItem(
                name=f'Item {i}',
                description='Test',
                price=Decimal('10.00'),
                restaurant=self.restaurant1,
                is_available=True
            )
            for i in range(100)
        ])
        
        total = self.restaurant1.get_total_menu_items()
        
        self.assertEqual(total, 100)
    
    def test_get_total_menu_items_method_exists(self):
        """Test that get_total_menu_items method exists on Restaurant model."""
        self.assertTrue(hasattr(self.restaurant1, 'get_total_menu_items'))
        self.assertTrue(callable(getattr(self.restaurant1, 'get_total_menu_items')))
    
    def test_get_total_menu_items_no_parameters_required(self):
        """Test that get_total_menu_items can be called without parameters."""
        # Should not raise TypeError
        try:
            total = self.restaurant1.get_total_menu_items()
            # If we get here, the method was called successfully
            self.assertIsInstance(total, int)
        except TypeError:
            self.fail("get_total_menu_items() should not require any parameters")


class RestaurantModelIntegrationTest(TestCase):
    """Integration tests for Restaurant model methods with related models."""
    
    def setUp(self):
        """Set up test data."""
        self.restaurant = Restaurant.objects.create(
            name='Integration Test Restaurant',
            owner_name='Test Owner',
            email='integration@test.com',
            phone_number='555-0300'
        )
    
    def test_get_total_menu_items_with_menu_item_relationship(self):
        """Test that get_total_menu_items uses the menu_items relationship correctly."""
        # Verify the relationship exists
        self.assertTrue(hasattr(self.restaurant, 'menu_items'))
        
        # Create items using the relationship
        self.restaurant.menu_items.create(
            name='Item 1',
            description='Test',
            price=Decimal('10.00'),
            is_available=True
        )
        self.restaurant.menu_items.create(
            name='Item 2',
            description='Test',
            price=Decimal('15.00'),
            is_available=True
        )
        
        # Verify count
        self.assertEqual(self.restaurant.get_total_menu_items(), 2)
        self.assertEqual(self.restaurant.menu_items.count(), 2)
