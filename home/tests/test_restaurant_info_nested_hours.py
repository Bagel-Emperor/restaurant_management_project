"""
Tests for Restaurant Info API with nested DailyOperatingHours.

This module tests the /api/restaurant-info/ endpoint which returns
comprehensive restaurant information including nested daily operating hours.
"""

from datetime import time
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from home.models import Restaurant, RestaurantLocation, DailyOperatingHours


class RestaurantInfoWithNestedHoursAPITests(TestCase):
    """Test suite for Restaurant Info API with nested daily operating hours."""
    
    def setUp(self):
        """Set up test client and test data."""
        self.client = APIClient()
        self.url = reverse('restaurant-info')
        
        # Create a restaurant
        self.restaurant = Restaurant.objects.create(
            name='Perpex Bistro',
            owner_name='John Doe',
            email='contact@perpexbistro.com',
            phone_number='555-0123',
            opening_hours={
                'Monday': '9:00 AM - 10:00 PM',
                'Friday': '9:00 AM - 11:00 PM'
            },
            has_delivery=True
        )
        
        # Create restaurant location
        self.location = RestaurantLocation.objects.create(
            restaurant=self.restaurant,
            address='123 Main St',
            city='New York',
            state='NY',
            zip_code='10001'
        )
        
        # Create daily operating hours for all 7 days
        self.daily_hours = []
        hours_config = [
            (0, time(9, 0), time(22, 0), False),   # Monday
            (1, time(9, 0), time(22, 0), False),   # Tuesday
            (2, time(9, 0), time(22, 0), False),   # Wednesday
            (3, time(9, 0), time(23, 0), False),   # Thursday
            (4, time(9, 0), time(23, 0), False),   # Friday
            (5, time(10, 0), time(23, 0), False),  # Saturday
            (6, time(10, 0), time(21, 0), False),  # Sunday
        ]
        
        for day, open_time, close_time, is_closed in hours_config:
            daily_hour = DailyOperatingHours.objects.create(
                day_of_week=day,
                open_time=open_time,
                close_time=close_time,
                is_closed=is_closed
            )
            self.daily_hours.append(daily_hour)
    
    def test_restaurant_info_includes_nested_daily_hours(self):
        """Test that restaurant info includes nested daily_operating_hours field."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('restaurant', response.data)
        
        restaurant_data = response.data['restaurant']
        
        # Assert daily_operating_hours field exists
        self.assertIn('daily_operating_hours', restaurant_data)
        
        # Assert it's a list
        self.assertIsInstance(restaurant_data['daily_operating_hours'], list)
    
    def test_daily_operating_hours_structure(self):
        """Test the structure of each daily operating hours entry."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        daily_hours = response.data['restaurant']['daily_operating_hours']
        
        # Should have 7 days
        self.assertEqual(len(daily_hours), 7)
        
        # Check first entry structure
        monday = daily_hours[0]
        expected_fields = {'id', 'day_of_week', 'day_name', 'open_time', 'close_time', 'is_closed'}
        actual_fields = set(monday.keys())
        
        self.assertEqual(expected_fields, actual_fields)
    
    def test_daily_operating_hours_content(self):
        """Test the actual content of daily operating hours."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        daily_hours = response.data['restaurant']['daily_operating_hours']
        
        # Check Monday
        monday = daily_hours[0]
        self.assertEqual(monday['day_of_week'], 0)
        self.assertEqual(monday['day_name'], 'Monday')
        self.assertEqual(monday['open_time'], '09:00 AM')
        self.assertEqual(monday['close_time'], '10:00 PM')
        self.assertFalse(monday['is_closed'])
        
        # Check Friday (later hours)
        friday = daily_hours[4]
        self.assertEqual(friday['day_of_week'], 4)
        self.assertEqual(friday['day_name'], 'Friday')
        self.assertEqual(friday['open_time'], '09:00 AM')
        self.assertEqual(friday['close_time'], '11:00 PM')
        self.assertFalse(friday['is_closed'])
        
        # Check Sunday
        sunday = daily_hours[6]
        self.assertEqual(sunday['day_of_week'], 6)
        self.assertEqual(sunday['day_name'], 'Sunday')
        self.assertEqual(sunday['open_time'], '10:00 AM')
        self.assertEqual(sunday['close_time'], '09:00 PM')
        self.assertFalse(sunday['is_closed'])
    
    def test_daily_operating_hours_ordering(self):
        """Test that daily hours are ordered Monday to Sunday."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        daily_hours = response.data['restaurant']['daily_operating_hours']
        
        # Verify ordering
        expected_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        actual_days = [day['day_name'] for day in daily_hours]
        
        self.assertEqual(expected_days, actual_days)
    
    def test_daily_operating_hours_with_closed_day(self):
        """Test daily operating hours when restaurant is closed on a specific day."""
        # Mark Sunday as closed
        sunday = DailyOperatingHours.objects.get(day_of_week=6)
        sunday.is_closed = True
        sunday.save()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        daily_hours = response.data['restaurant']['daily_operating_hours']
        sunday_data = daily_hours[6]
        
        # When closed, times should be None
        self.assertTrue(sunday_data['is_closed'])
        self.assertIsNone(sunday_data['open_time'])
        self.assertIsNone(sunday_data['close_time'])
    
    def test_restaurant_info_with_no_daily_hours(self):
        """Test restaurant info when no daily operating hours exist."""
        # Delete all daily operating hours
        DailyOperatingHours.objects.all().delete()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return empty array
        daily_hours = response.data['restaurant']['daily_operating_hours']
        self.assertEqual(daily_hours, [])
    
    def test_restaurant_info_includes_both_hour_formats(self):
        """Test that response includes both opening_hours (JSON) and daily_operating_hours (nested)."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        restaurant_data = response.data['restaurant']
        
        # Both fields should exist
        self.assertIn('opening_hours', restaurant_data)
        self.assertIn('daily_operating_hours', restaurant_data)
        
        # opening_hours should be dict
        self.assertIsInstance(restaurant_data['opening_hours'], dict)
        
        # daily_operating_hours should be list
        self.assertIsInstance(restaurant_data['daily_operating_hours'], list)
    
    def test_restaurant_info_complete_response_structure(self):
        """Test that response includes all expected fields."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('restaurant', response.data)
        
        restaurant_data = response.data['restaurant']
        
        expected_fields = [
            'id', 'name', 'owner_name', 'email', 'phone_number',
            'opening_hours', 'has_delivery', 'address', 'city', 'state',
            'zip_code', 'full_address', 'daily_operating_hours', 'created_at'
        ]
        
        for field in expected_fields:
            self.assertIn(field, restaurant_data, f"Missing field: {field}")
    
    def test_daily_hours_time_formatting(self):
        """Test that times are formatted correctly (12-hour format with AM/PM)."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        daily_hours = response.data['restaurant']['daily_operating_hours']
        
        # Check time format for Monday (09:00 should be 09:00 AM)
        monday = daily_hours[0]
        self.assertRegex(monday['open_time'], r'^\d{2}:\d{2} (AM|PM)$')
        self.assertRegex(monday['close_time'], r'^\d{2}:\d{2} (AM|PM)$')
    
    def test_restaurant_info_public_access(self):
        """Test that restaurant info endpoint is publicly accessible."""
        # Ensure no authentication
        self.client.force_authenticate(user=None)
        
        response = self.client.get(self.url)
        
        # Should still be accessible
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('daily_operating_hours', response.data['restaurant'])
    
    def test_daily_hours_read_only(self):
        """Test that daily operating hours are read-only in the response."""
        response = self.client.get(self.url)
        original_hours = response.data['restaurant']['daily_operating_hours']
        
        # Response should be consistent
        response = self.client.get(self.url)
        self.assertEqual(response.data['restaurant']['daily_operating_hours'], original_hours)
    
    def test_multiple_closed_days(self):
        """Test handling of multiple closed days."""
        # Mark Saturday and Sunday as closed
        DailyOperatingHours.objects.filter(day_of_week__in=[5, 6]).update(is_closed=True)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        daily_hours = response.data['restaurant']['daily_operating_hours']
        
        # Check Saturday
        saturday = daily_hours[5]
        self.assertTrue(saturday['is_closed'])
        self.assertIsNone(saturday['open_time'])
        self.assertIsNone(saturday['close_time'])
        
        # Check Sunday
        sunday = daily_hours[6]
        self.assertTrue(sunday['is_closed'])
        self.assertIsNone(sunday['open_time'])
        self.assertIsNone(sunday['close_time'])
    
    def test_daily_hours_independent_of_opening_hours_json(self):
        """Test that daily_operating_hours and opening_hours are independent."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        restaurant_data = response.data['restaurant']
        
        # opening_hours is the JSONField (simplified)
        self.assertEqual(restaurant_data['opening_hours']['Monday'], '9:00 AM - 10:00 PM')
        
        # daily_operating_hours is the detailed nested structure
        monday_detailed = restaurant_data['daily_operating_hours'][0]
        self.assertEqual(monday_detailed['day_name'], 'Monday')
        self.assertEqual(monday_detailed['open_time'], '09:00 AM')
        self.assertEqual(monday_detailed['close_time'], '10:00 PM')
