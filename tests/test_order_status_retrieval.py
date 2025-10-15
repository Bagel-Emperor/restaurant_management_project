"""
Test suite for Order Status Retrieval API endpoint.
Tests the get_order_status function-based view.
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from orders.models import Order, OrderStatus, Customer
from orders.choices import OrderStatusChoices


class OrderStatusRetrievalTestCase(TestCase):
    """Test cases for Order Status Retrieval endpoint."""
    
    def setUp(self):
        """Set up test client and create test data."""
        self.client = APIClient()
        
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
        
        # Create test orders with different statuses
        self.order_pending = Order.objects.create(
            customer=self.customer,
            user=self.user,
            total_amount=50.00,
            status=self.status_pending
        )
        
        self.order_processing = Order.objects.create(
            customer=self.customer,
            user=self.user,
            total_amount=75.00,
            status=self.status_processing
        )
        
        self.order_completed = Order.objects.create(
            customer=self.customer,
            user=self.user,
            total_amount=100.00,
            status=self.status_completed
        )
        
        self.order_cancelled = Order.objects.create(
            customer=self.customer,
            user=self.user,
            total_amount=25.00,
            status=self.status_cancelled
        )
    
    def test_get_status_pending_order(self):
        """Test retrieving status of a pending order."""
        url = reverse('order-status', kwargs={'order_id': self.order_pending.order_id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_id'], self.order_pending.order_id)
        self.assertEqual(response.data['status'], OrderStatusChoices.PENDING)
        self.assertIn('updated_at', response.data)
    
    def test_get_status_processing_order(self):
        """Test retrieving status of a processing order."""
        url = reverse('order-status', kwargs={'order_id': self.order_processing.order_id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_id'], self.order_processing.order_id)
        self.assertEqual(response.data['status'], OrderStatusChoices.PROCESSING)
        self.assertIn('updated_at', response.data)
    
    def test_get_status_completed_order(self):
        """Test retrieving status of a completed order."""
        url = reverse('order-status', kwargs={'order_id': self.order_completed.order_id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_id'], self.order_completed.order_id)
        self.assertEqual(response.data['status'], OrderStatusChoices.COMPLETED)
        self.assertIn('updated_at', response.data)
    
    def test_get_status_cancelled_order(self):
        """Test retrieving status of a cancelled order."""
        url = reverse('order-status', kwargs={'order_id': self.order_cancelled.order_id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_id'], self.order_cancelled.order_id)
        self.assertEqual(response.data['status'], OrderStatusChoices.CANCELLED)
        self.assertIn('updated_at', response.data)
    
    def test_get_status_nonexistent_order(self):
        """Test retrieving status of an order that doesn't exist."""
        url = reverse('order-status', kwargs={'order_id': 'ORD-NONEXISTENT'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Order not found')
        self.assertEqual(response.data['order_id'], 'ORD-NONEXISTENT')
    
    def test_public_access_no_authentication_required(self):
        """Test that the endpoint is publicly accessible (no auth required)."""
        # Ensure client is not authenticated
        self.client.force_authenticate(user=None)
        
        url = reverse('order-status', kwargs={'order_id': self.order_pending.order_id})
        response = self.client.get(url)
        
        # Should succeed without authentication
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_id'], self.order_pending.order_id)
    
    def test_response_structure(self):
        """Test that the response has the correct structure."""
        url = reverse('order-status', kwargs={'order_id': self.order_pending.order_id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify response contains required fields
        self.assertIn('order_id', response.data)
        self.assertIn('status', response.data)
        self.assertIn('updated_at', response.data)
        
        # Verify field types
        self.assertIsInstance(response.data['order_id'], str)
        self.assertIsInstance(response.data['status'], str)
        self.assertIsNotNone(response.data['updated_at'])
    
    def test_status_reflects_current_state(self):
        """Test that status changes are reflected immediately."""
        url = reverse('order-status', kwargs={'order_id': self.order_pending.order_id})
        
        # Get initial status
        response1 = self.client.get(url)
        self.assertEqual(response1.data['status'], OrderStatusChoices.PENDING)
        
        # Change status
        self.order_pending.status = self.status_processing
        self.order_pending.save()
        
        # Get updated status
        response2 = self.client.get(url)
        self.assertEqual(response2.data['status'], OrderStatusChoices.PROCESSING)
        
        # Verify updated_at changed
        self.assertNotEqual(response1.data['updated_at'], response2.data['updated_at'])
    
    def test_only_get_method_allowed(self):
        """Test that only GET requests are allowed."""
        url = reverse('order-status', kwargs={'order_id': self.order_pending.order_id})
        
        # POST should not be allowed
        response_post = self.client.post(url, {})
        self.assertEqual(response_post.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # PUT should not be allowed
        response_put = self.client.put(url, {})
        self.assertEqual(response_put.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # DELETE should not be allowed
        response_delete = self.client.delete(url)
        self.assertEqual(response_delete.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # PATCH should not be allowed
        response_patch = self.client.patch(url, {})
        self.assertEqual(response_patch.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_multiple_orders_independent_status(self):
        """Test that different orders have independent statuses."""
        url1 = reverse('order-status', kwargs={'order_id': self.order_pending.order_id})
        url2 = reverse('order-status', kwargs={'order_id': self.order_completed.order_id})
        
        response1 = self.client.get(url1)
        response2 = self.client.get(url2)
        
        # Verify each order has its own status
        self.assertEqual(response1.data['status'], OrderStatusChoices.PENDING)
        self.assertEqual(response2.data['status'], OrderStatusChoices.COMPLETED)
        self.assertNotEqual(response1.data['order_id'], response2.data['order_id'])
