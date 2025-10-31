"""
Django TestCase for calculate_tip_amount utility function.

This test suite validates the tip calculation functionality including:
1. Standard tip percentage calculations
2. Edge cases (0%, 100%, fractional percentages)
3. Different input types (Decimal, float, int)
4. Rounding and precision
5. Large and small amounts

Run with: python manage.py test orders.tests.test_calculate_tip
"""

from django.test import TestCase
from decimal import Decimal, InvalidOperation

from orders.utils import calculate_tip_amount


class CalculateTipAmountTests(TestCase):
    """Test cases for the calculate_tip_amount utility function."""
    
    def test_standard_15_percent_tip(self):
        """Test 15% tip calculation on standard amount."""
        result = calculate_tip_amount(Decimal('50.00'), 15)
        self.assertEqual(result, Decimal('7.50'))
    
    def test_standard_20_percent_tip(self):
        """Test 20% tip calculation on standard amount."""
        result = calculate_tip_amount(Decimal('100.00'), 20)
        self.assertEqual(result, Decimal('20.00'))
    
    def test_18_percent_tip(self):
        """Test 18% tip (common service charge)."""
        result = calculate_tip_amount(Decimal('75.50'), 18)
        self.assertEqual(result, Decimal('13.59'))
    
    def test_fractional_percentage(self):
        """Test fractional tip percentage (12.5%)."""
        result = calculate_tip_amount(80, 12.5)
        self.assertEqual(result, Decimal('10.00'))
    
    def test_zero_tip(self):
        """Test 0% tip returns zero."""
        result = calculate_tip_amount(Decimal('25.00'), 0)
        self.assertEqual(result, Decimal('0.00'))
    
    def test_100_percent_tip(self):
        """Test 100% tip (doubling the amount)."""
        result = calculate_tip_amount(Decimal('50.00'), 100)
        self.assertEqual(result, Decimal('50.00'))
    
    def test_large_order_amount(self):
        """Test tip calculation on large order."""
        result = calculate_tip_amount(Decimal('347.89'), 18)
        self.assertEqual(result, Decimal('62.62'))
    
    def test_small_order_amount(self):
        """Test tip calculation on small order."""
        result = calculate_tip_amount(Decimal('5.50'), 20)
        self.assertEqual(result, Decimal('1.10'))
    
    def test_very_small_amount(self):
        """Test tip on very small amount."""
        result = calculate_tip_amount(Decimal('1.00'), 15)
        self.assertEqual(result, Decimal('0.15'))
    
    def test_float_input_order_total(self):
        """Test function accepts float input for order total."""
        result = calculate_tip_amount(100.00, 15)
        self.assertEqual(result, Decimal('15.00'))
    
    def test_int_input_order_total(self):
        """Test function accepts integer input for order total."""
        result = calculate_tip_amount(100, 20)
        self.assertEqual(result, Decimal('20.00'))
    
    def test_int_input_percentage(self):
        """Test function accepts integer input for percentage."""
        result = calculate_tip_amount(Decimal('50.00'), 15)
        self.assertEqual(result, Decimal('7.50'))
    
    def test_rounding_to_two_decimals(self):
        """Test that result is rounded to exactly 2 decimal places."""
        # 15% of 33.33 = 4.9995, should round to 5.00
        result = calculate_tip_amount(Decimal('33.33'), 15)
        self.assertEqual(result, Decimal('5.00'))
    
    def test_rounding_down(self):
        """Test rounding down when third decimal is < 5."""
        # 10% of 10.01 = 1.001, should round down to 1.00
        result = calculate_tip_amount(Decimal('10.01'), 10)
        self.assertEqual(result, Decimal('1.00'))
    
    def test_rounding_up(self):
        """Test rounding up when third decimal is >= 5."""
        # 10% of 10.06 = 1.006, should round up to 1.01
        result = calculate_tip_amount(Decimal('10.06'), 10)
        self.assertEqual(result, Decimal('1.01'))
    
    def test_result_type_is_decimal(self):
        """Test that result is always Decimal type."""
        result = calculate_tip_amount(50, 15)
        self.assertIsInstance(result, Decimal)
    
    def test_result_has_two_decimal_places(self):
        """Test that result always has exactly 2 decimal places."""
        result = calculate_tip_amount(Decimal('100.00'), 15)
        # Convert to string to check decimal places
        result_str = str(result)
        decimal_places = len(result_str.split('.')[-1]) if '.' in result_str else 0
        self.assertEqual(decimal_places, 2)
    
    def test_25_percent_generous_tip(self):
        """Test 25% tip (generous tipper)."""
        result = calculate_tip_amount(Decimal('80.00'), 25)
        self.assertEqual(result, Decimal('20.00'))
    
    def test_10_percent_minimal_tip(self):
        """Test 10% tip (minimal service)."""
        result = calculate_tip_amount(Decimal('45.00'), 10)
        self.assertEqual(result, Decimal('4.50'))
    
    def test_odd_order_amount(self):
        """Test tip on odd order amount."""
        result = calculate_tip_amount(Decimal('37.49'), 18)
        self.assertEqual(result, Decimal('6.75'))
    
    def test_restaurant_bill_with_tax_included(self):
        """Test realistic restaurant bill scenario."""
        # $52.47 total after tax, 18% tip
        result = calculate_tip_amount(Decimal('52.47'), 18)
        self.assertEqual(result, Decimal('9.44'))
    
    def test_multiple_calculations_independent(self):
        """Test that multiple calculations don't interfere with each other."""
        result1 = calculate_tip_amount(Decimal('50.00'), 15)
        result2 = calculate_tip_amount(Decimal('100.00'), 20)
        result3 = calculate_tip_amount(Decimal('75.00'), 18)
        
        self.assertEqual(result1, Decimal('7.50'))
        self.assertEqual(result2, Decimal('20.00'))
        self.assertEqual(result3, Decimal('13.50'))


