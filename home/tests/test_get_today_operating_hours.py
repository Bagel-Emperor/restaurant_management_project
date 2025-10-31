"""
Test cases for the get_today_operating_hours utility function.

This test module provides comprehensive coverage for retrieving today's
restaurant operating hours, including various scenarios with different
days, closed days, and edge cases.
"""

from django.test import TestCase
from datetime import time, datetime
from unittest.mock import patch, Mock
from home.models import DailyOperatingHours
from home.utils import get_today_operating_hours


class GetTodayOperatingHoursTests(TestCase):
    """Test cases for basic get_today_operating_hours functionality."""
    
    def setUp(self):
        """Set up test data for operating hours."""
        # Create operating hours for all weekdays (Monday-Friday)
        DailyOperatingHours.objects.create(
            day_of_week=0,  # Monday
            open_time=time(9, 0),
            close_time=time(17, 0),
            is_closed=False
        )
        DailyOperatingHours.objects.create(
            day_of_week=1,  # Tuesday
            open_time=time(9, 0),
            close_time=time(17, 0),
            is_closed=False
        )
        DailyOperatingHours.objects.create(
            day_of_week=2,  # Wednesday
            open_time=time(9, 0),
            close_time=time(17, 0),
            is_closed=False
        )
        DailyOperatingHours.objects.create(
            day_of_week=3,  # Thursday
            open_time=time(9, 0),
            close_time=time(17, 0),
            is_closed=False
        )
        DailyOperatingHours.objects.create(
            day_of_week=4,  # Friday
            open_time=time(8, 0),
            close_time=time(20, 0),
            is_closed=False
        )
        # Saturday with different hours
        DailyOperatingHours.objects.create(
            day_of_week=5,  # Saturday
            open_time=time(10, 0),
            close_time=time(18, 0),
            is_closed=False
        )
        # Sunday marked as closed
        DailyOperatingHours.objects.create(
            day_of_week=6,  # Sunday
            open_time=time(0, 0),
            close_time=time(0, 0),
            is_closed=True
        )
    
    @patch('home.utils.datetime')
    def test_monday_returns_correct_hours(self, mock_datetime):
        """Test that Monday returns 9am-5pm."""
        # Mock datetime.now().weekday() to return 0 (Monday)
        mock_now = Mock()
        mock_now.weekday.return_value = 0
        mock_datetime.now.return_value = mock_now
        
        open_time, close_time = get_today_operating_hours()
        
        self.assertEqual(open_time, time(9, 0))
        self.assertEqual(close_time, time(17, 0))
    
    @patch('home.utils.datetime')
    def test_tuesday_returns_correct_hours(self, mock_datetime):
        """Test that Tuesday returns 9am-5pm."""
        mock_now = Mock()
        mock_now.weekday.return_value = 1
        mock_datetime.now.return_value = mock_now
        
        open_time, close_time = get_today_operating_hours()
        
        self.assertEqual(open_time, time(9, 0))
        self.assertEqual(close_time, time(17, 0))
    
    @patch('home.utils.datetime')
    def test_friday_returns_different_hours(self, mock_datetime):
        """Test that Friday returns different hours (8am-8pm)."""
        mock_now = Mock()
        mock_now.weekday.return_value = 4
        mock_datetime.now.return_value = mock_now
        
        open_time, close_time = get_today_operating_hours()
        
        self.assertEqual(open_time, time(8, 0))
        self.assertEqual(close_time, time(20, 0))
    
    @patch('home.utils.datetime')
    def test_saturday_returns_weekend_hours(self, mock_datetime):
        """Test that Saturday returns weekend hours (10am-6pm)."""
        mock_now = Mock()
        mock_now.weekday.return_value = 5
        mock_datetime.now.return_value = mock_now
        
        open_time, close_time = get_today_operating_hours()
        
        self.assertEqual(open_time, time(10, 0))
        self.assertEqual(close_time, time(18, 0))
    
    @patch('home.utils.datetime')
    def test_sunday_closed_returns_none(self, mock_datetime):
        """Test that Sunday (closed day) returns (None, None)."""
        mock_now = Mock()
        mock_now.weekday.return_value = 6
        mock_datetime.now.return_value = mock_now
        
        open_time, close_time = get_today_operating_hours()
        
        self.assertIsNone(open_time)
        self.assertIsNone(close_time)
    
    @patch('home.utils.datetime')
    def test_returns_tuple(self, mock_datetime):
        """Test that function returns a tuple."""
        mock_now = Mock()
        mock_now.weekday.return_value = 0
        mock_datetime.now.return_value = mock_now
        
        result = get_today_operating_hours()
        
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
    
    @patch('home.utils.datetime')
    def test_returns_time_objects(self, mock_datetime):
        """Test that returned values are time objects when open."""
        mock_now = Mock()
        mock_now.weekday.return_value = 0
        mock_datetime.now.return_value = mock_now
        
        open_time, close_time = get_today_operating_hours()
        
        self.assertIsInstance(open_time, time)
        self.assertIsInstance(close_time, time)


