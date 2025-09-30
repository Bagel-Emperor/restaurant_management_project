"""
Test suite for Orders utility functions.

This module contains comprehensive tests for the unique ID generation functions,
including validation, collision handling, edge cases, and security tests.
"""

from django.test import TestCase, override_settings
from django.db import transaction
from unittest.mock import patch, MagicMock
import string
import secrets

from orders.models import Order, OrderStatus
from orders.utils import (
    generate_unique_order_id,
    generate_order_number,
    generate_short_id,
    validate_order_id_format,
    DEFAULT_ORDER_ID_LENGTH,
    DEFAULT_ORDER_PREFIX,
    DEFAULT_SHORT_ID_LENGTH
)
from orders.choices import OrderStatusChoices


class GenerateUniqueOrderIDTestCase(TestCase):
    """
    Test case for unique order ID generation functionality.
    Tests the core generate_unique_order_id function.
    """
    
    def setUp(self):
        """Set up test data for each test method."""
        # Create a default order status for testing
        self.default_status, _ = OrderStatus.objects.get_or_create(
            name=OrderStatusChoices.PENDING
        )
    
    def test_generate_basic_id_without_model(self):
        """Test basic ID generation without database model checking."""
        order_id = generate_unique_order_id(length=8, prefix='TEST-')
        
        # Check structure
        self.assertTrue(order_id.startswith('TEST-'))
        self.assertEqual(len(order_id), 13)  # 'TEST-' (5) + 8 chars
        
        # Check only safe characters used
        id_part = order_id[5:]  # Remove 'TEST-' prefix
        safe_alphabet = string.ascii_uppercase + string.digits
        safe_alphabet = safe_alphabet.replace('0', '').replace('O', '').replace('1', '').replace('I', '')
        for char in id_part:
            self.assertIn(char, safe_alphabet)
    
    def test_generate_id_with_model_checking(self):
        """Test ID generation with database uniqueness checking."""
        # Create an order to test uniqueness against
        existing_order = Order.objects.create(
            total_amount=25.99,
            status=self.default_status,
            order_id='ORD-EXISTING'
        )
        
        # Generate new ID
        new_id = generate_unique_order_id(
            length=8,
            prefix='ORD-',
            model_class=Order,
            field_name='order_id'
        )
        
        # Should be different from existing
        self.assertNotEqual(new_id, existing_order.order_id)
        self.assertTrue(new_id.startswith('ORD-'))
        self.assertEqual(len(new_id), 12)  # 'ORD-' (4) + 8 chars
    
    def test_generate_id_collision_retry(self):
        """Test that collision detection works and function retries."""
        # Mock secrets.choice to return predictable values
        mock_choices = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'] * 20  # More values to prevent StopIteration
        choice_iter = iter(mock_choices)
        
        with patch('orders.utils.secrets.choice', side_effect=lambda x: next(choice_iter)):
            # Create an order with the ID that will be generated first
            existing_order = Order.objects.create(
                total_amount=15.50,
                status=self.default_status,
                order_id='ORD-ABCDEFGH'
            )
            
            # Generate new ID - should retry and get a different one
            new_id = generate_unique_order_id(
                length=8,
                prefix='ORD-',
                model_class=Order,
                field_name='order_id'
            )
            
            # Should get the second attempt
            self.assertEqual(new_id, 'ORD-BCDEFGHA')
            self.assertNotEqual(new_id, existing_order.order_id)
    
    def test_generate_id_max_attempts_exceeded(self):
        """Test that function raises error after max attempts exceeded."""
        # Mock to always return the same value
        with patch('orders.utils.secrets.choice', return_value='A'):
            # Create an order with the ID that will always be generated
            existing_order = Order.objects.create(
                total_amount=30.00,
                status=self.default_status,
                order_id='ORD-AAAAAAAA'
            )
            
            # Should raise ValueError after max attempts
            with self.assertRaises(ValueError) as context:
                generate_unique_order_id(
                    length=8,
                    prefix='ORD-',
                    model_class=Order,
                    field_name='order_id'
                )
            
            self.assertIn("Unable to generate unique ID after", str(context.exception))
    
    def test_generate_id_database_error_handling(self):
        """Test handling of database errors during uniqueness checking."""
        with patch.object(Order.objects, 'filter') as mock_filter:
            # Mock database error
            mock_filter.side_effect = Exception("Database connection error")
            
            # Should raise ValueError after retries
            with self.assertRaises(ValueError):
                generate_unique_order_id(
                    length=6,
                    prefix='ERR-',
                    model_class=Order,
                    field_name='order_id'
                )
    
    def test_generate_id_different_lengths(self):
        """Test ID generation with different lengths."""
        lengths_to_test = [4, 6, 8, 10, 12]
        
        for length in lengths_to_test:
            with self.subTest(length=length):
                order_id = generate_unique_order_id(length=length, prefix='TEST-')
                expected_total_length = 5 + length  # 'TEST-' + length
                self.assertEqual(len(order_id), expected_total_length)
    
    def test_generate_id_no_prefix(self):
        """Test ID generation without prefix."""
        order_id = generate_unique_order_id(length=6)
        
        self.assertEqual(len(order_id), 6)
        # Check safe characters
        safe_alphabet = string.ascii_uppercase + string.digits
        safe_alphabet = safe_alphabet.replace('0', '').replace('O', '').replace('1', '').replace('I', '')
        for char in order_id:
            self.assertIn(char, safe_alphabet)


