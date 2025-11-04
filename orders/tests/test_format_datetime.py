"""Tests for format_datetime utility function."""
from datetime import datetime
from django.test import TestCase
from orders.utils import format_datetime


class FormatDatetimeTests(TestCase):
    """Test cases for format_datetime function."""
    
    def test_format_datetime_valid(self):
        """Test formatting a valid datetime object."""
        dt = datetime(2023, 1, 1, 10, 30)
        result = format_datetime(dt)
        self.assertEqual(result, 'January 01, 2023 at 10:30 AM')
    
    def test_format_datetime_none_default_empty(self):
        """Test None returns empty string by default."""
        result = format_datetime(None)
        self.assertEqual(result, '')
    
    def test_format_datetime_none_custom_default(self):
        """Test None returns custom default."""
        result = format_datetime(None, default='N/A')
        self.assertEqual(result, 'N/A')
    
    def test_format_datetime_pm(self):
        """Test PM time formatting."""
        dt = datetime(2023, 12, 31, 23, 59)
        result = format_datetime(dt)
        self.assertEqual(result, 'December 31, 2023 at 11:59 PM')
