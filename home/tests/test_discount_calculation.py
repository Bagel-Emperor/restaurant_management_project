"""
Tests for the calculate_discount utility function.
"""
from decimal import Decimal
from django.test import TestCase
from home.utils import calculate_discount


class CalculateDiscountTestCase(TestCase):
    """Test cases for calculate_discount utility function."""
    
    def test_calculate_discount_20_percent(self):
        """Test calculating 20% discount on $100."""
        result = calculate_discount(100, 20)
        self.assertEqual(result, Decimal('80.00'))
    
    def test_calculate_discount_50_percent(self):
        """Test calculating 50% discount (half price)."""
        result = calculate_discount(50, 50)
        self.assertEqual(result, Decimal('25.00'))
    
    def test_calculate_discount_zero_percent(self):
        """Test that 0% discount returns original price."""
        result = calculate_discount(100, 0)
        self.assertEqual(result, Decimal('100.00'))
    
    def test_calculate_discount_100_percent(self):
        """Test that 100% discount returns $0 (free)."""
        result = calculate_discount(100, 100)
        self.assertEqual(result, Decimal('0.00'))
    
    def test_calculate_discount_decimal_price(self):
        """Test discount on decimal price."""
        result = calculate_discount(10.50, 20)
        self.assertEqual(result, Decimal('8.40'))
    
    def test_calculate_discount_decimal_percentage(self):
        """Test discount with decimal percentage."""
        result = calculate_discount(99.99, 15.5)
        # 99.99 - (99.99 * 0.155) = 99.99 - 15.498 = 84.492 -> 84.49
        self.assertEqual(result, Decimal('84.49'))
    
    def test_calculate_discount_complex_calculation(self):
        """Test discount with complex numbers."""
        result = calculate_discount(123.45, 33.33)
        # 123.45 - (123.45 * 0.3333) = 123.45 - 41.145585 = 82.304415 -> 82.30
        self.assertEqual(result, Decimal('82.30'))
    
    def test_calculate_discount_small_price(self):
        """Test discount on small price."""
        result = calculate_discount(0.99, 10)
        # 0.99 - (0.99 * 0.10) = 0.99 - 0.099 = 0.891 -> 0.89
        self.assertEqual(result, Decimal('0.89'))
    
    def test_calculate_discount_zero_price(self):
        """Test discount on zero price (edge case)."""
        result = calculate_discount(0, 50)
        self.assertEqual(result, Decimal('0.00'))
    
    def test_calculate_discount_returns_decimal(self):
        """Test that function returns Decimal type."""
        result = calculate_discount(100, 20)
        self.assertIsInstance(result, Decimal)
    
    def test_calculate_discount_precision(self):
        """Test that result has exactly 2 decimal places."""
        result = calculate_discount(100, 33.333)
        # Check it has exactly 2 decimal places
        self.assertEqual(result.as_tuple().exponent, -2)
    
    def test_calculate_discount_accepts_int(self):
        """Test that function accepts integer inputs."""
        result = calculate_discount(100, 20)
        self.assertEqual(result, Decimal('80.00'))
    
    def test_calculate_discount_accepts_float(self):
        """Test that function accepts float inputs."""
        result = calculate_discount(100.0, 20.0)
        self.assertEqual(result, Decimal('80.00'))
    
    def test_calculate_discount_accepts_decimal(self):
        """Test that function accepts Decimal inputs."""
        result = calculate_discount(Decimal('100'), Decimal('20'))
        self.assertEqual(result, Decimal('80.00'))
    
    def test_calculate_discount_accepts_string_numbers(self):
        """Test that function accepts string numbers."""
        result = calculate_discount('100', '20')
        self.assertEqual(result, Decimal('80.00'))
    
    # Error handling tests
    
    def test_calculate_discount_negative_price_raises_error(self):
        """Test that negative price raises ValueError."""
        with self.assertRaises(ValueError) as context:
            calculate_discount(-10, 20)
        self.assertIn('non-negative', str(context.exception))
    
    def test_calculate_discount_negative_percentage_raises_error(self):
        """Test that negative discount percentage raises ValueError."""
        with self.assertRaises(ValueError) as context:
            calculate_discount(100, -5)
        self.assertIn('between 0 and 100', str(context.exception))
    
    def test_calculate_discount_percentage_over_100_raises_error(self):
        """Test that discount percentage over 100 raises ValueError."""
        with self.assertRaises(ValueError) as context:
            calculate_discount(100, 150)
        self.assertIn('between 0 and 100', str(context.exception))
    
    def test_calculate_discount_invalid_price_type_raises_error(self):
        """Test that invalid price type raises TypeError."""
        with self.assertRaises(TypeError) as context:
            calculate_discount('abc', 20)
        self.assertIn('Invalid input types', str(context.exception))
    
    def test_calculate_discount_invalid_percentage_type_raises_error(self):
        """Test that invalid percentage type raises TypeError."""
        with self.assertRaises(TypeError) as context:
            calculate_discount(100, 'xyz')
        self.assertIn('Invalid input types', str(context.exception))
    
    def test_calculate_discount_none_price_raises_error(self):
        """Test that None price raises TypeError."""
        with self.assertRaises(TypeError) as context:
            calculate_discount(None, 20)
        self.assertIn('Invalid input types', str(context.exception))
    
    def test_calculate_discount_none_percentage_raises_error(self):
        """Test that None percentage raises TypeError."""
        with self.assertRaises(TypeError) as context:
            calculate_discount(100, None)
        self.assertIn('Invalid input types', str(context.exception))
    
    # Real-world scenario tests
    
    def test_calculate_discount_restaurant_burger(self):
        """Test real-world scenario: $12.99 burger with 15% discount."""
        result = calculate_discount(12.99, 15)
        # 12.99 - (12.99 * 0.15) = 12.99 - 1.9485 = 11.0415 -> 11.04
        self.assertEqual(result, Decimal('11.04'))
    
    def test_calculate_discount_restaurant_pizza(self):
        """Test real-world scenario: $18.50 pizza with 20% off."""
        result = calculate_discount(18.50, 20)
        # 18.50 - (18.50 * 0.20) = 18.50 - 3.70 = 14.80
        self.assertEqual(result, Decimal('14.80'))
    
    def test_calculate_discount_happy_hour_special(self):
        """Test real-world scenario: $8.99 appetizer with 25% happy hour discount."""
        result = calculate_discount(8.99, 25)
        # 8.99 - (8.99 * 0.25) = 8.99 - 2.2475 = 6.7425 -> 6.74
        self.assertEqual(result, Decimal('6.74'))
    
    def test_calculate_discount_early_bird_special(self):
        """Test real-world scenario: $22.95 dinner with 30% early bird discount."""
        result = calculate_discount(22.95, 30)
        # 22.95 - (22.95 * 0.30) = 22.95 - 6.885 = 16.065 -> 16.06 (banker's rounding)
        self.assertEqual(result, Decimal('16.06'))