class GetTodayOperatingHoursEdgeCaseTests(TestCase):
    """Test cases for edge cases and error scenarios."""
    
    @patch('home.utils.datetime')
    def test_no_hours_defined_returns_none(self, mock_datetime):
        """Test that when no hours are defined, returns (None, None)."""
        mock_now = Mock()
        mock_now.weekday.return_value = 0
        mock_datetime.now.return_value = mock_now
        
        # No DailyOperatingHours created
        open_time, close_time = get_today_operating_hours()
        
        self.assertIsNone(open_time)
        self.assertIsNone(close_time)
    
    @patch('home.utils.datetime')
    def test_missing_day_returns_none(self, mock_datetime):
        """Test that a missing day entry returns (None, None)."""
        # Only create hours for Monday
        DailyOperatingHours.objects.create(
            day_of_week=0,
            open_time=time(9, 0),
            close_time=time(17, 0),
            is_closed=False
        )
        
        # Query for Tuesday (no entry)
        mock_now = Mock()
        mock_now.weekday.return_value = 1
        mock_datetime.now.return_value = mock_now
        
        open_time, close_time = get_today_operating_hours()
        
        self.assertIsNone(open_time)
        self.assertIsNone(close_time)
    
    @patch('home.utils.datetime')
    def test_is_closed_true_returns_none(self, mock_datetime):
        """Test that is_closed=True returns (None, None) even with times."""
        DailyOperatingHours.objects.create(
            day_of_week=0,
            open_time=time(9, 0),
            close_time=time(17, 0),
            is_closed=True  # Marked as closed
        )
        
        mock_now = Mock()
        mock_now.weekday.return_value = 0
        mock_datetime.now.return_value = mock_now
        
        open_time, close_time = get_today_operating_hours()
        
        self.assertIsNone(open_time)
        self.assertIsNone(close_time)
    
    @patch('home.utils.datetime')
    def test_midnight_hours(self, mock_datetime):
        """Test that midnight hours (24-hour operation) work correctly."""
        DailyOperatingHours.objects.create(
            day_of_week=0,
            open_time=time(0, 0),
            close_time=time(23, 59),
            is_closed=False
        )
        
        mock_now = Mock()
        mock_now.weekday.return_value = 0
        mock_datetime.now.return_value = mock_now
        
        open_time, close_time = get_today_operating_hours()
        
        self.assertEqual(open_time, time(0, 0))
        self.assertEqual(close_time, time(23, 59))
    
    @patch('home.utils.datetime')
    def test_early_morning_hours(self, mock_datetime):
        """Test early morning opening times (e.g., 6am)."""
        DailyOperatingHours.objects.create(
            day_of_week=0,
            open_time=time(6, 30),
            close_time=time(14, 30),
            is_closed=False
        )
        
        mock_now = Mock()
        mock_now.weekday.return_value = 0
        mock_datetime.now.return_value = mock_now
        
        open_time, close_time = get_today_operating_hours()
        
        self.assertEqual(open_time, time(6, 30))
        self.assertEqual(close_time, time(14, 30))
    
    @patch('home.utils.datetime')
    def test_late_night_hours(self, mock_datetime):
        """Test late night closing times (e.g., 11pm)."""
        DailyOperatingHours.objects.create(
            day_of_week=0,
            open_time=time(11, 0),
            close_time=time(23, 0),
            is_closed=False
        )
        
        mock_now = Mock()
        mock_now.weekday.return_value = 0
        mock_datetime.now.return_value = mock_now
        
        open_time, close_time = get_today_operating_hours()
        
        self.assertEqual(open_time, time(11, 0))
        self.assertEqual(close_time, time(23, 0))