class CalculateTipAmountEdgeCaseTests(TestCase):
    """Test edge cases and boundary conditions."""
    
    def test_zero_order_total(self):
        """Test tip calculation when order total is zero."""
        result = calculate_tip_amount(Decimal('0.00'), 15)
        self.assertEqual(result, Decimal('0.00'))
    
    def test_very_high_percentage(self):
        """Test calculation with unusually high percentage."""
        result = calculate_tip_amount(Decimal('50.00'), 200)
        self.assertEqual(result, Decimal('100.00'))
    
    def test_fractional_cents_order(self):
        """Test order with fractional cents."""
        result = calculate_tip_amount(Decimal('12.345'), 20)
        self.assertEqual(result, Decimal('2.47'))
    
    def test_negative_order_total(self):
        """Test function handles negative order total (refund scenario)."""
        result = calculate_tip_amount(Decimal('-50.00'), 15)
        self.assertEqual(result, Decimal('-7.50'))
    
    def test_negative_tip_percentage(self):
        """Test function handles negative tip percentage (unusual but possible)."""
        result = calculate_tip_amount(Decimal('100.00'), -10)
        self.assertEqual(result, Decimal('-10.00'))
    
    def test_0_01_cent_order(self):
        """Test minimum possible order amount."""
        result = calculate_tip_amount(Decimal('0.01'), 20)
        self.assertEqual(result, Decimal('0.00'))
    
    def test_999_99_tip_percentage(self):
        """Test calculation with extremely high tip percentage."""
        result = calculate_tip_amount(Decimal('10.00'), 999.99)
        self.assertEqual(result, Decimal('100.00'))


class CalculateTipAmountInputValidationTests(TestCase):
    """Test input validation and error handling."""
    
    def test_string_decimal_input(self):
        """Test function accepts string representations of decimals."""
        result = calculate_tip_amount('50.00', '15')
        self.assertEqual(result, Decimal('7.50'))
    
    def test_invalid_order_total_type(self):
        """Test that invalid order_total type raises InvalidOperation."""
        with self.assertRaises(InvalidOperation):
            calculate_tip_amount('invalid', 15)
    
    def test_invalid_percentage_type(self):
        """Test that invalid tip_percentage type raises InvalidOperation."""
        with self.assertRaises(InvalidOperation):
            calculate_tip_amount(50, 'invalid')
    
    def test_none_order_total(self):
        """Test that None order_total raises InvalidOperation."""
        with self.assertRaises(InvalidOperation):
            calculate_tip_amount(None, 15)
    
    def test_none_tip_percentage(self):
        """Test that None tip_percentage raises InvalidOperation."""
        with self.assertRaises(InvalidOperation):
            calculate_tip_amount(50, None)


if __name__ == '__main__':
    print("=" * 80)
    print("CALCULATE TIP AMOUNT UTILITY TEST SUITE")
    print("=" * 80)
    print("\nRun with: python manage.py test orders.tests.test_calculate_tip")
    print("\nThis test suite covers:")
    print("  ✓ Standard tip percentages (10%, 15%, 18%, 20%, 25%)")
    print("  ✓ Fractional percentages (12.5%)")
    print("  ✓ Edge cases (0%, 100%, high percentages)")
    print("  ✓ Different input types (Decimal, float, int, string)")
    print("  ✓ Rounding and precision (exactly 2 decimal places)")
    print("  ✓ Large and small order amounts")
    print("  ✓ Negative values (refunds)")
    print("  ✓ Input validation and error handling")
    print("=" * 80)