class GenerateOrderNumberTestCase(TestCase):
    """
    Test case for generate_order_number convenience function.
    """
    
    def setUp(self):
        """Set up test data."""
        self.default_status, _ = OrderStatus.objects.get_or_create(
            name=OrderStatusChoices.PENDING
        )
    
    def test_generate_order_number_format(self):
        """Test that order numbers have correct format."""
        order_number = generate_order_number()
        
        self.assertTrue(order_number.startswith('ORD-'))
        self.assertEqual(len(order_number), 12)  # 'ORD-' + 8 chars
    
    def test_generate_order_number_uniqueness(self):
        """Test that order numbers are unique."""
        # Create an existing order
        existing_order = Order.objects.create(
            total_amount=45.00,
            status=self.default_status,
            order_id='ORD-TESTEXST'
        )
        
        # Generate new order number
        new_number = generate_order_number(model_class=Order)
        
        self.assertNotEqual(new_number, existing_order.order_id)
        self.assertTrue(new_number.startswith('ORD-'))
    
    def test_multiple_order_numbers_unique(self):
        """Test that multiple generated order numbers are unique."""
        numbers = []
        for _ in range(10):
            number = generate_order_number()
            numbers.append(number)
        
        # All should be unique
        self.assertEqual(len(numbers), len(set(numbers)))


class GenerateShortIDTestCase(TestCase):
    """
    Test case for generate_short_id function.
    """
    
    def test_generate_short_id_default_length(self):
        """Test short ID generation with default length."""
        short_id = generate_short_id()
        
        self.assertEqual(len(short_id), 6)
        # No prefix by default
        self.assertFalse(short_id.startswith('ORD-'))
    
    def test_generate_short_id_custom_length(self):
        """Test short ID generation with custom length."""
        for length in [4, 8, 10]:
            with self.subTest(length=length):
                short_id = generate_short_id(length=length)
                self.assertEqual(len(short_id), length)
    
    def test_generate_short_id_safe_characters(self):
        """Test that short IDs only use safe characters."""
        short_id = generate_short_id(length=8)
        
        safe_alphabet = string.ascii_uppercase + string.digits
        safe_alphabet = safe_alphabet.replace('0', '').replace('O', '').replace('1', '').replace('I', '')
        
        for char in short_id:
            self.assertIn(char, safe_alphabet)


class ValidateOrderIDFormatTestCase(TestCase):
    """
    Test case for order ID format validation.
    """
    
    def test_validate_correct_format(self):
        """Test validation of correctly formatted order IDs."""
        valid_ids = [
            ('ORD-A7X9K2M5', 'ORD-', 12),
            ('TEST-ABCD', 'TEST-', 9),
            ('B8N4P2', '', 6),
            ('XYZ-ABC23DEF', 'XYZ-', 12)
        ]
        
        for order_id, prefix, length in valid_ids:
            with self.subTest(order_id=order_id):
                self.assertTrue(
                    validate_order_id_format(order_id, prefix, length)
                )
    
    def test_validate_incorrect_format(self):
        """Test validation of incorrectly formatted order IDs."""
        invalid_ids = [
            ('', 'ORD-', 12),                    # Empty string
            ('ORD-A7X9K2M5', 'TEST-', 12),       # Wrong prefix
            ('ORD-A7X9K2M5', 'ORD-', 10),        # Wrong length
            ('ORD-A7X0K2M5', 'ORD-', 12),        # Contains '0'
            ('ORD-A7XOK2M5', 'ORD-', 12),        # Contains 'O'
            ('ORD-A7X1K2M5', 'ORD-', 12),        # Contains '1'
            ('ORD-A7XIK2M5', 'ORD-', 12),        # Contains 'I'
            ('ord-a7x9k2m5', 'ORD-', 12),        # Lowercase
        ]
        
        for order_id, prefix, length in invalid_ids:
            with self.subTest(order_id=order_id):
                self.assertFalse(
                    validate_order_id_format(order_id, prefix, length)
                )
    
    def test_validate_partial_parameters(self):
        """Test validation with partial parameters."""
        # Test with prefix only
        self.assertTrue(validate_order_id_format('ORD-ABCDEF', 'ORD-'))
        self.assertFalse(validate_order_id_format('TEST-ABCDEF', 'ORD-'))
        
        # Test with length only
        self.assertTrue(validate_order_id_format('ABCDEF', expected_length=6))
        self.assertFalse(validate_order_id_format('ABCDEF', expected_length=8))
        
        # Test with neither
        self.assertTrue(validate_order_id_format('ABCDEF'))
        self.assertFalse(validate_order_id_format('ABC0EF'))  # Contains '0'