class GetTodayOperatingHoursRealWorldTests(TestCase):
    """Test cases for real-world usage scenarios."""
    
    def setUp(self):
        """Set up realistic operating hours."""
        # Typical restaurant hours: Mon-Thu 11am-10pm, Fri-Sat 11am-11pm, Sun closed
        weekday_hours = [
            (0, time(11, 0), time(22, 0)),  # Monday
            (1, time(11, 0), time(22, 0)),  # Tuesday
            (2, time(11, 0), time(22, 0)),  # Wednesday
            (3, time(11, 0), time(22, 0)),  # Thursday
        ]
        for day, open_t, close_t in weekday_hours:
            DailyOperatingHours.objects.create(
                day_of_week=day,
                open_time=open_t,
                close_time=close_t,
                is_closed=False
            )
        
        # Weekend hours
        DailyOperatingHours.objects.create(
            day_of_week=4,  # Friday
            open_time=time(11, 0),
            close_time=time(23, 0),
            is_closed=False
        )
        DailyOperatingHours.objects.create(
            day_of_week=5,  # Saturday
            open_time=time(11, 0),
            close_time=time(23, 0),
            is_closed=False
        )
        DailyOperatingHours.objects.create(
            day_of_week=6,  # Sunday
            open_time=time(0, 0),
            close_time=time(0, 0),
            is_closed=True
        )
    
    @patch('home.utils.datetime')
    def test_typical_weekday(self, mock_datetime):
        """Test typical weekday hours (11am-10pm)."""
        mock_now = Mock()
        mock_now.weekday.return_value = 2  # Wednesday
        mock_datetime.now.return_value = mock_now
        
        open_time, close_time = get_today_operating_hours()
        
        self.assertEqual(open_time, time(11, 0))
        self.assertEqual(close_time, time(22, 0))
    
    @patch('home.utils.datetime')
    def test_typical_weekend(self, mock_datetime):
        """Test typical weekend hours (11am-11pm)."""
        mock_now = Mock()
        mock_now.weekday.return_value = 5  # Saturday
        mock_datetime.now.return_value = mock_now
        
        open_time, close_time = get_today_operating_hours()
        
        self.assertEqual(open_time, time(11, 0))
        self.assertEqual(close_time, time(23, 0))
    
    @patch('home.utils.datetime')
    def test_can_format_hours_for_display(self, mock_datetime):
        """Test that returned times can be formatted for display."""
        mock_now = Mock()
        mock_now.weekday.return_value = 0
        mock_datetime.now.return_value = mock_now
        
        open_time, close_time = get_today_operating_hours()
        
        # Format for display
        if open_time and close_time:
            hours_str = f"{open_time.strftime('%I:%M %p')} - {close_time.strftime('%I:%M %p')}"
            self.assertEqual(hours_str, "11:00 AM - 10:00 PM")
    
    @patch('home.utils.datetime')
    def test_can_check_if_open(self, mock_datetime):
        """Test that we can check if restaurant is open today."""
        # Test open day
        mock_now = Mock()
        mock_now.weekday.return_value = 0
        mock_datetime.now.return_value = mock_now
        
        open_time, close_time = get_today_operating_hours()
        is_open_today = open_time is not None and close_time is not None
        self.assertTrue(is_open_today)
        
        # Test closed day
        mock_now = Mock()
        mock_now.weekday.return_value = 6
        mock_datetime.now.return_value = mock_now
        
        open_time, close_time = get_today_operating_hours()
        is_open_today = open_time is not None and close_time is not None
        self.assertFalse(is_open_today)
    
    def test_function_works_with_actual_datetime(self):
        """Test that function works with actual datetime (not mocked)."""
        # This will use the actual current day
        result = get_today_operating_hours()
        
        # Should return a tuple
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        
        # Both values should be either None or time objects
        open_time, close_time = result
        if open_time is not None:
            self.assertIsInstance(open_time, time)
        if close_time is not None:
            self.assertIsInstance(close_time, time)
