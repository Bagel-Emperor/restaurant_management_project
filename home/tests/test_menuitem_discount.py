"""
Tests for MenuItem discount_percentage field and calculate_final_price() method.
"""
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from home.models import MenuItem, Restaurant
from django.contrib.auth.models import User


class MenuItemDiscountTestCase(TestCase):
    """Test cases for MenuItem discount functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create a restaurant
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner_name='Test Owner',
            email='test@restaurant.com',
            phone_number='555-0123'
        )
        
        # Create a menu item
        self.menu_item = MenuItem.objects.create(
            name='Test Burger',
            description='A delicious test burger',
            price=Decimal('10.00'),
            restaurant=self.restaurant
        )
    
    def test_default_discount_is_zero(self):
        """Test that new menu items have 0% discount by default."""
        self.assertEqual(self.menu_item.discount_percentage, Decimal('0.00'))
    
    def test_calculate_final_price_no_discount(self):
        """Test calculate_final_price() with 0% discount returns original price."""
        self.menu_item.discount_percentage = Decimal('0.00')
        self.menu_item.save()
        
        final_price = self.menu_item.calculate_final_price()
        self.assertEqual(final_price, Decimal('10.00'))
    
    def test_calculate_final_price_with_20_percent_discount(self):
        """Test calculate_final_price() with 20% discount."""
        self.menu_item.discount_percentage = Decimal('20.00')
        self.menu_item.save()
        
        final_price = self.menu_item.calculate_final_price()
        # 10.00 - (10.00 * 0.20) = 8.00
        self.assertEqual(final_price, Decimal('8.00'))
    
    def test_calculate_final_price_with_50_percent_discount(self):
        """Test calculate_final_price() with 50% discount."""
        self.menu_item.discount_percentage = Decimal('50.00')
        self.menu_item.save()
        
        final_price = self.menu_item.calculate_final_price()
        # 10.00 - (10.00 * 0.50) = 5.00
        self.assertEqual(final_price, Decimal('5.00'))
    
    def test_calculate_final_price_with_100_percent_discount(self):
        """Test calculate_final_price() with 100% discount (free)."""
        self.menu_item.discount_percentage = Decimal('100.00')
        self.menu_item.save()
        
        final_price = self.menu_item.calculate_final_price()
        # 10.00 - (10.00 * 1.00) = 0.00
        self.assertEqual(final_price, Decimal('0.00'))
    
    def test_calculate_final_price_with_decimal_discount(self):
        """Test calculate_final_price() with decimal discount percentage."""
        self.menu_item.price = Decimal('15.50')
        self.menu_item.discount_percentage = Decimal('15.00')
        self.menu_item.save()
        
        final_price = self.menu_item.calculate_final_price()
        # 15.50 - (15.50 * 0.15) = 15.50 - 2.325 = 13.175 -> 13.18 (rounded)
        self.assertEqual(final_price, Decimal('13.18'))
    
    def test_calculate_final_price_with_odd_discount(self):
        """Test calculate_final_price() with odd discount percentage."""
        self.menu_item.price = Decimal('9.99')
        self.menu_item.discount_percentage = Decimal('33.33')
        self.menu_item.save()
        
        final_price = self.menu_item.calculate_final_price()
        # 9.99 - (9.99 * 0.3333) = 9.99 - 3.329667 = 6.660333 -> 6.66 (rounded)
        self.assertEqual(final_price, Decimal('6.66'))
    
    def test_discount_percentage_accepts_valid_values(self):
        """Test that discount_percentage accepts valid values (0-100)."""
        valid_discounts = [Decimal('0.00'), Decimal('25.50'), Decimal('50.00'), Decimal('99.99'), Decimal('100.00')]
        
        for discount in valid_discounts:
            self.menu_item.discount_percentage = discount
            self.menu_item.save()
            self.assertEqual(self.menu_item.discount_percentage, discount)
    
    def test_discount_percentage_rejects_negative_values(self):
        """Test that discount_percentage rejects negative values."""
        self.menu_item.discount_percentage = Decimal('-10.00')
        
        with self.assertRaises(ValidationError):
            self.menu_item.full_clean()
    
    def test_discount_percentage_rejects_values_over_100(self):
        """Test that discount_percentage rejects values over 100."""
        self.menu_item.discount_percentage = Decimal('150.00')
        
        with self.assertRaises(ValidationError):
            self.menu_item.full_clean()
    
    def test_calculate_final_price_returns_decimal(self):
        """Test that calculate_final_price() returns a Decimal type."""
        self.menu_item.discount_percentage = Decimal('25.00')
        self.menu_item.save()
        
        final_price = self.menu_item.calculate_final_price()
        self.assertIsInstance(final_price, Decimal)
    
    def test_calculate_final_price_precision(self):
        """Test that calculate_final_price() returns price with 2 decimal places."""
        self.menu_item.price = Decimal('12.99')
        self.menu_item.discount_percentage = Decimal('17.50')
        self.menu_item.save()
        
        final_price = self.menu_item.calculate_final_price()
        # 12.99 - (12.99 * 0.175) = 12.99 - 2.27325 = 10.71675 -> 10.72 (rounded)
        self.assertEqual(final_price, Decimal('10.72'))
        
        # Check it has exactly 2 decimal places
        self.assertEqual(final_price.as_tuple().exponent, -2)
