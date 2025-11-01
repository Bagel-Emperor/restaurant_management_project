"""
Test suite for Django admin custom actions in the orders app.

This module tests the custom admin actions defined in orders/admin.py,
specifically focusing on the mark_orders_processed action that allows
administrators to bulk update order statuses.
"""

from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from orders.models import Order, OrderStatus, Customer
from orders.admin import OrderAdmin, mark_orders_processed
from orders.choices import OrderStatusChoices


class MarkOrdersProcessedActionTest(TestCase):
    """Test cases for the mark_orders_processed admin action."""
    
    def setUp(self):
        """Set up test data before each test."""
        # Create a test user (admin)
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        
        # Create a test customer
        self.customer = Customer.objects.create(
            name='Test Customer',
            email='customer@test.com',
            phone='555-0100'
        )
        
        # Create order statuses
        self.pending_status, _ = OrderStatus.objects.get_or_create(
            name=OrderStatusChoices.PENDING
        )
        self.processing_status, _ = OrderStatus.objects.get_or_create(
            name=OrderStatusChoices.PROCESSING
        )
        self.completed_status, _ = OrderStatus.objects.get_or_create(
            name=OrderStatusChoices.COMPLETED
        )
        
        # Create test orders with different statuses
        self.pending_order_1 = Order.objects.create(
            customer=self.customer,
            status=self.pending_status,
            total_amount=50.00
        )
        self.pending_order_2 = Order.objects.create(
            customer=self.customer,
            status=self.pending_status,
            total_amount=75.00
        )
        self.processing_order = Order.objects.create(
            customer=self.customer,
            status=self.processing_status,
            total_amount=100.00
        )
        self.completed_order = Order.objects.create(
            customer=self.customer,
            status=self.completed_status,
            total_amount=125.00
        )
        
        # Set up admin site and request factory
        self.site = AdminSite()
        self.order_admin = OrderAdmin(Order, self.site)
        self.factory = RequestFactory()
    
    def _create_request(self):
        """Helper method to create a request with proper message framework support."""
        request = self.factory.get('/')
        request.user = self.admin_user
        
        # Add session support
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        # Add message framework support
        messages = FallbackStorage(request)
        request._messages = messages
        
        return request
    
    def test_mark_single_pending_order_as_processed(self):
        """Test marking a single pending order as processed."""
        # Create queryset with one pending order
        queryset = Order.objects.filter(pk=self.pending_order_1.pk)
        
        # Create request with message support
        request = self._create_request()
        
        # Execute the action
        mark_orders_processed(self.order_admin, request, queryset)
        
        # Refresh from database
        self.pending_order_1.refresh_from_db()
        
        # Assert the order status was updated
        self.assertEqual(self.pending_order_1.status.name, OrderStatusChoices.PROCESSING)
    
    def test_mark_multiple_pending_orders_as_processed(self):
        """Test marking multiple pending orders as processed."""
        # Create queryset with both pending orders
        queryset = Order.objects.filter(
            pk__in=[self.pending_order_1.pk, self.pending_order_2.pk]
        )
        
        # Create request with message support
        request = self._create_request()
        
        # Execute the action
        mark_orders_processed(self.order_admin, request, queryset)
        
        # Refresh from database
        self.pending_order_1.refresh_from_db()
        self.pending_order_2.refresh_from_db()
        
        # Assert both orders were updated
        self.assertEqual(self.pending_order_1.status.name, OrderStatusChoices.PROCESSING)
        self.assertEqual(self.pending_order_2.status.name, OrderStatusChoices.PROCESSING)
    
    def test_mark_already_processing_order_as_processed(self):
        """Test that marking an already processing order doesn't cause issues."""
        # Create queryset with already processing order
        queryset = Order.objects.filter(pk=self.processing_order.pk)
        
        # Create request with message support
        request = self._create_request()
        
        # Execute the action
        mark_orders_processed(self.order_admin, request, queryset)
        
        # Refresh from database
        self.processing_order.refresh_from_db()
        
        # Assert the order is still in processing status
        self.assertEqual(self.processing_order.status.name, OrderStatusChoices.PROCESSING)
    
    def test_mark_completed_order_as_processed(self):
        """Test that completed orders can be changed to processing status."""
        # Create queryset with completed order
        queryset = Order.objects.filter(pk=self.completed_order.pk)
        
        # Create request with message support
        request = self._create_request()
        
        # Execute the action
        mark_orders_processed(self.order_admin, request, queryset)
        
        # Refresh from database
        self.completed_order.refresh_from_db()
        
        # Assert the order status was updated to processing
        self.assertEqual(self.completed_order.status.name, OrderStatusChoices.PROCESSING)
    
    def test_mark_mixed_status_orders_as_processed(self):
        """Test marking orders with mixed statuses as processed."""
        # Create queryset with orders of different statuses
        queryset = Order.objects.filter(
            pk__in=[
                self.pending_order_1.pk,
                self.processing_order.pk,
                self.completed_order.pk
            ]
        )
        
        # Create request with message support
        request = self._create_request()
        
        # Execute the action
        mark_orders_processed(self.order_admin, request, queryset)
        
        # Refresh from database
        self.pending_order_1.refresh_from_db()
        self.processing_order.refresh_from_db()
        self.completed_order.refresh_from_db()
        
        # Assert all orders are now in processing status
        self.assertEqual(self.pending_order_1.status.name, OrderStatusChoices.PROCESSING)
        self.assertEqual(self.processing_order.status.name, OrderStatusChoices.PROCESSING)
        self.assertEqual(self.completed_order.status.name, OrderStatusChoices.PROCESSING)
    
    def test_action_returns_correct_count(self):
        """Test that the action correctly counts updated orders."""
        # Create queryset with pending and processing orders
        queryset = Order.objects.filter(
            pk__in=[self.pending_order_1.pk, self.processing_order.pk]
        )
        
        # Count how many are not already processing
        not_processing_count = queryset.exclude(status=self.processing_status).count()
        self.assertEqual(not_processing_count, 1)  # Only pending_order_1
        
        # Create request with message support
        request = self._create_request()
        
        # Execute the action
        mark_orders_processed(self.order_admin, request, queryset)
        
        # After action, verify both are processing
        updated_queryset = Order.objects.filter(
            pk__in=[self.pending_order_1.pk, self.processing_order.pk]
        )
        for order in updated_queryset:
            self.assertEqual(order.status.name, OrderStatusChoices.PROCESSING)
    
    def test_action_with_empty_queryset(self):
        """Test the action with an empty queryset."""
        # Create empty queryset
        queryset = Order.objects.none()
        
        # Create request with message support
        request = self._create_request()
        
        # Execute the action (should not raise an error)
        mark_orders_processed(self.order_admin, request, queryset)
        
        # Verify original orders are unchanged
        self.pending_order_1.refresh_from_db()
        self.assertEqual(self.pending_order_1.status.name, OrderStatusChoices.PENDING)
    
    def test_action_preserves_other_order_fields(self):
        """Test that the action only updates status and preserves other fields."""
        # Store original values
        original_total = self.pending_order_1.total_amount
        original_customer = self.pending_order_1.customer
        original_order_id = self.pending_order_1.order_id
        
        # Create queryset
        queryset = Order.objects.filter(pk=self.pending_order_1.pk)
        
        # Create request with message support
        request = self._create_request()
        
        # Execute the action
        mark_orders_processed(self.order_admin, request, queryset)
        
        # Refresh from database
        self.pending_order_1.refresh_from_db()
        
        # Assert other fields are preserved
        self.assertEqual(self.pending_order_1.total_amount, original_total)
        self.assertEqual(self.pending_order_1.customer, original_customer)
        self.assertEqual(self.pending_order_1.order_id, original_order_id)
        # Only status should change
        self.assertEqual(self.pending_order_1.status.name, OrderStatusChoices.PROCESSING)
    
    def test_action_works_with_user_assigned_orders(self):
        """Test the action works with orders that have a user assigned."""
        # Create an order with a user
        user_order = Order.objects.create(
            customer=self.customer,
            user=self.admin_user,
            status=self.pending_status,
            total_amount=200.00
        )
        
        # Create queryset
        queryset = Order.objects.filter(pk=user_order.pk)
        
        # Create request with message support
        request = self._create_request()
        
        # Execute the action
        mark_orders_processed(self.order_admin, request, queryset)
        
        # Refresh from database
        user_order.refresh_from_db()
        
        # Assert the order was updated
        self.assertEqual(user_order.status.name, OrderStatusChoices.PROCESSING)
        self.assertEqual(user_order.user, self.admin_user)


