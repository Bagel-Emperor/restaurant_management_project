"""
Test suite for calculate_order_price utility function.
Tests calculation logic, validation, and edge cases.
"""
from django.test import TestCase
from decimal import Decimal
from orders.utils import calculate_order_price


class CalculateOrderPriceTestCase(TestCase):
    """Test cases for calculate_order_price utility function."""
    
    def test_calculate_price_with_dict_items(self):
        """Test calculating price with dictionary items."""
        items = [
            {'quantity': 2, 'price': Decimal('12.99')},
            {'quantity': 1, 'price': Decimal('8.50')},
            {'quantity': 3, 'price': Decimal('5.25')}
        ]
        
        expected = Decimal('2') * Decimal('12.99') + Decimal('1') * Decimal('8.50') + Decimal('3') * Decimal('5.25')
        result = calculate_order_price(items)
        
        self.assertEqual(result, expected)
        self.assertEqual(result, Decimal('50.23'))
    
    def test_calculate_price_empty_list(self):
        """Test that empty list returns zero."""
        result = calculate_order_price([])
        self.assertEqual(result, Decimal('0.00'))
    
    def test_calculate_price_single_item(self):
        """Test calculating price with single item."""
        items = [{'quantity': 5, 'price': Decimal('10.00')}]
        result = calculate_order_price(items)
        
        self.assertEqual(result, Decimal('50.00'))
    
    def test_calculate_price_zero_quantity(self):
        """Test item with zero quantity."""
        items = [
            {'quantity': 0, 'price': Decimal('12.99')},
            {'quantity': 2, 'price': Decimal('8.50')}
        ]
        
        result = calculate_order_price(items)
        self.assertEqual(result, Decimal('17.00'))
    
    def test_calculate_price_zero_price(self):
        """Test item with zero price (free item)."""
        items = [
            {'quantity': 1, 'price': Decimal('0.00')},
            {'quantity': 2, 'price': Decimal('10.00')}
        ]
        
        result = calculate_order_price(items)
        self.assertEqual(result, Decimal('20.00'))
    
    def test_calculate_price_with_decimals(self):
        """Test precise decimal calculation."""
        items = [
            {'quantity': 3, 'price': Decimal('12.99')},
            {'quantity': 2, 'price': Decimal('7.50')}
        ]
        
        # 3 * 12.99 = 38.97
        # 2 * 7.50 = 15.00
        # Total = 53.97
        result = calculate_order_price(items)
        self.assertEqual(result, Decimal('53.97'))
    
    def test_calculate_price_with_float_conversion(self):
        """Test that floats are properly converted to Decimal."""
        items = [
            {'quantity': 2, 'price': 12.99},  # float
            {'quantity': 1, 'price': 8.50}    # float
        ]
        
        result = calculate_order_price(items)
        self.assertEqual(result, Decimal('34.48'))
    
    def test_calculate_price_with_string_numbers(self):
        """Test that string numbers are properly converted."""
        items = [
            {'quantity': '2', 'price': '12.99'},
            {'quantity': '1', 'price': '8.50'}
        ]
        
        result = calculate_order_price(items)
        self.assertEqual(result, Decimal('34.48'))
    
    def test_calculate_price_with_integer_price(self):
        """Test that integer prices work correctly."""
        items = [
            {'quantity': 3, 'price': 10},  # int
            {'quantity': 2, 'price': 5}    # int
        ]
        
        result = calculate_order_price(items)
        self.assertEqual(result, Decimal('40.00'))
    
    def test_calculate_price_negative_quantity_raises_error(self):
        """Test that negative quantity raises ValueError."""
        items = [{'quantity': -1, 'price': Decimal('10.00')}]
        
        with self.assertRaises(ValueError) as context:
            calculate_order_price(items)
        
        self.assertIn('negative quantity', str(context.exception).lower())
    
    def test_calculate_price_negative_price_raises_error(self):
        """Test that negative price raises ValueError."""
        items = [{'quantity': 2, 'price': Decimal('-10.00')}]
        
        with self.assertRaises(ValueError) as context:
            calculate_order_price(items)
        
        self.assertIn('negative price', str(context.exception).lower())
    
    def test_calculate_price_missing_quantity_raises_error(self):
        """Test that missing quantity field raises TypeError."""
        items = [{'price': Decimal('10.00')}]  # missing quantity
        
        with self.assertRaises(TypeError) as context:
            calculate_order_price(items)
        
        self.assertIn('quantity', str(context.exception).lower())
    
    def test_calculate_price_missing_price_raises_error(self):
        """Test that missing price field raises TypeError."""
        items = [{'quantity': 2}]  # missing price
        
        with self.assertRaises(TypeError) as context:
            calculate_order_price(items)
        
        self.assertIn('price', str(context.exception).lower())
    
    def test_calculate_price_invalid_quantity_type_raises_error(self):
        """Test that invalid quantity type raises TypeError."""
        items = [{'quantity': 'invalid', 'price': Decimal('10.00')}]
        
        with self.assertRaises(TypeError):
            calculate_order_price(items)
    
    def test_calculate_price_invalid_price_type_raises_error(self):
        """Test that invalid price type raises TypeError."""
        items = [{'quantity': 2, 'price': 'invalid'}]
        
        with self.assertRaises(TypeError):
            calculate_order_price(items)
    
    def test_calculate_price_with_object_attributes(self):
        """Test calculating price with objects (not dicts)."""
        # Create mock objects with attributes
        class MockItem:
            def __init__(self, quantity, price):
                self.quantity = quantity
                self.price = price
        
        items = [
            MockItem(2, Decimal('12.99')),
            MockItem(1, Decimal('8.50'))
        ]
        
        result = calculate_order_price(items)
        self.assertEqual(result, Decimal('34.48'))
    
    def test_calculate_price_large_numbers(self):
        """Test calculation with large quantities and prices."""
        items = [
            {'quantity': 1000, 'price': Decimal('999.99')},
            {'quantity': 500, 'price': Decimal('1234.56')}
        ]
        
        # 1000 * 999.99 = 999,990.00
        # 500 * 1234.56 = 617,280.00
        # Total = 1,617,270.00
        result = calculate_order_price(items)
        self.assertEqual(result, Decimal('1617270.00'))
    
    def test_calculate_price_many_items(self):
        """Test calculation with many items."""
        items = [
            {'quantity': 1, 'price': Decimal('1.00')}
            for _ in range(100)
        ]
        
        result = calculate_order_price(items)
        self.assertEqual(result, Decimal('100.00'))
    
    def test_calculate_price_precision_maintained(self):
        """Test that decimal precision is maintained (no rounding errors)."""
        items = [
            {'quantity': 3, 'price': Decimal('0.10')},
            {'quantity': 2, 'price': Decimal('0.20')}
        ]
        
        # 3 * 0.10 = 0.30
        # 2 * 0.20 = 0.40
        # Total = 0.70 (exact, no floating point error)
        result = calculate_order_price(items)
        self.assertEqual(result, Decimal('0.70'))
    
    def test_calculate_price_result_quantized_to_cents(self):
        """Test that result is quantized to 2 decimal places."""
        items = [
            {'quantity': 1, 'price': Decimal('10.999')}  # 3 decimal places
        ]
        
        result = calculate_order_price(items)
        # Should be rounded to 2 decimal places
        self.assertEqual(result, Decimal('11.00'))
    
    def test_calculate_price_mixed_zero_and_nonzero(self):
        """Test mix of zero and non-zero quantities/prices."""
        items = [
            {'quantity': 0, 'price': Decimal('10.00')},
            {'quantity': 2, 'price': Decimal('0.00')},
            {'quantity': 3, 'price': Decimal('5.00')}
        ]
        
        result = calculate_order_price(items)
        self.assertEqual(result, Decimal('15.00'))
    
    def test_calculate_price_real_world_scenario(self):
        """Test realistic restaurant order scenario."""
        items = [
            {'quantity': 2, 'price': Decimal('12.99')},  # 2 Burgers
            {'quantity': 1, 'price': Decimal('8.50')},   # 1 Salad
            {'quantity': 3, 'price': Decimal('2.50')},   # 3 Drinks
            {'quantity': 1, 'price': Decimal('6.99')}    # 1 Dessert
        ]
        
        # 2 * 12.99 = 25.98
        # 1 * 8.50 = 8.50
        # 3 * 2.50 = 7.50
        # 1 * 6.99 = 6.99
        # Total = 48.97
        result = calculate_order_price(items)
        self.assertEqual(result, Decimal('48.97'))
