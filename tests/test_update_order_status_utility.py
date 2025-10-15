"""
Test suite for order status update utility function.
Tests the update_order_status utility function in orders/utils.py.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from orders.models import Order, OrderStatus, Customer
from orders.choices import OrderStatusChoices
from orders.utils import update_order_status


class UpdateOrderStatusUtilityTestCase(TestCase):
    """Test cases for update_order_status utility function."""
    
    def setUp(self):
        """Set up test data."""
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Create a test customer
        self.customer = Customer.objects.create(
            name='Test Customer',
            email='customer@test.com',
            phone='1234567890'
        )
        
        # Create order statuses
        self.status_pending = OrderStatus.objects.create(name=OrderStatusChoices.PENDING)
        self.status_processing = OrderStatus.objects.create(name=OrderStatusChoices.PROCESSING)
        self.status_completed = OrderStatus.objects.create(name=OrderStatusChoices.COMPLETED)
        self.status_cancelled = OrderStatus.objects.create(name=OrderStatusChoices.CANCELLED)
        
        # Create a test order
        self.order = Order.objects.create(
            customer=self.customer,
            user=self.user,
            total_amount=100.00,
            status=self.status_pending
        )
    
    def test_update_status_pending_to_processing(self):
        """Test updating order status from Pending to Processing."""
        result = update_order_status(
            self.order.order_id,
            OrderStatusChoices.PROCESSING,
            'testuser'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], 'Order status updated successfully')
        self.assertEqual(result['order_id'], self.order.order_id)
        self.assertEqual(result['previous_status'], OrderStatusChoices.PENDING)
        self.assertEqual(result['new_status'], OrderStatusChoices.PROCESSING)
        
        # Verify database was updated
        self.order.refresh_from_db()
        self.assertEqual(self.order.status.name, OrderStatusChoices.PROCESSING)
    
    def test_update_status_processing_to_completed(self):
        """Test updating order status from Processing to Completed."""
        # Set initial status to Processing
        self.order.status = self.status_processing
        self.order.save()
        
        result = update_order_status(
            self.order.order_id,
            OrderStatusChoices.COMPLETED,
            'admin'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['previous_status'], OrderStatusChoices.PROCESSING)
        self.assertEqual(result['new_status'], OrderStatusChoices.COMPLETED)
        
        # Verify database was updated
        self.order.refresh_from_db()
        self.assertEqual(self.order.status.name, OrderStatusChoices.COMPLETED)
    
    def test_update_status_to_cancelled(self):
        """Test updating order status to Cancelled."""
        result = update_order_status(
            self.order.order_id,
            OrderStatusChoices.CANCELLED,
            'customer'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['new_status'], OrderStatusChoices.CANCELLED)
        
        # Verify database was updated
        self.order.refresh_from_db()
        self.assertEqual(self.order.status.name, OrderStatusChoices.CANCELLED)
    
    def test_update_status_same_as_current(self):
        """Test updating order to its current status (no change needed)."""
        result = update_order_status(
            self.order.order_id,
            OrderStatusChoices.PENDING,  # Same as current
            'testuser'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('already has status', result['message'])
        self.assertEqual(result['previous_status'], OrderStatusChoices.PENDING)
        self.assertEqual(result['new_status'], OrderStatusChoices.PENDING)
    
    def test_update_status_nonexistent_order(self):
        """Test updating status for an order that doesn't exist."""
        result = update_order_status(
            'ORD-NONEXISTENT',
            OrderStatusChoices.PROCESSING,
            'testuser'
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['message'], 'Order not found')
        self.assertEqual(result['order_id'], 'ORD-NONEXISTENT')
        self.assertIn('No order found with ID', result['error'])
    
    def test_update_status_invalid_status(self):
        """Test updating order with an invalid status value."""
        result = update_order_status(
            self.order.order_id,
            'InvalidStatus',
            'testuser'
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['message'], 'Invalid status provided')
        self.assertIn('Status must be one of', result['error'])
        
        # Verify order status unchanged
        self.order.refresh_from_db()
        self.assertEqual(self.order.status.name, OrderStatusChoices.PENDING)
    
    def test_update_status_empty_status(self):
        """Test updating order with empty status."""
        result = update_order_status(
            self.order.order_id,
            '',
            'testuser'
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['message'], 'Invalid status provided')
    
    def test_update_status_without_user_info(self):
        """Test updating status without providing user_info (should default to 'system')."""
        result = update_order_status(
            self.order.order_id,
            OrderStatusChoices.PROCESSING
            # user_info not provided
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['new_status'], OrderStatusChoices.PROCESSING)
    
    def test_update_status_creates_status_object_if_missing(self):
        """Test that function creates OrderStatus object if it doesn't exist."""
        # Delete all status objects except Pending
        OrderStatus.objects.exclude(name=OrderStatusChoices.PENDING).delete()
        
        result = update_order_status(
            self.order.order_id,
            OrderStatusChoices.COMPLETED,  # This status doesn't exist yet
            'admin'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['new_status'], OrderStatusChoices.COMPLETED)
        
        # Verify the OrderStatus object was created
        self.assertTrue(OrderStatus.objects.filter(name=OrderStatusChoices.COMPLETED).exists())
    
    def test_update_status_multiple_orders_independent(self):
        """Test that updating one order doesn't affect others."""
        # Create another order
        order2 = Order.objects.create(
            customer=self.customer,
            user=self.user,
            total_amount=50.00,
            status=self.status_pending
        )
        
        # Update first order
        result1 = update_order_status(
            self.order.order_id,
            OrderStatusChoices.COMPLETED,
            'admin'
        )
        
        self.assertTrue(result1['success'])
        
        # Verify second order unchanged
        order2.refresh_from_db()
        self.assertEqual(order2.status.name, OrderStatusChoices.PENDING)
    
    def test_update_status_all_valid_transitions(self):
        """Test all valid status transitions."""
        transitions = [
            (OrderStatusChoices.PENDING, OrderStatusChoices.PROCESSING),
            (OrderStatusChoices.PROCESSING, OrderStatusChoices.COMPLETED),
        ]
        
        for from_status, to_status in transitions:
            # Set order to from_status
            status_obj = OrderStatus.objects.get(name=from_status)
            self.order.status = status_obj
            self.order.save()
            
            # Update to to_status
            result = update_order_status(
                self.order.order_id,
                to_status,
                'testuser'
            )
            
            self.assertTrue(result['success'], f"Failed transition from {from_status} to {to_status}")
            self.assertEqual(result['previous_status'], from_status)
            self.assertEqual(result['new_status'], to_status)
            
            # Verify database
            self.order.refresh_from_db()
            self.assertEqual(self.order.status.name, to_status)
    
    def test_update_status_return_structure(self):
        """Test that return dictionary has the correct structure."""
        result = update_order_status(
            self.order.order_id,
            OrderStatusChoices.PROCESSING,
            'admin'
        )
        
        # Verify keys in successful response
        self.assertIn('success', result)
        self.assertIn('message', result)
        self.assertIn('order_id', result)
        self.assertIn('previous_status', result)
        self.assertIn('new_status', result)
        self.assertNotIn('error', result)  # Error key should not be present on success
        
        # Verify types
        self.assertIsInstance(result['success'], bool)
        self.assertIsInstance(result['message'], str)
        self.assertIsInstance(result['order_id'], str)
        self.assertIsInstance(result['previous_status'], str)
        self.assertIsInstance(result['new_status'], str)
    
    def test_update_status_error_return_structure(self):
        """Test that error response has the correct structure."""
        result = update_order_status(
            'ORD-INVALID',
            OrderStatusChoices.PROCESSING,
            'testuser'
        )
        
        # Verify keys in error response
        self.assertIn('success', result)
        self.assertIn('message', result)
        self.assertIn('order_id', result)
        self.assertIn('error', result)
        
        # Verify types
        self.assertIsInstance(result['success'], bool)
        self.assertFalse(result['success'])
        self.assertIsInstance(result['error'], str)
    
    def test_update_status_case_sensitive(self):
        """Test that status names are case-sensitive."""
        result = update_order_status(
            self.order.order_id,
            'processing',  # lowercase (invalid)
            'testuser'
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['message'], 'Invalid status provided')
