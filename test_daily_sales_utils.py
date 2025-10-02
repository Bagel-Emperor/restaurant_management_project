#!/usr/bin/env python3
"""
Comprehensive unit tests for the get_daily_sales_total utility function.
Tests various scenarios including orders on different dates, multiple orders per date,
and edge cases like no orders or different order statuses.
"""

import os
import sys
from datetime import date, timedelta
from decimal import Decimal

import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_management.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from orders.models import Order, Customer, OrderStatus
from orders.choices import OrderStatusChoices
from orders.utils import get_daily_sales_total


class DailySalesTotalTests(TestCase):
    """Test cases for the get_daily_sales_total utility function."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test customer
        self.customer = Customer.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone='1234567890'
        )
        
        # Create order statuses
        self.pending_status, _ = OrderStatus.objects.get_or_create(name=OrderStatusChoices.PENDING)
        self.completed_status, _ = OrderStatus.objects.get_or_create(name=OrderStatusChoices.COMPLETED)
        self.cancelled_status, _ = OrderStatus.objects.get_or_create(name=OrderStatusChoices.CANCELLED)
        
        # Define test dates
        self.today = date.today()
        self.yesterday = self.today - timedelta(days=1)
        self.tomorrow = self.today + timedelta(days=1)
        self.week_ago = self.today - timedelta(days=7)
    
    def test_daily_sales_no_orders(self):
        """Test daily sales calculation when no orders exist for the date."""
        # Test with a date that has no orders
        result = get_daily_sales_total(self.tomorrow)  # Future date, no orders
        
        self.assertEqual(result, Decimal('0.00'))
        self.assertIsInstance(result, Decimal)
    
    def test_daily_sales_single_order(self):
        """Test daily sales calculation with a single order."""
        # Create a single order for today
        order_amount = Decimal('25.99')
        Order.objects.create(
            user=self.user,
            total_amount=order_amount,
            status=self.pending_status,
            created_at=timezone.now().replace(
                hour=10, minute=30, second=0, microsecond=0
            )
        )
        
        result = get_daily_sales_total(self.today)
        
        self.assertEqual(result, order_amount)
        self.assertIsInstance(result, Decimal)
    
    def test_daily_sales_multiple_orders_same_day(self):
        """Test daily sales calculation with multiple orders on the same day."""
        # Create multiple orders for today with different amounts
        amounts = [Decimal('15.50'), Decimal('32.75'), Decimal('8.25'), Decimal('45.00')]
        expected_total = sum(amounts)
        
        for i, amount in enumerate(amounts):
            Order.objects.create(
                user=self.user if i % 2 == 0 else None,  # Alternate between user and guest orders
                customer=self.customer if i % 2 == 1 else None,
                total_amount=amount,
                status=self.pending_status,
                created_at=timezone.now().replace(
                    hour=8 + i, minute=0, second=0, microsecond=0
                )
            )
        
        result = get_daily_sales_total(self.today)
        
        self.assertEqual(result, expected_total)
        self.assertEqual(result, Decimal('101.50'))  # 15.50 + 32.75 + 8.25 + 45.00
    
    def test_daily_sales_different_dates(self):
        """Test that orders from different dates don't interfere with each other."""
        # Create orders on different dates
        today_amounts = [Decimal('20.00'), Decimal('15.00')]
        yesterday_amounts = [Decimal('30.00'), Decimal('25.00')]
        
        # Create today's orders
        for amount in today_amounts:
            Order.objects.create(
                user=self.user,
                total_amount=amount,
                status=self.completed_status,
                created_at=timezone.now().replace(
                    hour=12, minute=0, second=0, microsecond=0
                )
            )
        
        # Create yesterday's orders
        yesterday_datetime = timezone.now() - timedelta(days=1)
        for amount in yesterday_amounts:
            Order.objects.create(
                customer=self.customer,
                total_amount=amount,
                status=self.completed_status,
                created_at=yesterday_datetime.replace(
                    hour=15, minute=0, second=0, microsecond=0
                )
            )
        
        # Test today's sales
        today_result = get_daily_sales_total(self.today)
        self.assertEqual(today_result, sum(today_amounts))
        self.assertEqual(today_result, Decimal('35.00'))
        
        # Test yesterday's sales
        yesterday_result = get_daily_sales_total(self.yesterday)
        self.assertEqual(yesterday_result, sum(yesterday_amounts))
        self.assertEqual(yesterday_result, Decimal('55.00'))
    
    def test_daily_sales_different_order_statuses(self):
        """Test that all order statuses are included in sales calculation."""
        # Create orders with different statuses
        amounts_and_statuses = [
            (Decimal('10.00'), self.pending_status),
            (Decimal('20.00'), self.completed_status),
            (Decimal('15.00'), self.cancelled_status)
        ]
        expected_total = sum(amount for amount, _ in amounts_and_statuses)
        
        for amount, status in amounts_and_statuses:
            Order.objects.create(
                user=self.user,
                total_amount=amount,
                status=status,
                created_at=timezone.now()
            )
        
        result = get_daily_sales_total(self.today)
        
        self.assertEqual(result, expected_total)
        self.assertEqual(result, Decimal('45.00'))
    
    def test_daily_sales_precision(self):
        """Test that decimal precision is maintained in calculations."""
        # Create orders with precise decimal amounts
        precise_amounts = [
            Decimal('12.99'),
            Decimal('8.33'),
            Decimal('5.67'),
            Decimal('0.01')
        ]
        expected_total = sum(precise_amounts)  # Should be 27.00
        
        for amount in precise_amounts:
            Order.objects.create(
                user=self.user,
                total_amount=amount,
                status=self.pending_status,
                created_at=timezone.now()
            )
        
        result = get_daily_sales_total(self.today)
        
        self.assertEqual(result, expected_total)
        self.assertEqual(result, Decimal('27.00'))
        self.assertIsInstance(result, Decimal)
    
    def test_daily_sales_time_boundaries(self):
        """Test that orders at different times of day are correctly included."""
        # Create orders at different times throughout the day
        base_datetime = timezone.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        
        times_and_amounts = [
            (0, 0, Decimal('10.00')),    # Start of day
            (6, 30, Decimal('15.00')),   # Early morning
            (12, 0, Decimal('25.00')),   # Noon
            (18, 45, Decimal('20.00')),  # Evening
            (23, 59, Decimal('5.00'))    # End of day
        ]
        expected_total = sum(amount for _, _, amount in times_and_amounts)
        
        for hour, minute, amount in times_and_amounts:
            Order.objects.create(
                user=self.user,
                total_amount=amount,
                status=self.pending_status,
                created_at=base_datetime.replace(hour=hour, minute=minute)
            )
        
        result = get_daily_sales_total(self.today)
        
        self.assertEqual(result, expected_total)
        self.assertEqual(result, Decimal('75.00'))
    
    def test_daily_sales_guest_vs_user_orders(self):
        """Test that both user and guest orders are included."""
        # Create user order
        user_amount = Decimal('30.00')
        Order.objects.create(
            user=self.user,
            total_amount=user_amount,
            status=self.pending_status,
            created_at=timezone.now()
        )
        
        # Create guest order
        guest_amount = Decimal('25.00')
        Order.objects.create(
            customer=self.customer,
            total_amount=guest_amount,
            status=self.pending_status,
            created_at=timezone.now()
        )
        
        result = get_daily_sales_total(self.today)
        expected_total = user_amount + guest_amount
        
        self.assertEqual(result, expected_total)
        self.assertEqual(result, Decimal('55.00'))
    
    def test_daily_sales_large_amounts(self):
        """Test with larger monetary amounts to ensure no overflow issues."""
        # Create orders with larger amounts
        large_amounts = [
            Decimal('999.99'),
            Decimal('1234.56'),
            Decimal('500.00')
        ]
        expected_total = sum(large_amounts)  # Should be 2734.55
        
        for amount in large_amounts:
            Order.objects.create(
                user=self.user,
                total_amount=amount,
                status=self.completed_status,
                created_at=timezone.now()
            )
        
        result = get_daily_sales_total(self.today)
        
        self.assertEqual(result, expected_total)
        self.assertEqual(result, Decimal('2734.55'))


def run_tests():
    """Run the daily sales total tests."""
    print("🧪 Running Daily Sales Total Utility Tests...")
    print("=" * 60)
    
    # Create a test suite
    import unittest
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(DailySalesTotalTests)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("=" * 60)
    if result.wasSuccessful():
        print("✅ All tests passed!")
        print(f"📊 Ran {result.testsRun} tests successfully")
    else:
        print("❌ Some tests failed!")
        print(f"📊 Ran {result.testsRun} tests, {len(result.failures)} failures, {len(result.errors)} errors")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)