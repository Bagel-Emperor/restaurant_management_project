"""
Test cases for Order.get_unique_item_names() method.

This test module provides comprehensive coverage for the get_unique_item_names()
method, which returns a list of unique menu item names associated with an order.
"""

from django.test import TestCase
from decimal import Decimal
from orders.models import Order, OrderItem, OrderStatus
from orders.choices import OrderStatusChoices
from home.models import MenuItem, Restaurant, MenuCategory
from django.contrib.auth.models import User


class GetUniqueItemNamesTests(TestCase):
    """Test cases for the Order.get_unique_item_names() method."""
    
    def setUp(self):
        """Set up test data with restaurant, menu items, and orders."""
        # Create a user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a restaurant
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner_name='Test Owner',
            email='restaurant@test.com',
            phone_number='555-0100'
        )
        
        # Create a menu category
        self.category = MenuCategory.objects.create(
            name='Main Course',
            description='Main course items'
        )
        
        # Create multiple menu items
        self.pizza = MenuItem.objects.create(
            name='Margherita Pizza',
            description='Classic pizza',
            price=Decimal('12.99'),
            restaurant=self.restaurant,
            category=self.category
        )
        
        self.salad = MenuItem.objects.create(
            name='Caesar Salad',
            description='Fresh salad',
            price=Decimal('8.99'),
            restaurant=self.restaurant,
            category=self.category
        )
        
        self.pasta = MenuItem.objects.create(
            name='Spaghetti Carbonara',
            description='Creamy pasta',
            price=Decimal('14.99'),
            restaurant=self.restaurant,
            category=self.category
        )
        
        self.burger = MenuItem.objects.create(
            name='Cheeseburger',
            description='Juicy burger',
            price=Decimal('10.99'),
            restaurant=self.restaurant,
            category=self.category
        )
        
        self.dessert = MenuItem.objects.create(
            name='Tiramisu',
            description='Italian dessert',
            price=Decimal('6.99'),
            restaurant=self.restaurant,
            category=self.category
        )
        
        # Create order status
        self.status, _ = OrderStatus.objects.get_or_create(
            name=OrderStatusChoices.PENDING
        )
        
        # Create a test order
        self.order = Order.objects.create(
            user=self.user,
            status=self.status,
            total_amount=Decimal('0.00')
        )
    
    def test_single_item_order(self):
        """Test get_unique_item_names with a single item."""
        OrderItem.objects.create(
            order=self.order,
            menu_item=self.pizza,
            quantity=1,
            price=self.pizza.price
        )
        
        unique_names = self.order.get_unique_item_names()
        
        self.assertEqual(len(unique_names), 1)
        self.assertEqual(unique_names[0], 'Margherita Pizza')
    
    def test_multiple_unique_items(self):
        """Test get_unique_item_names with multiple different items."""
        OrderItem.objects.create(
            order=self.order,
            menu_item=self.pizza,
            quantity=1,
            price=self.pizza.price
        )
        OrderItem.objects.create(
            order=self.order,
            menu_item=self.salad,
            quantity=1,
            price=self.salad.price
        )
        OrderItem.objects.create(
            order=self.order,
            menu_item=self.pasta,
            quantity=1,
            price=self.pasta.price
        )
        
        unique_names = self.order.get_unique_item_names()
        
        self.assertEqual(len(unique_names), 3)
        self.assertIn('Margherita Pizza', unique_names)
        self.assertIn('Caesar Salad', unique_names)
        self.assertIn('Spaghetti Carbonara', unique_names)
    
    def test_duplicate_items_removed(self):
        """Test that duplicate item names are removed (only unique names returned)."""
        # Add the same item multiple times as separate OrderItems
        OrderItem.objects.create(
            order=self.order,
            menu_item=self.pizza,
            quantity=2,
            price=self.pizza.price
        )
        OrderItem.objects.create(
            order=self.order,
            menu_item=self.pizza,
            quantity=1,
            price=self.pizza.price
        )
        OrderItem.objects.create(
            order=self.order,
            menu_item=self.salad,
            quantity=1,
            price=self.salad.price
        )
        
        unique_names = self.order.get_unique_item_names()
        
        # Should only have 2 unique names despite 3 OrderItems
        self.assertEqual(len(unique_names), 2)
        self.assertIn('Margherita Pizza', unique_names)
        self.assertIn('Caesar Salad', unique_names)
    
    def test_empty_order(self):
        """Test get_unique_item_names with an order that has no items."""
        unique_names = self.order.get_unique_item_names()
        
        self.assertEqual(len(unique_names), 0)
        self.assertEqual(unique_names, [])
    
    def test_alphabetical_ordering(self):
        """Test that returned names are in alphabetical order."""
        # Add items in non-alphabetical order
        OrderItem.objects.create(
            order=self.order,
            menu_item=self.dessert,  # Tiramisu (T)
            quantity=1,
            price=self.dessert.price
        )
        OrderItem.objects.create(
            order=self.order,
            menu_item=self.burger,  # Cheeseburger (C)
            quantity=1,
            price=self.burger.price
        )
        OrderItem.objects.create(
            order=self.order,
            menu_item=self.pizza,  # Margherita Pizza (M)
            quantity=1,
            price=self.pizza.price
        )
        
        unique_names = self.order.get_unique_item_names()
        
        # Should be alphabetically sorted
        expected_order = ['Cheeseburger', 'Margherita Pizza', 'Tiramisu']
        self.assertEqual(unique_names, expected_order)
    
    def test_large_order_with_duplicates(self):
        """Test get_unique_item_names with a large order containing many duplicates."""
        # Create a large order with repeated items
        items = [
            (self.pizza, 2),
            (self.salad, 1),
            (self.pizza, 3),  # Duplicate
            (self.pasta, 1),
            (self.salad, 2),  # Duplicate
            (self.burger, 1),
            (self.pizza, 1),  # Duplicate again
            (self.dessert, 2),
        ]
        
        for menu_item, quantity in items:
            OrderItem.objects.create(
                order=self.order,
                menu_item=menu_item,
                quantity=quantity,
                price=menu_item.price
            )
        
        unique_names = self.order.get_unique_item_names()
        
        # Should have 5 unique items despite 8 OrderItems
        self.assertEqual(len(unique_names), 5)
        expected_names = [
            'Caesar Salad',
            'Cheeseburger',
            'Margherita Pizza',
            'Spaghetti Carbonara',
            'Tiramisu'
        ]
        self.assertEqual(unique_names, expected_names)
    
    def test_return_type_is_list(self):
        """Test that the method returns a list, not a set."""
        OrderItem.objects.create(
            order=self.order,
            menu_item=self.pizza,
            quantity=1,
            price=self.pizza.price
        )
        
        unique_names = self.order.get_unique_item_names()
        
        self.assertIsInstance(unique_names, list)
        self.assertNotIsInstance(unique_names, set)
    
    def test_preserves_item_name_casing(self):
        """Test that original casing of item names is preserved."""
        # Create item with specific casing
        special_item = MenuItem.objects.create(
            name='WiFi-Enabled COFFEE',
            description='Special coffee',
            price=Decimal('5.99'),
            restaurant=self.restaurant,
            category=self.category
        )
        
        OrderItem.objects.create(
            order=self.order,
            menu_item=special_item,
            quantity=1,
            price=special_item.price
        )
        
        unique_names = self.order.get_unique_item_names()
        
        self.assertEqual(unique_names[0], 'WiFi-Enabled COFFEE')
    
    def test_multiple_orders_independence(self):
        """Test that each order's unique items are independent."""
        # Create another order
        order2 = Order.objects.create(
            user=self.user,
            status=self.status,
            total_amount=Decimal('0.00')
        )
        
        # Add different items to each order
        OrderItem.objects.create(
            order=self.order,
            menu_item=self.pizza,
            quantity=1,
            price=self.pizza.price
        )
        
        OrderItem.objects.create(
            order=order2,
            menu_item=self.salad,
            quantity=1,
            price=self.salad.price
        )
        
        names1 = self.order.get_unique_item_names()
        names2 = order2.get_unique_item_names()
        
        self.assertEqual(names1, ['Margherita Pizza'])
        self.assertEqual(names2, ['Caesar Salad'])
        self.assertNotEqual(names1, names2)
    
    def test_works_with_different_order_statuses(self):
        """Test that method works regardless of order status."""
        # Create orders with different statuses
        completed_status, _ = OrderStatus.objects.get_or_create(
            name=OrderStatusChoices.COMPLETED
        )
        cancelled_status, _ = OrderStatus.objects.get_or_create(
            name=OrderStatusChoices.CANCELLED
        )
        
        completed_order = Order.objects.create(
            user=self.user,
            status=completed_status,
            total_amount=Decimal('20.00')
        )
        
        cancelled_order = Order.objects.create(
            user=self.user,
            status=cancelled_status,
            total_amount=Decimal('15.00')
        )
        
        # Add items to each
        OrderItem.objects.create(
            order=completed_order,
            menu_item=self.pizza,
            quantity=1,
            price=self.pizza.price
        )
        
        OrderItem.objects.create(
            order=cancelled_order,
            menu_item=self.salad,
            quantity=1,
            price=self.salad.price
        )
        
        # Both should work
        self.assertEqual(completed_order.get_unique_item_names(), ['Margherita Pizza'])
        self.assertEqual(cancelled_order.get_unique_item_names(), ['Caesar Salad'])
    
    def test_unicode_and_special_characters(self):
        """Test that method handles item names with Unicode and special characters."""
        special_items = [
            ('Crème Brûlée', Decimal('7.99')),
            ('Jalapeño Poppers', Decimal('6.99')),
            ('Açaí Bowl', Decimal('9.99')),
            ('Miso Soup (味噌汁)', Decimal('4.99')),
        ]
        
        for name, price in special_items:
            item = MenuItem.objects.create(
                name=name,
                description='Special item',
                price=price,
                restaurant=self.restaurant,
                category=self.category
            )
            OrderItem.objects.create(
                order=self.order,
                menu_item=item,
                quantity=1,
                price=price
            )
        
        unique_names = self.order.get_unique_item_names()
        
        self.assertEqual(len(unique_names), 4)
        # Check all special names are preserved
        for name, _ in special_items:
            self.assertIn(name, unique_names)


