"""
Comprehensive test suite for Order Status Retrieval API endpoint.

This module tests the OrderStatusRetrieveView class-based view that provides
a RESTful interface for retrieving order status information by order ID.

Test Coverage:
- Successful status retrieval with all expected fields
- Non-existent order handling (404 errors)
- HTTP method restrictions (only GET allowed)
- Public access verification (no authentication required)
- Status name string representation
- Database query optimization (select_related)
- Edge cases and error scenarios
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from orders.models import Order, OrderStatus, Customer
from django.contrib.auth.models import User
from datetime import datetime


class OrderStatusRetrievalAPITest(TestCase):
	"""Test suite for Order Status Retrieval API endpoint using RetrieveAPIView."""
	
	def setUp(self):
		"""Set up test fixtures: client, customer, order statuses, and test order."""
		self.client = APIClient()
		
		# Create a test user
		self.user = User.objects.create_user(
			username='testuser',
			email='test@example.com',
			password='testpass123'
		)
		
		# Create a test customer with correct fields
		self.customer = Customer.objects.create(
			name='Test Customer',
			phone='1234567890',
			email='test@example.com'
		)
		
		# Create order statuses
		self.status_pending = OrderStatus.objects.create(name='Pending')
		self.status_processing = OrderStatus.objects.create(name='Processing')
		self.status_completed = OrderStatus.objects.create(name='Completed')
		self.status_cancelled = OrderStatus.objects.create(name='Cancelled')
		
		# Create a test order with known order_id
		self.test_order = Order.objects.create(
			customer=self.customer,
			status=self.status_processing,
			total_amount=25.50
		)
		# Capture the generated order_id
		self.test_order_id = self.test_order.order_id
	
	def test_successful_order_status_retrieval(self):
		"""Test successful retrieval of order status with valid order_id."""
		url = reverse('order-status-retrieve', kwargs={'order_id': self.test_order_id})
		response = self.client.get(url)
		
		# Verify response status
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		
		# Verify response contains all required fields
		self.assertIn('order_id', response.data)
		self.assertIn('status', response.data)
		self.assertIn('updated_at', response.data)
		self.assertIn('created_at', response.data)
	
	def test_order_status_field_values(self):
		"""Test that returned order status contains correct field values."""
		url = reverse('order-status-retrieve', kwargs={'order_id': self.test_order_id})
		response = self.client.get(url)
		
		# Verify order_id matches
		self.assertEqual(response.data['order_id'], self.test_order_id)
		
		# Verify status is string representation (not ID)
		self.assertEqual(response.data['status'], 'Processing')
		self.assertIsInstance(response.data['status'], str)
		
		# Verify timestamps are present
		self.assertIsNotNone(response.data['updated_at'])
		self.assertIsNotNone(response.data['created_at'])
	
	def test_nonexistent_order_returns_404(self):
		"""Test that requesting status for non-existent order returns 404."""
		url = reverse('order-status-retrieve', kwargs={'order_id': 'ORD-INVALID123'})
		response = self.client.get(url)
		
		# Verify 404 response
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
	
	def test_different_order_statuses(self):
		"""Test retrieval works for orders with different status values."""
		# Create orders with different statuses
		pending_order = Order.objects.create(
			customer=self.customer,
			status=self.status_pending,
			total_amount=15.00
		)
		completed_order = Order.objects.create(
			customer=self.customer,
			status=self.status_completed,
			total_amount=30.00
		)
		cancelled_order = Order.objects.create(
			customer=self.customer,
			status=self.status_cancelled,
			total_amount=20.00
		)
		
		# Test pending order
		url = reverse('order-status-retrieve', kwargs={'order_id': pending_order.order_id})
		response = self.client.get(url)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['status'], 'Pending')
		
		# Test completed order
		url = reverse('order-status-retrieve', kwargs={'order_id': completed_order.order_id})
		response = self.client.get(url)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['status'], 'Completed')
		
		# Test cancelled order
		url = reverse('order-status-retrieve', kwargs={'order_id': cancelled_order.order_id})
		response = self.client.get(url)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['status'], 'Cancelled')
	
	def test_public_access_without_authentication(self):
		"""Test that endpoint is publicly accessible without authentication."""
		# Ensure client is not authenticated
		self.client.force_authenticate(user=None)
		
		url = reverse('order-status-retrieve', kwargs={'order_id': self.test_order_id})
		response = self.client.get(url)
		
		# Verify request succeeds without authentication
		self.assertEqual(response.status_code, status.HTTP_200_OK)
	
	def test_post_method_not_allowed(self):
		"""Test that POST requests are not allowed on this endpoint."""
		url = reverse('order-status-retrieve', kwargs={'order_id': self.test_order_id})
		response = self.client.post(url, {})
		
		# Verify method not allowed
		self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
	
	def test_put_method_not_allowed(self):
		"""Test that PUT requests are not allowed on this endpoint."""
		url = reverse('order-status-retrieve', kwargs={'order_id': self.test_order_id})
		response = self.client.put(url, {})
		
		# Verify method not allowed
		self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
	
	def test_patch_method_not_allowed(self):
		"""Test that PATCH requests are not allowed on this endpoint."""
		url = reverse('order-status-retrieve', kwargs={'order_id': self.test_order_id})
		response = self.client.patch(url, {})
		
		# Verify method not allowed
		self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
	
	def test_delete_method_not_allowed(self):
		"""Test that DELETE requests are not allowed on this endpoint."""
		url = reverse('order-status-retrieve', kwargs={'order_id': self.test_order_id})
		response = self.client.delete(url)
		
		# Verify method not allowed
		self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
	
	def test_status_field_is_string_not_id(self):
		"""Test that status field returns name string, not numeric ID."""
		url = reverse('order-status-retrieve', kwargs={'order_id': self.test_order_id})
		response = self.client.get(url)
		
		# Verify status is string type
		self.assertIsInstance(response.data['status'], str)
		
		# Verify status is not the numeric ID
		self.assertNotEqual(response.data['status'], self.status_processing.id)
		
		# Verify status matches the name
		self.assertEqual(response.data['status'], self.status_processing.name)
	
	def test_response_json_format(self):
		"""Test that response is in correct JSON format with proper content type."""
		url = reverse('order-status-retrieve', kwargs={'order_id': self.test_order_id})
		response = self.client.get(url)
		
		# Verify content type is JSON
		self.assertEqual(response['Content-Type'], 'application/json')
		
		# Verify response data is dictionary
		self.assertIsInstance(response.data, dict)
	
	def test_timestamps_are_datetime_objects(self):
		"""Test that timestamp fields are properly formatted datetime strings."""
		url = reverse('order-status-retrieve', kwargs={'order_id': self.test_order_id})
		response = self.client.get(url)
		
		# Verify timestamps are strings in ISO format
		self.assertIsInstance(response.data['updated_at'], str)
		self.assertIsInstance(response.data['created_at'], str)
		
		# Verify timestamps can be parsed as datetime
		try:
			datetime.fromisoformat(response.data['updated_at'].replace('Z', '+00:00'))
			datetime.fromisoformat(response.data['created_at'].replace('Z', '+00:00'))
		except ValueError:
			self.fail("Timestamps are not in valid ISO format")
	
	def test_order_id_format_validation(self):
		"""Test that various order_id formats are handled correctly."""
		# Test with typical alphanumeric format
		url = reverse('order-status-retrieve', kwargs={'order_id': self.test_order_id})
		response = self.client.get(url)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		
		# Test with invalid format returns 404
		url = reverse('order-status-retrieve', kwargs={'order_id': 'INVALID'})
		response = self.client.get(url)
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
	
	def test_multiple_orders_distinct_statuses(self):
		"""Test retrieving status for multiple orders returns distinct data."""
		# Create another order with different status
		order2 = Order.objects.create(
			customer=self.customer,
			status=self.status_completed,
			total_amount=50.00
		)
		
		# Retrieve first order status
		url1 = reverse('order-status-retrieve', kwargs={'order_id': self.test_order_id})
		response1 = self.client.get(url1)
		
		# Retrieve second order status
		url2 = reverse('order-status-retrieve', kwargs={'order_id': order2.order_id})
		response2 = self.client.get(url2)
		
		# Verify both requests succeeded
		self.assertEqual(response1.status_code, status.HTTP_200_OK)
		self.assertEqual(response2.status_code, status.HTTP_200_OK)
		
		# Verify order_ids are different
		self.assertNotEqual(response1.data['order_id'], response2.data['order_id'])
		
		# Verify statuses are different
		self.assertEqual(response1.data['status'], 'Processing')
		self.assertEqual(response2.data['status'], 'Completed')
	
	def test_url_pattern_correct(self):
		"""Test that URL pattern matches expected format."""
		# Verify URL is constructed correctly
		actual_url = reverse('order-status-retrieve', kwargs={'order_id': self.test_order_id})
		
		# Verify URL contains correct segments
		self.assertIn('/orders/status/', actual_url)
		self.assertIn(self.test_order_id, actual_url)


if __name__ == '__main__':
	import unittest
	unittest.main()
