"""
Unit tests for the custom OrderManager.
Tests the get_active_orders() method and related functionality.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal

from orders.models import Order, OrderStatus, Customer
from orders.choices import OrderStatusChoices
from home.models import Restaurant, MenuItem


class OrderManagerTests(TestCase):
    """Test cases for the custom OrderManager."""
    
    def setUp(self):
        """Set up test data."""
        # Create test restaurant
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner_name='Test Owner',
            email='owner@test.com',
            phone_number='555-1234'
        )
        
        # Create test menu item
        self.menu_item = MenuItem.objects.create(
            name='Test Burger',
            description='A delicious test burger',
            price=Decimal('12.99'),
            restaurant=self.restaurant,
            is_available=True
        )
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test customer
        self.customer = Customer.objects.create(
            name='John Doe',
            phone='555-9876',
            email='john@example.com'
        )
        
        # Create all order statuses
        self.status_pending, _ = OrderStatus.objects.get_or_create(name=OrderStatusChoices.PENDING)
        self.status_processing, _ = OrderStatus.objects.get_or_create(name=OrderStatusChoices.PROCESSING)
        self.status_completed, _ = OrderStatus.objects.get_or_create(name=OrderStatusChoices.COMPLETED)
        self.status_cancelled, _ = OrderStatus.objects.get_or_create(name=OrderStatusChoices.CANCELLED)
    
    def test_get_active_orders_returns_pending_and_processing(self):
        """Test that get_active_orders returns only pending and processing orders."""
        # Create orders with different statuses
        order_pending = Order.objects.create(
            user=self.user,
            customer=self.customer,
            status=self.status_pending,
            total_amount=Decimal('25.99')
        )
        
        order_processing = Order.objects.create(
            user=self.user,
            customer=self.customer,
            status=self.status_processing,
            total_amount=Decimal('35.50')
        )
        
        order_completed = Order.objects.create(
            user=self.user,
            customer=self.customer,
            status=self.status_completed,
            total_amount=Decimal('42.00')
        )
        
        order_cancelled = Order.objects.create(
            user=self.user,
            customer=self.customer,
            status=self.status_cancelled,
            total_amount=Decimal('15.25')
        )
        
        # Test get_active_orders
        active_orders = Order.objects.get_active_orders()
        
        # Should return only pending and processing orders
        self.assertEqual(active_orders.count(), 2)
        self.assertIn(order_pending, active_orders)
        self.assertIn(order_processing, active_orders)
        self.assertNotIn(order_completed, active_orders)
        self.assertNotIn(order_cancelled, active_orders)
    
    def test_get_active_orders_empty_result(self):
        """Test get_active_orders when no active orders exist."""
        # Create only completed and cancelled orders
        Order.objects.create(
            user=self.user,
            customer=self.customer,
            status=self.status_completed,
            total_amount=Decimal('42.00')
        )
        
        Order.objects.create(
            user=self.user,
            customer=self.customer,
            status=self.status_cancelled,
            total_amount=Decimal('15.25')
        )
        
        # Test get_active_orders
        active_orders = Order.objects.get_active_orders()
        
        # Should return empty queryset
        self.assertEqual(active_orders.count(), 0)
        self.assertFalse(active_orders.exists())
    
    def test_get_active_orders_only_pending(self):
        """Test get_active_orders when only pending orders exist."""
        # Create only pending orders
        order1 = Order.objects.create(
            user=self.user,
            customer=self.customer,
            status=self.status_pending,
            total_amount=Decimal('25.99')
        )
        
        order2 = Order.objects.create(
            user=self.user,
            customer=self.customer,
            status=self.status_pending,
            total_amount=Decimal('18.75')
        )
        
        # Test get_active_orders
        active_orders = Order.objects.get_active_orders()
        
        # Should return both pending orders
        self.assertEqual(active_orders.count(), 2)
        self.assertIn(order1, active_orders)
        self.assertIn(order2, active_orders)
    
    def test_get_active_orders_only_processing(self):
        """Test get_active_orders when only processing orders exist."""
        # Create only processing orders
        order1 = Order.objects.create(
            user=self.user,
            customer=self.customer,
            status=self.status_processing,
            total_amount=Decimal('35.50')
        )
        
        order2 = Order.objects.create(
            user=self.user,
            customer=self.customer,
            status=self.status_processing,
            total_amount=Decimal('29.99')
        )
        
        # Test get_active_orders
        active_orders = Order.objects.get_active_orders()
        
        # Should return both processing orders
        self.assertEqual(active_orders.count(), 2)
        self.assertIn(order1, active_orders)
        self.assertIn(order2, active_orders)
    
    def test_get_active_orders_queryset_properties(self):
        """Test that get_active_orders returns a proper QuerySet."""
        # Create test orders
        Order.objects.create(
            user=self.user,
            customer=self.customer,
            status=self.status_pending,
            total_amount=Decimal('25.99')
        )
        
        Order.objects.create(
            user=self.user,
            customer=self.customer,
            status=self.status_processing,
            total_amount=Decimal('35.50')
        )
        
        # Test get_active_orders
        active_orders = Order.objects.get_active_orders()
        
        # Should be a QuerySet
        from django.db.models import QuerySet
        self.assertIsInstance(active_orders, QuerySet)
        
        # Should be iterable
        orders_list = list(active_orders)
        self.assertEqual(len(orders_list), 2)
        
        # Should support further filtering
        filtered_orders = active_orders.filter(total_amount__gt=Decimal('30.00'))
        self.assertEqual(filtered_orders.count(), 1)
    
    def test_get_active_orders_preserves_order_fields(self):
        """Test that get_active_orders preserves all order fields."""
        # Create test order
        order = Order.objects.create(
            user=self.user,
            customer=self.customer,
            status=self.status_pending,
            total_amount=Decimal('25.99')
        )
        
        # Get active orders
        active_orders = Order.objects.get_active_orders()
        retrieved_order = active_orders.first()
        
        # Verify all fields are preserved
        self.assertEqual(retrieved_order.id, order.id)
        self.assertEqual(retrieved_order.user, order.user)
        self.assertEqual(retrieved_order.customer, order.customer)
        self.assertEqual(retrieved_order.status, order.status)
        self.assertEqual(retrieved_order.total_amount, order.total_amount)
        self.assertEqual(retrieved_order.created_at, order.created_at)
    
    def test_custom_manager_does_not_break_default_behavior(self):
        """Test that adding custom manager doesn't break default Django functionality."""
        # Create test orders
        order1 = Order.objects.create(
            user=self.user,
            customer=self.customer,
            status=self.status_pending,
            total_amount=Decimal('25.99')
        )
        
        order2 = Order.objects.create(
            user=self.user,
            customer=self.customer,
            status=self.status_completed,
            total_amount=Decimal('42.00')
        )
        
        # Test default manager methods still work
        all_orders = Order.objects.all()
        self.assertEqual(all_orders.count(), 2)
        
        # Test get by ID
        retrieved_order = Order.objects.get(id=order1.id)
        self.assertEqual(retrieved_order, order1)
        
        # Test filter
        pending_orders = Order.objects.filter(status=self.status_pending)
        self.assertEqual(pending_orders.count(), 1)
        self.assertIn(order1, pending_orders)
        
        # Test create
        new_order = Order.objects.create(
            user=self.user,
            customer=self.customer,
            status=self.status_processing,
            total_amount=Decimal('15.00')
        )
        self.assertEqual(Order.objects.count(), 3)
    
    def test_manager_method_name_and_signature(self):
        """Test that the manager method has the correct name and signature."""
        # Verify the method exists
        self.assertTrue(hasattr(Order.objects, 'get_active_orders'))
        
        # Verify it's callable
        self.assertTrue(callable(getattr(Order.objects, 'get_active_orders')))
        
        # Verify it can be called without arguments
        try:
            result = Order.objects.get_active_orders()
            # Should not raise an exception
        except TypeError:
            self.fail("get_active_orders() method should not require arguments")