class OrderModelIntegrationTestCase(TestCase):
    """
    Test case for Order model integration with utility functions.
    """
    
    def setUp(self):
        """Set up test data."""
        self.default_status, _ = OrderStatus.objects.get_or_create(
            name=OrderStatusChoices.PENDING
        )
    
    def test_order_automatic_id_generation(self):
        """Test that Order model automatically generates order_id on save."""
        order = Order.objects.create(
            total_amount=19.99,
            status=self.default_status
        )
        
        # Should have generated an order_id
        self.assertIsNotNone(order.order_id)
        self.assertTrue(order.order_id.startswith('ORD-'))
        self.assertEqual(len(order.order_id), 12)
    
    def test_order_preserves_existing_id(self):
        """Test that Order model preserves manually set order_id."""
        custom_id = 'CUSTOM-12345'
        order = Order.objects.create(
            total_amount=29.99,
            status=self.default_status,
            order_id=custom_id
        )
        
        # Should preserve the custom ID
        self.assertEqual(order.order_id, custom_id)
    
    def test_order_str_representation(self):
        """Test Order string representation uses order_id."""
        order = Order.objects.create(
            total_amount=35.00,
            status=self.default_status
        )
        
        expected_str = f"Order {order.order_id} - {self.default_status.name}"
        self.assertEqual(str(order), expected_str)
    
    def test_multiple_orders_unique_ids(self):
        """Test that multiple orders get unique IDs."""
        orders = []
        for i in range(5):
            order = Order.objects.create(
                total_amount=10.00 + i,
                status=self.default_status
            )
            orders.append(order)
        
        # All order IDs should be unique
        order_ids = [order.order_id for order in orders]
        self.assertEqual(len(order_ids), len(set(order_ids)))
        
        # All should follow the format
        for order_id in order_ids:
            self.assertTrue(order_id.startswith('ORD-'))
            self.assertEqual(len(order_id), 12)


class ConstantsTestCase(TestCase):
    """
    Test case for module constants.
    """
    
    def test_constants_values(self):
        """Test that constants have expected values."""
        self.assertEqual(DEFAULT_ORDER_ID_LENGTH, 8)
        self.assertEqual(DEFAULT_ORDER_PREFIX, 'ORD-')
        self.assertEqual(DEFAULT_SHORT_ID_LENGTH, 6)


class SecurityTestCase(TestCase):
    """
    Test case for security aspects of ID generation.
    """
    
    def test_uses_cryptographically_secure_random(self):
        """Test that secrets module is used for cryptographic security."""
        with patch('orders.utils.secrets.choice') as mock_choice:
            mock_choice.return_value = 'A'
            
            order_id = generate_unique_order_id(length=4)
            
            # Should have called secrets.choice
            self.assertTrue(mock_choice.called)
            self.assertEqual(order_id, 'AAAA')
    
    def test_no_predictable_patterns(self):
        """Test that generated IDs don't follow predictable patterns."""
        ids = []
        for _ in range(100):
            order_id = generate_unique_order_id(length=6)
            ids.append(order_id)
        
        # Should all be different (highly likely with 6 characters)
        unique_ids = set(ids)
        self.assertGreater(len(unique_ids), 95)  # Allow for very small chance of collision
    
    def test_safe_character_exclusions(self):
        """Test that confusing characters are properly excluded."""
        excluded_chars = ['0', 'O', '1', 'I']
        
        # Generate many IDs and check none contain excluded characters
        for _ in range(50):
            order_id = generate_unique_order_id(length=8)
            for char in excluded_chars:
                self.assertNotIn(char, order_id)