"""
Test cases for PaymentMethod API endpoints.

This test module provides comprehensive coverage for the PaymentMethod
API endpoints, including listing, filtering, and response format validation.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from orders.models import PaymentMethod


class PaymentMethodListAPITests(TestCase):
    """Test cases for the PaymentMethod list API endpoint."""
    
    def setUp(self):
        """Set up test data and API client."""
        self.client = APIClient()
        self.url = reverse('payment-method-list')
        
        # Create test payment methods
        self.credit_card = PaymentMethod.objects.create(
            name='Credit Card',
            description='Pay securely with Visa, Mastercard, or Amex',
            is_active=True
        )
        self.cash = PaymentMethod.objects.create(
            name='Cash',
            description='Pay with physical currency',
            is_active=True
        )
        self.paypal = PaymentMethod.objects.create(
            name='PayPal',
            description='Pay with PayPal account',
            is_active=True
        )
        self.inactive_method = PaymentMethod.objects.create(
            name='Check',
            description='Pay by check (no longer accepted)',
            is_active=False
        )
    
    def test_list_payment_methods_success(self):
        """Test successfully retrieving list of payment methods."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_only_active_payment_methods_returned(self):
        """Test that only active payment methods are returned."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return 3 active methods, not 4 total
        self.assertEqual(response.data['count'], 3)
        
        # Extract names from results
        returned_names = [item['name'] for item in response.data['results']]
        
        # Active methods should be in results
        self.assertIn('Credit Card', returned_names)
        self.assertIn('Cash', returned_names)
        self.assertIn('PayPal', returned_names)
        
        # Inactive method should NOT be in results
        self.assertNotIn('Check', returned_names)
    
    def test_payment_methods_ordered_alphabetically(self):
        """Test that payment methods are returned in alphabetical order by name."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        names = [item['name'] for item in response.data['results']]
        
        # Should be alphabetically sorted
        self.assertEqual(names, sorted(names))
        self.assertEqual(names, ['Cash', 'Credit Card', 'PayPal'])
    
    def test_response_contains_all_fields(self):
        """Test that each payment method contains all required fields."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        for item in response.data['results']:
            self.assertIn('id', item)
            self.assertIn('name', item)
            self.assertIn('description', item)
            self.assertIn('is_active', item)
    
    def test_response_format_structure(self):
        """Test that response has correct pagination structure."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check pagination structure
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)
        
        # Verify types
        self.assertIsInstance(response.data['count'], int)
        self.assertIsInstance(response.data['results'], list)
    
    def test_all_returned_methods_have_is_active_true(self):
        """Test that all returned payment methods have is_active=True."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        for item in response.data['results']:
            self.assertTrue(item['is_active'])
    
    def test_empty_results_when_no_active_methods(self):
        """Test response when no active payment methods exist."""
        # Deactivate all payment methods
        PaymentMethod.objects.all().update(is_active=False)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(response.data['results'], [])
    
    def test_get_method_allowed(self):
        """Test that GET method is allowed."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_post_method_not_allowed(self):
        """Test that POST method is not allowed (read-only endpoint)."""
        data = {
            'name': 'Bitcoin',
            'description': 'Pay with cryptocurrency',
            'is_active': True
        }
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_put_method_not_allowed(self):
        """Test that PUT method is not allowed."""
        response = self.client.put(self.url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_delete_method_not_allowed(self):
        """Test that DELETE method is not allowed."""
        response = self.client.delete(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_no_authentication_required(self):
        """Test that endpoint is accessible without authentication."""
        # Don't authenticate client
        response = self.client.get(self.url)
        
        # Should still work (public endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PaymentMethodSerializerTests(TestCase):
    """Test cases for PaymentMethod serialization."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.url = reverse('payment-method-list')
    
    def test_description_null_serialized_correctly(self):
        """Test that null description is serialized as null, not empty string."""
        payment_method = PaymentMethod.objects.create(
            name='Gift Card',
            description=None,
            is_active=True
        )
        
        response = self.client.get(self.url)
        
        gift_card_data = next(
            item for item in response.data['results'] 
            if item['name'] == 'Gift Card'
        )
        
        self.assertIsNone(gift_card_data['description'])
    
    def test_description_empty_string_serialized_correctly(self):
        """Test that empty string description is preserved."""
        payment_method = PaymentMethod.objects.create(
            name='Bank Transfer',
            description='',
            is_active=True
        )
        
        response = self.client.get(self.url)
        
        bank_transfer_data = next(
            item for item in response.data['results'] 
            if item['name'] == 'Bank Transfer'
        )
        
        self.assertEqual(bank_transfer_data['description'], '')
    
    def test_special_characters_in_name_serialized(self):
        """Test that special characters in name are properly serialized."""
        payment_method = PaymentMethod.objects.create(
            name='Credit/Debit Card',
            description='Cards with special chars!',
            is_active=True
        )
        
        response = self.client.get(self.url)
        
        special_char_data = next(
            item for item in response.data['results'] 
            if item['name'] == 'Credit/Debit Card'
        )
        
        self.assertEqual(special_char_data['name'], 'Credit/Debit Card')
    
    def test_unicode_characters_serialized(self):
        """Test that Unicode characters are properly serialized."""
        payment_method = PaymentMethod.objects.create(
            name='支付宝 (Alipay)',
            description='中文描述',
            is_active=True
        )
        
        response = self.client.get(self.url)
        
        unicode_data = next(
            item for item in response.data['results'] 
            if item['name'] == '支付宝 (Alipay)'
        )
        
        self.assertEqual(unicode_data['name'], '支付宝 (Alipay)')
        self.assertEqual(unicode_data['description'], '中文描述')


class PaymentMethodAPIBusinessLogicTests(TestCase):
    """Test cases for business logic scenarios with PaymentMethod API."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.url = reverse('payment-method-list')
    
    def test_adding_new_active_method_appears_in_list(self):
        """Test that newly added active payment method appears in API."""
        # Get initial count
        response = self.client.get(self.url)
        initial_count = response.data['count']
        
        # Add new payment method
        PaymentMethod.objects.create(
            name='Venmo',
            description='Digital wallet',
            is_active=True
        )
        
        # Get updated list
        response = self.client.get(self.url)
        
        self.assertEqual(response.data['count'], initial_count + 1)
        names = [item['name'] for item in response.data['results']]
        self.assertIn('Venmo', names)
    
    def test_deactivating_method_removes_from_list(self):
        """Test that deactivating a payment method removes it from API results."""
        # Create active payment method
        method = PaymentMethod.objects.create(
            name='Bitcoin',
            description='Cryptocurrency',
            is_active=True
        )
        
        # Verify it appears in list
        response = self.client.get(self.url)
        names = [item['name'] for item in response.data['results']]
        self.assertIn('Bitcoin', names)
        
        # Deactivate it
        method.is_active = False
        method.save()
        
        # Verify it's removed from list
        response = self.client.get(self.url)
        names = [item['name'] for item in response.data['results']]
        self.assertNotIn('Bitcoin', names)
    
    def test_reactivating_method_adds_back_to_list(self):
        """Test that reactivating a payment method adds it back to API results."""
        # Create inactive payment method
        method = PaymentMethod.objects.create(
            name='Wire Transfer',
            description='Bank wire',
            is_active=False
        )
        
        # Verify it doesn't appear in list
        response = self.client.get(self.url)
        names = [item['name'] for item in response.data['results']]
        self.assertNotIn('Wire Transfer', names)
        
        # Reactivate it
        method.is_active = True
        method.save()
        
        # Verify it appears in list
        response = self.client.get(self.url)
        names = [item['name'] for item in response.data['results']]
        self.assertIn('Wire Transfer', names)
    
    def test_large_number_of_payment_methods(self):
        """Test API performance with many payment methods."""
        # Create 50 active payment methods
        for i in range(50):
            PaymentMethod.objects.create(
                name=f'Payment Method {i:02d}',
                description=f'Description for method {i}',
                is_active=True
            )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 50)
    
    def test_payment_method_id_consistency(self):
        """Test that payment method IDs are stable across requests."""
        method = PaymentMethod.objects.create(
            name='Stable ID Test',
            is_active=True
        )
        
        # First request
        response1 = self.client.get(self.url)
        item1 = next(
            item for item in response1.data['results']
            if item['name'] == 'Stable ID Test'
        )
        
        # Second request
        response2 = self.client.get(self.url)
        item2 = next(
            item for item in response2.data['results']
            if item['name'] == 'Stable ID Test'
        )
        
        # IDs should match
        self.assertEqual(item1['id'], item2['id'])
        self.assertEqual(item1['id'], method.id)