class OrderManagerIntegrationTests(TestCase):
    """Integration tests for OrderManager with related models."""
    
    def setUp(self):
        """Set up test data."""
        # Create test restaurant
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner_name='Test Owner',
            email='owner@test.com',
            phone_number='555-1234'
        )
        
        # Create test users
        self.user1 = User.objects.create_user(username='user1', email='user1@test.com')
        self.user2 = User.objects.create_user(username='user2', email='user2@test.com')
        
        # Create test customers
        self.customer1 = Customer.objects.create(name='Customer 1', phone='555-0001')
        self.customer2 = Customer.objects.create(name='Customer 2', phone='555-0002')
        
        # Create order statuses
        self.status_pending, _ = OrderStatus.objects.get_or_create(name=OrderStatusChoices.PENDING)
        self.status_processing, _ = OrderStatus.objects.get_or_create(name=OrderStatusChoices.PROCESSING)
        self.status_completed, _ = OrderStatus.objects.get_or_create(name=OrderStatusChoices.COMPLETED)
    
    def test_get_active_orders_across_multiple_users(self):
        """Test get_active_orders works correctly across multiple users."""
        # Create orders for different users
        Order.objects.create(user=self.user1, customer=self.customer1, status=self.status_pending, total_amount=Decimal('25.99'))
        Order.objects.create(user=self.user1, customer=self.customer1, status=self.status_completed, total_amount=Decimal('42.00'))
        Order.objects.create(user=self.user2, customer=self.customer2, status=self.status_processing, total_amount=Decimal('35.50'))
        Order.objects.create(user=self.user2, customer=self.customer2, status=self.status_completed, total_amount=Decimal('18.75'))
        
        # Get active orders
        active_orders = Order.objects.get_active_orders()
        
        # Should return active orders from both users
        self.assertEqual(active_orders.count(), 2)
        
        # Verify correct orders are returned
        statuses = [order.status.name for order in active_orders]
        self.assertIn(OrderStatusChoices.PENDING, statuses)
        self.assertIn(OrderStatusChoices.PROCESSING, statuses)
        self.assertNotIn(OrderStatusChoices.COMPLETED, statuses)
    
    def test_get_active_orders_with_related_data(self):
        """Test get_active_orders with select_related for performance."""
        # Create test order
        order = Order.objects.create(
            user=self.user1,
            customer=self.customer1,
            status=self.status_pending,
            total_amount=Decimal('25.99')
        )
        
        # Get active orders with related data
        active_orders = Order.objects.get_active_orders().select_related('user', 'customer', 'status')
        
        # Should be able to access related data without additional queries
        with self.assertNumQueries(1):  # Only one query for the select_related data
            for order in active_orders:
                # These should not trigger additional queries
                user_name = order.user.username
                customer_name = order.customer.name
                status_name = order.status.name