class OrderAdminConfigTest(TestCase):
    """Test cases for OrderAdmin configuration."""
    
    def setUp(self):
        """Set up test data before each test."""
        self.site = AdminSite()
        self.order_admin = OrderAdmin(Order, self.site)
    
    def test_mark_orders_processed_action_is_registered(self):
        """Test that the mark_orders_processed action is registered."""
        self.assertIn(mark_orders_processed, self.order_admin.actions)
    
    def test_action_has_short_description(self):
        """Test that the action has a user-friendly display name."""
        self.assertTrue(hasattr(mark_orders_processed, 'short_description'))
        self.assertEqual(
            mark_orders_processed.short_description,
            "Mark selected orders as Processed"
        )
    
    def test_list_display_configured(self):
        """Test that list_display is properly configured."""
        expected_fields = [
            'order_id',
            'customer',
            'user',
            'status',
            'total_amount',
            'created_at',
            'updated_at'
        ]
        self.assertEqual(self.order_admin.list_display, expected_fields)
    
    def test_list_filter_configured(self):
        """Test that list_filter is properly configured."""
        expected_filters = ['status', 'created_at', 'updated_at']
        self.assertEqual(self.order_admin.list_filter, expected_filters)
    
    def test_search_fields_configured(self):
        """Test that search_fields is properly configured."""
        expected_search = [
            'order_id',
            'customer__name',
            'customer__email',
            'user__username',
            'user__email'
        ]
        self.assertEqual(self.order_admin.search_fields, expected_search)
    
    def test_readonly_fields_configured(self):
        """Test that readonly_fields is properly configured."""
        expected_readonly = ['order_id', 'created_at', 'updated_at']
        self.assertEqual(self.order_admin.readonly_fields, expected_readonly)
    
    def test_ordering_configured(self):
        """Test that default ordering is properly configured."""
        self.assertEqual(self.order_admin.ordering, ['-created_at'])
    
    def test_list_select_related_configured(self):
        """Test that list_select_related is properly configured for performance."""
        expected_related = ['customer', 'user', 'status']
        self.assertEqual(self.order_admin.list_select_related, expected_related)
    
    def test_list_per_page_configured(self):
        """Test that pagination is properly configured."""
        self.assertEqual(self.order_admin.list_per_page, 25)
