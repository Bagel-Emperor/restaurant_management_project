#!/usr/bin/env python3
"""
Test Suite for Task 15A: Admin Ride History Serializers

This module provides comprehensive test coverage for admin ride history
filtering and display serializers. Tests validate date range filtering,
status filtering, driver-specific filtering, and proper data serialization
for admin dashboard functionality.

Test Coverage:
- RideHistoryFilterSerializer validation and field handling
- AdminRideHistorySerializer output formatting and field mapping
- Cross-field validation for date ranges
- Edge cases and error conditions
- Performance considerations for admin queries

Run with: python manage.py test test_task_15a_admin_ride_history
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
from orders.models import Ride, Driver, Rider
from orders.serializers import RideHistoryFilterSerializer, AdminRideHistorySerializer


class TaskC15ARideHistoryFilterSerializerTests(TestCase):
    """
    Test cases for RideHistoryFilterSerializer.
    
    Tests validate filtering parameter validation, cross-field validation
    for date ranges, and proper handling of optional filter fields for
    admin ride history queries.
    """

    def test_empty_filter_valid(self):
        """Test that empty filter (no fields) is valid for showing all rides."""
        serializer = RideHistoryFilterSerializer(data={})
        self.assertTrue(serializer.is_valid(), f"Empty filter should be valid, errors: {serializer.errors}")
        self.assertEqual(len(serializer.validated_data), 0)

    def test_start_date_only_valid(self):
        """Test filtering with only start_date specified."""
        data = {
            'start_date': '2025-07-01'
        }
        serializer = RideHistoryFilterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), f"Start date only should be valid, errors: {serializer.errors}")
        self.assertEqual(serializer.validated_data['start_date'], date(2025, 7, 1))

    def test_end_date_only_valid(self):
        """Test filtering with only end_date specified."""
        data = {
            'end_date': '2025-07-10'
        }
        serializer = RideHistoryFilterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), f"End date only should be valid, errors: {serializer.errors}")
        self.assertEqual(serializer.validated_data['end_date'], date(2025, 7, 10))

    def test_date_range_valid(self):
        """Test filtering with valid date range (start <= end)."""
        data = {
            'start_date': '2025-07-01',
            'end_date': '2025-07-10'
        }
        serializer = RideHistoryFilterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), f"Valid date range should be valid, errors: {serializer.errors}")
        self.assertEqual(serializer.validated_data['start_date'], date(2025, 7, 1))
        self.assertEqual(serializer.validated_data['end_date'], date(2025, 7, 10))

    def test_same_start_end_date_valid(self):
        """Test filtering with same start and end date (single day)."""
        data = {
            'start_date': '2025-07-05',
            'end_date': '2025-07-05'
        }
        serializer = RideHistoryFilterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), f"Same start/end date should be valid, errors: {serializer.errors}")
        self.assertEqual(serializer.validated_data['start_date'], date(2025, 7, 5))
        self.assertEqual(serializer.validated_data['end_date'], date(2025, 7, 5))

    def test_invalid_date_range_rejected(self):
        """Test that invalid date range (start > end) is rejected."""
        data = {
            'start_date': '2025-07-10',
            'end_date': '2025-07-01'  # end before start
        }
        serializer = RideHistoryFilterSerializer(data=data)
        self.assertFalse(serializer.is_valid(), "Invalid date range should be rejected")
        self.assertIn('non_field_errors', serializer.errors)
        error_message = str(serializer.errors['non_field_errors'][0])
        self.assertIn('Start date must be before or equal to end date', error_message)

    def test_status_completed_valid(self):
        """Test filtering by COMPLETED status."""
        data = {
            'status': 'COMPLETED'
        }
        serializer = RideHistoryFilterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), f"COMPLETED status should be valid, errors: {serializer.errors}")
        self.assertEqual(serializer.validated_data['status'], 'COMPLETED')

    def test_status_cancelled_valid(self):
        """Test filtering by CANCELLED status."""
        data = {
            'status': 'CANCELLED'
        }
        serializer = RideHistoryFilterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), f"CANCELLED status should be valid, errors: {serializer.errors}")
        self.assertEqual(serializer.validated_data['status'], 'CANCELLED')

    def test_invalid_status_rejected(self):
        """Test that invalid status values are rejected."""
        invalid_statuses = ['REQUESTED', 'ONGOING', 'INVALID', 'completed', '']
        
        for status in invalid_statuses:
            data = {'status': status}
            serializer = RideHistoryFilterSerializer(data=data)
            self.assertFalse(serializer.is_valid(), f"Invalid status '{status}' should be rejected")
            self.assertIn('status', serializer.errors)

    def test_driver_id_valid(self):
        """Test filtering by valid driver ID."""
        data = {
            'driver_id': 7
        }
        serializer = RideHistoryFilterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), f"Valid driver_id should be valid, errors: {serializer.errors}")
        self.assertEqual(serializer.validated_data['driver_id'], 7)

    def test_driver_id_zero_invalid(self):
        """Test that driver_id of 0 is rejected (min_value=1)."""
        data = {
            'driver_id': 0
        }
        serializer = RideHistoryFilterSerializer(data=data)
        self.assertFalse(serializer.is_valid(), "driver_id=0 should be rejected")
        self.assertIn('driver_id', serializer.errors)

    def test_driver_id_negative_invalid(self):
        """Test that negative driver_id is rejected."""
        data = {
            'driver_id': -5
        }
        serializer = RideHistoryFilterSerializer(data=data)
        self.assertFalse(serializer.is_valid(), "Negative driver_id should be rejected")
        self.assertIn('driver_id', serializer.errors)

    def test_all_fields_combined_valid(self):
        """Test filtering with all fields specified and valid."""
        data = {
            'start_date': '2025-06-01',
            'end_date': '2025-06-30',
            'status': 'COMPLETED',
            'driver_id': 12
        }
        serializer = RideHistoryFilterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), f"All valid fields should be valid, errors: {serializer.errors}")
        self.assertEqual(serializer.validated_data['start_date'], date(2025, 6, 1))
        self.assertEqual(serializer.validated_data['end_date'], date(2025, 6, 30))
        self.assertEqual(serializer.validated_data['status'], 'COMPLETED')
        self.assertEqual(serializer.validated_data['driver_id'], 12)


class TaskC15AAdminRideHistorySerializerTests(TestCase):
    """
    Test cases for AdminRideHistorySerializer.
    
    Tests validate proper serialization of Ride model data for admin views,
    including user name resolution, field mapping, and edge case handling
    for missing or null relationships.
    """

    def setUp(self):
        """Set up test data for serializer tests."""
        # Create test users
        self.rider_user = User.objects.create_user(
            username='test_rider',
            email='rider@test.com',
            first_name='Aarav',
            last_name='Kumar'
        )
        
        self.driver_user = User.objects.create_user(
            username='test_driver',
            email='driver@test.com',
            first_name='Riya',
            last_name='Sharma'
        )
        
        self.username_only_user = User.objects.create_user(
            username='username_only',
            email='username@test.com'
            # No first_name/last_name
        )

        # Create Rider and Driver profiles
        self.rider = Rider.objects.create(
            user=self.rider_user,
            phone='+919876543210'
        )
        
        self.driver = Driver.objects.create(
            user=self.driver_user,
            phone='+919876543211',
            license_number='DL123456789',
            license_expiry=date(2026, 12, 31),
            vehicle_make='Toyota',
            vehicle_model='Camry',
            vehicle_year=2022,
            vehicle_type='sedan',
            vehicle_color='White',
            license_plate='KA05AB1234',
            current_latitude=Decimal('12.9700000'),
            current_longitude=Decimal('77.5900000'),
            availability_status='available'
        )
        
        self.username_rider = Rider.objects.create(
            user=self.username_only_user,
            phone='+919876543212'
        )

    def test_completed_ride_serialization(self):
        """Test serialization of a completed ride with all fields."""
        ride = Ride.objects.create(
            rider=self.rider,
            driver=self.driver,
            pickup_address='Koramangala, Bangalore',
            pickup_lat=Decimal('12.9716000'),
            pickup_lng=Decimal('77.5946000'),
            dropoff_address='Indiranagar, Bangalore',
            drop_lat=Decimal('12.9800000'),
            drop_lng=Decimal('77.6000000'),
            fare=Decimal('340.50'),
            status='COMPLETED',
            payment_method='UPI',
            completed_at=datetime(2025, 7, 8, 14, 32, 12, tzinfo=timezone.utc)
        )

        serializer = AdminRideHistorySerializer(ride)
        data = serializer.data
        
        # Verify all expected fields are present
        expected_fields = ['ride_id', 'rider', 'driver', 'status', 'fare', 'payment_method', 'completed_at']
        self.assertEqual(set(data.keys()), set(expected_fields))
        
        # Verify field values
        self.assertEqual(data['ride_id'], ride.id)
        self.assertEqual(data['rider'], 'Aarav Kumar')  # full name
        self.assertEqual(data['driver'], 'Riya Sharma')  # full name
        self.assertEqual(data['status'], 'COMPLETED')
        self.assertEqual(Decimal(data['fare']), Decimal('340.50'))
        self.assertEqual(data['payment_method'], 'UPI')
        self.assertEqual(data['completed_at'], '2025-07-08T14:32:12Z')

    def test_cancelled_ride_serialization(self):
        """Test serialization of a cancelled ride."""
        ride = Ride.objects.create(
            rider=self.rider,
            driver=self.driver,
            pickup_address='Koramangala, Bangalore',
            pickup_lat=Decimal('12.9716000'),
            pickup_lng=Decimal('77.5946000'),
            dropoff_address='Indiranagar, Bangalore',
            drop_lat=Decimal('12.9800000'),
            drop_lng=Decimal('77.6000000'),
            fare=Decimal('0.00'),
            status='CANCELLED',
            payment_method='CASH',
            completed_at=datetime(2025, 7, 9, 10, 15, 30, tzinfo=timezone.utc)
        )

        serializer = AdminRideHistorySerializer(ride)
        data = serializer.data
        
        self.assertEqual(data['status'], 'CANCELLED')
        self.assertEqual(Decimal(data['fare']), Decimal('0.00'))
        self.assertEqual(data['payment_method'], 'CASH')

    def test_ride_with_username_only_users(self):
        """Test serialization when users only have username (no first/last name)."""
        username_driver = Driver.objects.create(
            user=self.username_only_user,
            phone='+919876543213',
            license_number='DL987654321',
            license_expiry=date(2026, 12, 31),
            vehicle_make='Honda',
            vehicle_model='Civic',
            vehicle_year=2021,
            vehicle_type='sedan',
            vehicle_color='Blue',
            license_plate='KA05CD5678',
            current_latitude=Decimal('12.9700000'),
            current_longitude=Decimal('77.5900000'),
            availability_status='available'
        )
        
        ride = Ride.objects.create(
            rider=self.username_rider,
            driver=username_driver,
            pickup_address='Whitefield, Bangalore',
            pickup_lat=Decimal('12.9716000'),
            pickup_lng=Decimal('77.5946000'),
            dropoff_address='Electronic City, Bangalore',
            drop_lat=Decimal('12.9800000'),
            drop_lng=Decimal('77.6000000'),
            fare=Decimal('250.00'),
            status='COMPLETED',
            payment_method='CARD',
            completed_at=datetime(2025, 7, 10, 16, 45, 0, tzinfo=timezone.utc)
        )

        serializer = AdminRideHistorySerializer(ride)
        data = serializer.data
        
        # Should fall back to username when no full name available
        self.assertEqual(data['rider'], 'username_only')
        self.assertEqual(data['driver'], 'username_only')

    def test_ride_without_driver(self):
        """Test serialization of ride without assigned driver (edge case)."""
        ride = Ride.objects.create(
            rider=self.rider,
            driver=None,  # No driver assigned
            pickup_address='MG Road, Bangalore',
            pickup_lat=Decimal('12.9716000'),
            pickup_lng=Decimal('77.5946000'),
            dropoff_address='Brigade Road, Bangalore',
            drop_lat=Decimal('12.9800000'),
            drop_lng=Decimal('77.6000000'),
            fare=Decimal('0.00'),
            status='CANCELLED',
            payment_method='UPI'
        )

        serializer = AdminRideHistorySerializer(ride)
        data = serializer.data
        
        self.assertEqual(data['rider'], 'Aarav Kumar')
        self.assertIsNone(data['driver'])  # Should be None for unassigned

    def test_multiple_rides_serialization(self):
        """Test serialization of multiple rides for list views."""
        rides = []
        
        # Create multiple rides with different data
        for i in range(3):
            ride = Ride.objects.create(
                rider=self.rider,
                driver=self.driver,
                pickup_address=f'Location {i+1}, Bangalore',
                pickup_lat=Decimal('12.9716000') + (Decimal('0.001000') * i),
                pickup_lng=Decimal('77.5946000') + (Decimal('0.001000') * i),
                dropoff_address=f'Destination {i+1}, Bangalore',
                drop_lat=Decimal('12.9800000') + (Decimal('0.001000') * i),
                drop_lng=Decimal('77.6000000') + (Decimal('0.001000') * i),
                fare=Decimal(f'{100 + (i * 50)}.00'),
                status='COMPLETED' if i % 2 == 0 else 'CANCELLED',
                payment_method=['UPI', 'CASH', 'CARD'][i],
                completed_at=datetime(2025, 7, 8 + i, 14, 30, 0, tzinfo=timezone.utc)
            )
            rides.append(ride)

        serializer = AdminRideHistorySerializer(rides, many=True)
        data = serializer.data
        
        # Verify we get 3 serialized rides
        self.assertEqual(len(data), 3)
        
        # Verify each ride has correct structure
        for i, ride_data in enumerate(data):
            expected_fields = ['ride_id', 'rider', 'driver', 'status', 'fare', 'payment_method', 'completed_at']
            self.assertEqual(set(ride_data.keys()), set(expected_fields))
            self.assertEqual(ride_data['ride_id'], rides[i].id)
            self.assertEqual(Decimal(ride_data['fare']), Decimal(f'{100 + (i * 50)}.00'))

    def test_decimal_fare_precision(self):
        """Test that fare maintains proper decimal precision."""
        test_fares = [
            Decimal('123.45'),
            Decimal('999.99'),
            Decimal('0.01'),
            Decimal('1000.00')
        ]
        
        for fare in test_fares:
            ride = Ride.objects.create(
                rider=self.rider,
                driver=self.driver,
                pickup_address='Test Pickup Location',
                pickup_lat=Decimal('12.9716000'),
                pickup_lng=Decimal('77.5946000'),
                dropoff_address='Test Dropoff Location',
                drop_lat=Decimal('12.9800000'),
                drop_lng=Decimal('77.6000000'),
                fare=fare,
                status='COMPLETED',
                payment_method='UPI',
                completed_at=datetime(2025, 7, 8, 14, 30, 0, tzinfo=timezone.utc)
            )

            serializer = AdminRideHistorySerializer(ride)
            serialized_fare = Decimal(serializer.data['fare'])
            self.assertEqual(serialized_fare, fare, f"Fare precision should be maintained for {fare}")
            
            # Clean up for next iteration
            ride.delete()


if __name__ == '__main__':
    import unittest
    
    # Create test suite
    test_classes = [
        TaskC15ARideHistoryFilterSerializerTests,
        TaskC15AAdminRideHistorySerializerTests
    ]
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"TASK 15A TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, failure in result.failures:
            print(f"- {test}: {failure.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, error in result.errors:
            error_lines = error.split('\n')
            error_msg = next((line for line in reversed(error_lines) if line.strip() and 'TypeError:' in line or 'Error:' in line), error_lines[-1] if error_lines else 'Unknown error')
            print(f"- {test}: {error_msg}")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)