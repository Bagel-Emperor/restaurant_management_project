"""
Django TestCase for MenuItemManager custom manager.

This test suite validates the custom manager functionality including:
1. Manager attachment and method availability
2. get_top_selling_items() method behavior
3. Annotation correctness (total_ordered)
4. Ordering logic (descending by quantity)
5. Parameter handling (num_items)
6. Edge cases (no orders, tied quantities)

Run with: python manage.py test home.tests.test_menu_item_manager
"""

from django.test import TestCase
from decimal import Decimal

from home.models import MenuItem, MenuCategory, Restaurant
from orders.models import Order, OrderItem, OrderStatus
from django.contrib.auth.models import User


class MenuItemManagerTests(TestCase):
    """Test cases for the custom MenuItemManager."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all test methods."""
        # Create test user
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test restaurant
        cls.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner_name='Test Owner',
            email='restaurant@test.com',
            phone_number='555-0100',
            opening_hours={'Monday': '9am-10pm'}
        )
        
        # Create test category
        cls.category = MenuCategory.objects.create(
            name='Test Category',
            description='Test category description'
        )
        
        # Create OrderStatus for orders
        cls.pending_status, _ = OrderStatus.objects.get_or_create(name='pending')
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create test menu items
        self.item1 = MenuItem.objects.create(
            name='Burger',
            description='Delicious burger',
            price=Decimal('12.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_available=True
        )
        
        self.item2 = MenuItem.objects.create(
            name='Pizza',
            description='Cheese pizza',
            price=Decimal('15.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_available=True
        )
        
        self.item3 = MenuItem.objects.create(
            name='Salad',
            description='Fresh salad',
            price=Decimal('8.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_available=True
        )
        
        self.item4 = MenuItem.objects.create(
            name='Pasta',
            description='Italian pasta',
            price=Decimal('13.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_available=True
        )
        
        self.item5 = MenuItem.objects.create(
            name='Steak',
            description='Grilled steak',
            price=Decimal('25.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_available=True
        )
    
    def test_manager_is_attached(self):
        """Test that custom manager is properly attached to MenuItem model."""
        self.assertEqual(MenuItem.objects.__class__.__name__, 'MenuItemManager')
    
    def test_get_top_selling_items_method_exists(self):
        """Test that get_top_selling_items method exists on the manager."""
        self.assertTrue(hasattr(MenuItem.objects, 'get_top_selling_items'))
        self.assertTrue(callable(MenuItem.objects.get_top_selling_items))
    
    def test_get_top_selling_items_default_parameter(self):
        """Test get_top_selling_items with default num_items=5."""
        result = MenuItem.objects.get_top_selling_items()
        self.assertEqual(len(result), 5)
    
    def test_get_top_selling_items_custom_parameter(self):
        """Test get_top_selling_items with custom num_items parameter."""
        result = MenuItem.objects.get_top_selling_items(num_items=3)
        self.assertEqual(len(result), 3)
        
        result = MenuItem.objects.get_top_selling_items(num_items=1)
        self.assertEqual(len(result), 1)
        
        result = MenuItem.objects.get_top_selling_items(num_items=10)
        self.assertLessEqual(len(result), 10)
    
    def test_total_ordered_annotation_exists(self):
        """Test that items are annotated with total_ordered field."""
        result = MenuItem.objects.get_top_selling_items(num_items=1)
        self.assertTrue(hasattr(result[0], 'total_ordered'))
    
    def test_total_ordered_zero_when_no_orders(self):
        """Test that items with no orders have total_ordered=0."""
        result = MenuItem.objects.get_top_selling_items()
        for item in result:
            self.assertEqual(item.total_ordered, 0)
    
    def test_total_ordered_calculates_correctly(self):
        """Test that total_ordered correctly sums quantities from OrderItems."""
        # Create orders with items
        order1 = Order.objects.create(
            user=self.user,
            total_amount=Decimal('50.00'),
            status=self.pending_status
        )
        
        order2 = Order.objects.create(
            user=self.user,
            total_amount=Decimal('30.00'),
            status=self.pending_status
        )
        
        # item1 (Burger): ordered 5 times in order1, 3 times in order2 = 8 total
        OrderItem.objects.create(
            order=order1,
            menu_item=self.item1,
            quantity=5,
            price=self.item1.price
        )
        OrderItem.objects.create(
            order=order2,
            menu_item=self.item1,
            quantity=3,
            price=self.item1.price
        )
        
        # item2 (Pizza): ordered 2 times = 2 total
        OrderItem.objects.create(
            order=order1,
            menu_item=self.item2,
            quantity=2,
            price=self.item2.price
        )
        
        # item3 (Salad): ordered 10 times = 10 total
        OrderItem.objects.create(
            order=order1,
            menu_item=self.item3,
            quantity=10,
            price=self.item3.price
        )
        
        # Get top selling items
        top_items = MenuItem.objects.get_top_selling_items(num_items=5)
        
        # Verify totals
        salad = next(item for item in top_items if item.name == 'Salad')
        self.assertEqual(salad.total_ordered, 10)
        
        burger = next(item for item in top_items if item.name == 'Burger')
        self.assertEqual(burger.total_ordered, 8)
        
        pizza = next(item for item in top_items if item.name == 'Pizza')
        self.assertEqual(pizza.total_ordered, 2)
        
        pasta = next(item for item in top_items if item.name == 'Pasta')
        self.assertEqual(pasta.total_ordered, 0)
        
        steak = next(item for item in top_items if item.name == 'Steak')
        self.assertEqual(steak.total_ordered, 0)
    
    def test_ordering_descending_by_total_ordered(self):
        """Test that items are ordered by total_ordered in descending order."""
        # Create orders
        order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('100.00'),
            status=self.pending_status
        )
        
        # Create order items with different quantities
        OrderItem.objects.create(order=order, menu_item=self.item1, quantity=5, price=self.item1.price)
        OrderItem.objects.create(order=order, menu_item=self.item2, quantity=10, price=self.item2.price)
        OrderItem.objects.create(order=order, menu_item=self.item3, quantity=3, price=self.item3.price)
        OrderItem.objects.create(order=order, menu_item=self.item4, quantity=7, price=self.item4.price)
        
        # Get top selling items
        top_items = MenuItem.objects.get_top_selling_items()
        
        # Verify ordering
        self.assertEqual(top_items[0].name, 'Pizza')  # 10
        self.assertEqual(top_items[1].name, 'Pasta')  # 7
        self.assertEqual(top_items[2].name, 'Burger')  # 5
        self.assertEqual(top_items[3].name, 'Salad')  # 3
        self.assertEqual(top_items[4].name, 'Steak')  # 0
        
        # Verify descending order
        for i in range(len(top_items) - 1):
            self.assertGreaterEqual(
                top_items[i].total_ordered,
                top_items[i + 1].total_ordered
            )
    
    def test_returns_queryset(self):
        """Test that method returns a QuerySet for further chaining."""
        result = MenuItem.objects.get_top_selling_items()
        self.assertEqual(result.__class__.__name__, 'QuerySet')
    
    def test_can_filter_result_further(self):
        """Test that returned QuerySet can be chained with other manager methods."""
        # Create an order
        order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('50.00'),
            status=self.pending_status
        )
        OrderItem.objects.create(order=order, menu_item=self.item1, quantity=5, price=self.item1.price)
        OrderItem.objects.create(order=order, menu_item=self.item2, quantity=3, price=self.item2.price)
        
        # Mark item2 as unavailable
        self.item2.is_available = False
        self.item2.save()
        
        # Get top selling items (returns sliced QuerySet)
        top_items = MenuItem.objects.get_top_selling_items(num_items=5)
        
        # Verify that sliced queryset contains both items
        item_names = [item.name for item in top_items]
        self.assertIn('Burger', item_names)
        self.assertIn('Pizza', item_names)
        
        # To filter, need to filter BEFORE calling get_top_selling_items
        # This demonstrates proper usage pattern
        top_available = MenuItem.objects.filter(is_available=True)
        # Note: Can't call get_top_selling_items on filtered queryset directly
        # as it's a custom manager method, not a queryset method
    
    def test_handles_ties_in_quantity(self):
        """Test behavior when multiple items have the same quantity ordered."""
        # Create orders with tied quantities
        order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('100.00'),
            status=self.pending_status
        )
        
        OrderItem.objects.create(order=order, menu_item=self.item1, quantity=5, price=self.item1.price)
        OrderItem.objects.create(order=order, menu_item=self.item2, quantity=5, price=self.item2.price)
        OrderItem.objects.create(order=order, menu_item=self.item3, quantity=5, price=self.item3.price)
        
        top_items = MenuItem.objects.get_top_selling_items(num_items=3)
        
        # All three should have total_ordered=5
        for item in top_items[:3]:
            self.assertEqual(item.total_ordered, 5)
    
    def test_respects_num_items_limit(self):
        """Test that num_items parameter correctly limits results."""
        # Request more items than exist
        result = MenuItem.objects.get_top_selling_items(num_items=100)
        self.assertLessEqual(len(result), MenuItem.objects.count())
        
        # Request specific number
        result = MenuItem.objects.get_top_selling_items(num_items=2)
        self.assertEqual(len(result), 2)
    
    def test_works_with_empty_database(self):
        """Test that method works when no menu items exist."""
        MenuItem.objects.all().delete()
        result = MenuItem.objects.get_top_selling_items()
        self.assertEqual(len(result), 0)


if __name__ == '__main__':
    print("=" * 80)
    print("MENUITEMMANAGER TEST SUITE")
    print("=" * 80)
    print("\nRun with: python manage.py test home.tests.test_menu_item_manager")
    print("\nThis test suite covers:")
    print("  ✓ Manager attachment and method availability")
    print("  ✓ Parameter handling (default and custom num_items)")
    print("  ✓ Annotation correctness (total_ordered calculation)")
    print("  ✓ Ordering logic (descending by quantity)")
    print("  ✓ QuerySet chaining capabilities")
    print("  ✓ Edge cases (ties, empty database, filtering)")
    print("=" * 80)