class GetUniqueItemNamesPerformanceTests(TestCase):
    """Test cases for performance characteristics of get_unique_item_names()."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner_name='Test Owner',
            email='restaurant@test.com',
            phone_number='555-0100'
        )
        
        self.category = MenuCategory.objects.create(
            name='Test Category',
            description='Test items'
        )
        
        self.status, _ = OrderStatus.objects.get_or_create(
            name=OrderStatusChoices.PENDING
        )
        
        self.order = Order.objects.create(
            user=self.user,
            status=self.status,
            total_amount=Decimal('0.00')
        )
    
    def test_query_efficiency_with_select_related(self):
        """Test that method uses select_related to avoid N+1 queries."""
        # Create multiple items
        items = []
        for i in range(5):
            item = MenuItem.objects.create(
                name=f'Item {i}',
                description=f'Description {i}',
                price=Decimal('10.00'),
                restaurant=self.restaurant,
                category=self.category
            )
            items.append(item)
            OrderItem.objects.create(
                order=self.order,
                menu_item=item,
                quantity=1,
                price=item.price
            )
        
        # Count queries
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        
        with CaptureQueriesContext(connection) as context:
            unique_names = self.order.get_unique_item_names()
        
        # Should only execute 1 query (with select_related join)
        # Not 6 queries (1 for order_items + 5 for each menu_item)
        self.assertEqual(len(context.captured_queries), 1)
        self.assertEqual(len(unique_names), 5)
    
    def test_handles_large_number_of_items(self):
        """Test that method efficiently handles orders with many items."""
        # Create 50 items
        for i in range(50):
            item = MenuItem.objects.create(
                name=f'Item {i:02d}',
                description=f'Description {i}',
                price=Decimal('10.00'),
                restaurant=self.restaurant,
                category=self.category
            )
            OrderItem.objects.create(
                order=self.order,
                menu_item=item,
                quantity=1,
                price=item.price
            )
        
        unique_names = self.order.get_unique_item_names()
        
        self.assertEqual(len(unique_names), 50)
        # Verify alphabetical ordering
        self.assertEqual(unique_names[0], 'Item 00')
        self.assertEqual(unique_names[-1], 'Item 49')
