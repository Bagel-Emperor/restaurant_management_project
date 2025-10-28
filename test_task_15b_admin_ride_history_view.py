#!/usr/bin/env python3
"""
Test Suite for Task 15B: Admin Ride History View

This module provides comprehensive test coverage for the admin ride history
API endpoint. Tests validate authentication, authorization, filtering logic,
query parameter validation, and proper data serialization for admin analytics.

Test Coverage:
- Authentication and admin authorization checks
- Query parameter validation and filtering
- Date range filtering with edge cases
- Status and driver filtering
- Combined filter scenarios
- Empty result handling

Run with: python manage.py test test_task_15b_admin_ride_history_view
Author: Restaurant Management System
Created: 2025-01-11
"""

import os
import sys
import django
from datetime import date, datetime, timezone
from decimal import Decimal

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_management.settings')

# Setup Django
django.setup()

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from orders.models import Ride, Driver, Rider


class TaskC15BAdminRideHistoryViewTests(TestCase):
    """
    Test cases for Admin Ride History View API endpoint.
    
    Tests validate the admin-only endpoint for querying ride history with
    various filters, ensuring proper authentication, authorization, and
    data retrieval for administrative monitoring and analytics.
    """

    def setUp(self):
        """Set up test data for admin ride history view tests."""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin_user',
            email='admin@test.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create regular user (non-admin)
        self.regular_user = User.objects.create_user(
            username='regular_user',
            email='regular@test.com',
            password='userpass123'
        )
        
        # Create test rider users
        self.rider_user1 = User.objects.create_user(
            username='rider1',
            email='rider1@test.com',
            first_name='Aarav',
            last_name='Kumar'
        )
        
        self.rider_user2 = User.objects.create_user(
            username='rider2',
            email='rider2@test.com',
            first_name='Maya',
            last_name='Sharma'
        )
        
        # Create test driver users
        self.driver_user1 = User.objects.create_user(
            username='driver1',
            email='driver1@test.com',
            first_name='Rakesh',
            last_name='Patel'
        )
        
        self.driver_user2 = User.objects.create_user(
            username='driver2',
            email='driver2@test.com',
            first_name='Sanjay',
            last_name='Singh'
        )
        
        # Create Rider profiles
        self.rider1 = Rider.objects.create(
            user=self.rider_user1,
            phone='+919876543210'
        )
        
        self.rider2 = Rider.objects.create(
            user=self.rider_user2,
            phone='+919876543211'
        )
        
        # Create Driver profiles
        self.driver1 = Driver.objects.create(
            user=self.driver_user1,
            phone='+919876543212',
            license_number='DL111111111',
            license_expiry=date(2026, 12, 31),
            vehicle_make='Toyota',
            vehicle_model='Camry',
            vehicle_year=2022,
            vehicle_type='sedan',
            vehicle_color='White',
            license_plate='KA05AB1111',
            current_latitude=Decimal('12.9700000'),
            current_longitude=Decimal('77.5900000'),
            availability_status='available'
        )
        
        self.driver2 = Driver.objects.create(
            user=self.driver_user2,
            phone='+919876543213',
            license_number='DL222222222',
            license_expiry=date(2026, 12, 31),
            vehicle_make='Honda',
            vehicle_model='City',
            vehicle_year=2021,
            vehicle_type='sedan',
            vehicle_color='Blue',
            license_plate='KA05AB2222',
            current_latitude=Decimal('12.9700000'),
            current_longitude=Decimal('77.5900000'),
            availability_status='available'
        )
        
        # Create test rides with different statuses and dates
        self.ride1 = Ride.objects.create(
            rider=self.rider1,
            driver=self.driver1,
            pickup_address='Koramangala, Bangalore',
            pickup_lat=Decimal('12.9716000'),
            pickup_lng=Decimal('77.5946000'),
            dropoff_address='Indiranagar, Bangalore',
            drop_lat=Decimal('12.9800000'),
            drop_lng=Decimal('77.6000000'),
            fare=Decimal('295.75'),
            status='COMPLETED',
            payment_method='CASH',
            completed_at=datetime(2025, 7, 7, 12, 34, 0, tzinfo=timezone.utc)
        )
        
        self.ride2 = Ride.objects.create(
            rider=self.rider2,
            driver=self.driver1,
            pickup_address='Whitefield, Bangalore',
            pickup_lat=Decimal('12.9716000'),
            pickup_lng=Decimal('77.5946000'),
            dropoff_address='Electronic City, Bangalore',
            drop_lat=Decimal('12.9800000'),
            drop_lng=Decimal('77.6000000'),
            fare=Decimal('450.00'),
            status='COMPLETED',
            payment_method='UPI',
            completed_at=datetime(2025, 7, 8, 14, 20, 0, tzinfo=timezone.utc)
        )
        
        self.ride3 = Ride.objects.create(
            rider=self.rider1,
            driver=self.driver2,
            pickup_address='MG Road, Bangalore',
            pickup_lat=Decimal('12.9716000'),
            pickup_lng=Decimal('77.5946000'),
            dropoff_address='Brigade Road, Bangalore',
            drop_lat=Decimal('12.9800000'),
            drop_lng=Decimal('77.6000000'),
            fare=Decimal('0.00'),
            status='CANCELLED',
            payment_method='CARD',
            completed_at=datetime(2025, 7, 9, 10, 15, 0, tzinfo=timezone.utc)
        )
        
        self.ride4 = Ride.objects.create(
            rider=self.rider2,
            driver=self.driver2,
            pickup_address='Jayanagar, Bangalore',
            pickup_lat=Decimal('12.9716000'),
            pickup_lng=Decimal('77.5946000'),
            dropoff_address='BTM Layout, Bangalore',
            drop_lat=Decimal('12.9800000'),
            drop_lng=Decimal('77.6000000'),
            fare=Decimal('180.50'),
            status='COMPLETED',
            payment_method='UPI',
            completed_at=datetime(2025, 7, 15, 16, 45, 0, tzinfo=timezone.utc)
        )
        
        # Initialize API client
        self.client = APIClient()
        
        # API endpoint
        self.url = '/PerpexBistro/orders/admin/ride-history/'

    def test_unauthenticated_access_rejected(self):
        """Test that unauthenticated users cannot access admin ride history."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_admin_access_rejected(self):
        """Test that non-admin authenticated users are rejected."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)
        self.assertIn('admin', response.data['error'].lower())

    def test_admin_access_allowed(self):
        """Test that admin users can access ride history."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_fetch_all_rides_no_filters(self):
        """Test fetching all rides without any filters."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)  # All 4 test rides

    def test_filter_by_status_completed(self):
        """Test filtering rides by COMPLETED status."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'status': 'COMPLETED'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # 3 completed rides
        
        for ride in response.data:
            self.assertEqual(ride['status'], 'COMPLETED')

    def test_filter_by_status_cancelled(self):
        """Test filtering rides by CANCELLED status."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'status': 'CANCELLED'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # 1 cancelled ride
        self.assertEqual(response.data[0]['status'], 'CANCELLED')

    def test_filter_by_driver_id(self):
        """Test filtering rides by specific driver ID."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'driver_id': self.driver1.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Driver1 has 2 rides
        
        for ride in response.data:
            self.assertEqual(ride['driver'], 'Rakesh Patel')

    def test_filter_by_date_range(self):
        """Test filtering rides by date range."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {
            'start_date': '2025-07-01',
            'end_date': '2025-07-10'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # 3 rides in July 1-10

    def test_filter_by_start_date_only(self):
        """Test filtering with only start_date specified."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'start_date': '2025-07-10'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only ride4 on July 15

    def test_filter_by_end_date_only(self):
        """Test filtering with only end_date specified."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'end_date': '2025-07-08'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # ride1 and ride2

    def test_combined_filters_status_and_driver(self):
        """Test combining status and driver_id filters."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {
            'status': 'COMPLETED',
            'driver_id': self.driver2.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only ride4 matches
        self.assertEqual(response.data[0]['driver'], 'Sanjay Singh')

    def test_combined_filters_all_parameters(self):
        """Test combining all filter parameters."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {
            'start_date': '2025-07-01',
            'end_date': '2025-07-10',
            'status': 'COMPLETED',
            'driver_id': self.driver1.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # ride1 and ride2

    def test_invalid_status_rejected(self):
        """Test that invalid status values are rejected."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'status': 'INVALID'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('status', response.data)

    def test_invalid_driver_id_rejected(self):
        """Test that invalid driver_id values are rejected."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'driver_id': 'not_a_number'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('driver_id', response.data)

    def test_invalid_date_format_rejected(self):
        """Test that invalid date formats are rejected."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'start_date': '07-01-2025'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('start_date', response.data)

    def test_invalid_date_range_rejected(self):
        """Test that invalid date ranges (start > end) are rejected."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {
            'start_date': '2025-07-20',
            'end_date': '2025-07-10'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_response_structure(self):
        """Test that response has correct structure and fields."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        
        # Check first ride has all expected fields
        ride = response.data[0]
        expected_fields = ['ride_id', 'rider', 'driver', 'status', 'fare', 'payment_method', 'completed_at']
        for field in expected_fields:
            self.assertIn(field, ride)

    def test_empty_result_set(self):
        """Test that empty result sets are handled correctly."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {
            'start_date': '2025-08-01',
            'end_date': '2025-08-31'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
        self.assertIsInstance(response.data, list)

    def test_rides_ordered_by_completed_at(self):
        """Test that rides are ordered by most recent first."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify descending order by completed_at
        if len(response.data) > 1:
            for i in range(len(response.data) - 1):
                current_time = datetime.fromisoformat(response.data[i]['completed_at'].replace('Z', '+00:00'))
                next_time = datetime.fromisoformat(response.data[i + 1]['completed_at'].replace('Z', '+00:00'))
                self.assertGreaterEqual(current_time, next_time)

    def test_fare_decimal_precision(self):
        """Test that fare values maintain proper decimal precision."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'status': 'COMPLETED'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        for ride in response.data:
            # Verify fare is present and numeric
            self.assertIn('fare', ride)
            fare_value = Decimal(str(ride['fare']))
            self.assertIsInstance(fare_value, Decimal)


if __name__ == '__main__':
    import unittest
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TaskC15BAdminRideHistoryViewTests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"TASK 15B TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, failure in result.failures:
            print(f"- {test}: {failure.split('AssertionError: ')[-1].split('\\n')[0] if 'AssertionError:' in failure else failure.split('\\n')[-2]}")
    
    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, error in result.errors:
            error_lines = error.split('\n')
            error_msg = next((line for line in reversed(error_lines) if line.strip() and ('Error:' in line or 'Exception' in line)), error_lines[-1] if error_lines else 'Unknown error')
            print(f"- {test}: {error_msg}")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
