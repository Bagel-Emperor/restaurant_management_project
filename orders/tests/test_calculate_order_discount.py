"""
Tests for the calculate_order_discount utility function.

This module tests the generic discount calculation utility that calculates
discount amounts based on order total and discount percentage.
"""

from decimal import Decimal
from django.test import TestCase
from orders.utils import calculate_order_discount


class TestCalculateOrderDiscount(TestCase):
    """Test suite for calculate_order_discount function."""
    
    def test_basic_discount_calculation(self):
        """Test basic discount calculation with typical values."""
        result = calculate_order_discount(100, 10)
        assert result == Decimal('10.00')
        
    def test_decimal_inputs(self):
        """Test that function works with Decimal inputs."""
        result = calculate_order_discount(Decimal('50.00'), Decimal('20.5'))
        assert result == Decimal('10.25')
        
    def test_float_inputs(self):
        """Test that function works with float inputs."""
        result = calculate_order_discount(75.50, 15)
        # 75.50 * 15% = 11.325, rounds to 11.32 (banker's rounding)
        assert result == Decimal('11.32')
        
    def test_zero_discount(self):
        """Test that 0% discount returns zero."""
        result = calculate_order_discount(100, 0)
        assert result == Decimal('0.00')
        
    def test_full_discount(self):
        """Test that 100% discount returns the full order total."""
        result = calculate_order_discount(100, 100)
        assert result == Decimal('100.00')
        
    def test_zero_order_total(self):
        """Test that zero order total returns zero discount."""
        result = calculate_order_discount(0, 50)
        assert result == Decimal('0.00')
        
    def test_small_percentage(self):
        """Test calculation with small discount percentage."""
        result = calculate_order_discount(100, 2.5)
        assert result == Decimal('2.50')
        
    def test_large_order_total(self):
        """Test calculation with large order total."""
        result = calculate_order_discount(10000, 15)
        assert result == Decimal('1500.00')
        
    def test_fractional_result(self):
        """Test that fractional results are properly quantized."""
        result = calculate_order_discount(33.33, 10)
        assert result == Decimal('3.33')
        
    def test_rounding_precision(self):
        """Test that results are rounded to 2 decimal places."""
        # 33.33 * 33.33% = 11.10889, should round to 11.11
        result = calculate_order_discount(Decimal('33.33'), Decimal('33.33'))
        assert result == Decimal('11.11')
        
    def test_integer_inputs(self):
        """Test that function works with integer inputs."""
        result = calculate_order_discount(50, 20)
        assert result == Decimal('10.00')
        
    def test_mixed_input_types(self):
        """Test that function works with mixed input types."""
        result = calculate_order_discount(Decimal('100'), 15.5)
        assert result == Decimal('15.50')
        
    def test_negative_order_total_raises_error(self):
        """Test that negative order total raises ValueError."""
        with self.assertRaisesMessage(ValueError, "Order total cannot be negative"):
            calculate_order_discount(-100, 10)
            
    def test_negative_discount_percentage_raises_error(self):
        """Test that negative discount percentage raises ValueError."""
        with self.assertRaisesMessage(ValueError, "Discount percentage must be between 0 and 100"):
            calculate_order_discount(100, -10)
            
    def test_discount_percentage_over_100_raises_error(self):
        """Test that discount percentage over 100 raises ValueError."""
        with self.assertRaisesMessage(ValueError, "Discount percentage must be between 0 and 100"):
            calculate_order_discount(100, 150)
            
    def test_invalid_order_total_type_raises_error(self):
        """Test that invalid order total type raises TypeError."""
        with self.assertRaisesMessage(TypeError, "Invalid input types"):
            calculate_order_discount("invalid", 10)
            
    def test_invalid_discount_percentage_type_raises_error(self):
        """Test that invalid discount percentage type raises TypeError."""
        with self.assertRaisesMessage(TypeError, "Invalid input types"):
            calculate_order_discount(100, "invalid")
            
    def test_none_order_total_raises_error(self):
        """Test that None order total raises TypeError."""
        with self.assertRaisesMessage(TypeError, "Invalid input types"):
            calculate_order_discount(None, 10)
            
    def test_none_discount_percentage_raises_error(self):
        """Test that None discount percentage raises TypeError."""
        with self.assertRaisesMessage(TypeError, "Invalid input types"):
            calculate_order_discount(100, None)
            
    def test_string_numeric_inputs(self):
        """Test that string representations of numbers work."""
        result = calculate_order_discount("100", "10")
        assert result == Decimal('10.00')
        
    def test_very_small_discount(self):
        """Test calculation with very small discount percentage."""
        result = calculate_order_discount(100, 0.01)
        assert result == Decimal('0.01')
        
    def test_very_small_order_total(self):
        """Test calculation with very small order total."""
        result = calculate_order_discount(0.50, 10)
        assert result == Decimal('0.05')
        
    def test_edge_case_99_99_percent(self):
        """Test calculation with 99.99% discount."""
        result = calculate_order_discount(100, 99.99)
        assert result == Decimal('99.99')
        
    def test_precision_with_many_decimals(self):
        """Test that function handles inputs with many decimal places."""
        result = calculate_order_discount(Decimal('123.456789'), Decimal('12.3456'))
        # 123.456789 * 0.123456 = 15.2408594...
        assert result == Decimal('15.24')
        
    def test_discount_never_exceeds_order_total(self):
        """Test safety check that discount cannot exceed order total."""
        # Even though this shouldn't happen with 0-100% validation,
        # the function has a safety check
        result = calculate_order_discount(50, 100)
        assert result == Decimal('50.00')
        assert result <= Decimal('50.00')
