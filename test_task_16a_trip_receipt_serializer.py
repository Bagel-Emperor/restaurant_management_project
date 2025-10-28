#!/usr/bin/env python3
"""
Test Suite for Task 16A: Trip Receipt Serializer

This module provides comprehensive test coverage for the TripReceiptSerializer
which generates structured, professional receipts for completed rides. Tests
validate field structure, data formatting, name resolution, and edge cases.

Test Coverage:
- Receipt structure and required fields
- Rider/driver name formatting (first name preference)
- Fare decimal precision
- Origin/destination inclusion
- Payment method and status fields
- Timestamp formatting
- Edge cases (missing rider, missing driver, incomplete data)

Run with: python test_task_16a_trip_receipt_serializer.py
Author: Restaurant Management System
Created: 2025-10-27
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
from orders.serializers import TripReceiptSerializer


class TaskC16ATripReceiptSerializerTests(TestCase):
    """
    Test cases for Trip Receipt Serializer.
    
    Tests validate the serializer's ability to generate professional,
    structured receipts for completed rides with proper field formatting,
    name resolution, and edge case handling.
    """

    def setUp(self):
        """Set up test data for trip receipt serializer tests."""
        # Create rider user with first name for receipt
        self.rider_user = User.objects.create_user(
            username='sneha_rider',
            email='sneha@test.com',
            first_name='Sneha',
            last_name='Patel',
            password='riderpass123'
        )
        
        # Create driver user with first name for receipt
        self.driver_user = User.objects.create_user(
            username='karan_driver',
            email='karan@test.com',
            first_name='Karan',
            last_name='Singh',
            password='driverpass123'
        )
        
        # Create rider user without first name (username fallback)
        self.rider_user_no_name = User.objects.create_user(
            username='rider_username_only',
            email='rider_no_name@test.com',
            password='riderpass123'
        )
        
        # Create driver user without first name (username fallback)
        self.driver_user_no_name = User.objects.create_user(
            username='driver_username_only',
            email='driver_no_name@test.com',
            password='driverpass123'
        )
        
        # Create rider and driver instances
        self.rider = Rider.objects.create(
            user=self.rider_user,
            phone='+919876543210'
        )
        
        self.driver = Driver.objects.create(
            user=self.driver_user,
            phone='+919876543211',
            license_number='DL1234567890',
            license_expiry=date(2026, 12, 31),
            vehicle_make='Honda',
            vehicle_model='Accord',
            vehicle_year=2023,
            vehicle_type='sedan',
            vehicle_color='Black',
            license_plate='KA01AB1234',
            current_latitude=Decimal('12.9716'),
            current_longitude=Decimal('77.5946'),
            availability_status='available'
        )
        
        self.rider_no_name = Rider.objects.create(
            user=self.rider_user_no_name,
            phone='+919876543212'
        )
        
        self.driver_no_name = Driver.objects.create(
            user=self.driver_user_no_name,
            phone='+919876543213',
            license_number='DL0987654321',
            license_expiry=date(2027, 6, 30),
            vehicle_make='Toyota',
            vehicle_model='Camry',
            vehicle_year=2022,
            vehicle_type='sedan',
            vehicle_color='White',
            license_plate='KA02CD5678',
            current_latitude=Decimal('12.9716'),
            current_longitude=Decimal('77.5946'),
            availability_status='available'
        )
        
        # Create completed ride for receipt generation
        self.completed_ride = Ride.objects.create(
            rider=self.rider,
            driver=self.driver,
            pickup_address='Indiranagar, Bangalore',
            pickup_lat=Decimal('12.9716'),
            pickup_lng=Decimal('77.5946'),
            dropoff_address='HSR Layout, Bangalore',
            drop_lat=Decimal('12.9350'),
            drop_lng=Decimal('77.6244'),
            status='COMPLETED',
            fare=Decimal('275.00'),
            payment_method='UPI',
            completed_at=datetime(2025, 7, 10, 18, 15, 0, tzinfo=timezone.utc)
        )
        
        # Create completed ride with high-precision fare
        self.ride_precise_fare = Ride.objects.create(
            rider=self.rider,
            driver=self.driver,
            pickup_address='MG Road, Bangalore',
            pickup_lat=Decimal('12.9716'),
            pickup_lng=Decimal('77.5946'),
            dropoff_address='Whitefield, Bangalore',
            drop_lat=Decimal('12.9000'),
            drop_lng=Decimal('77.6000'),
            status='COMPLETED',
            fare=Decimal('456.75'),
            payment_method='CARD',
            completed_at=datetime(2025, 7, 11, 9, 30, 0, tzinfo=timezone.utc)
        )
        
        # Create ride with users who have no first names
        self.ride_no_names = Ride.objects.create(
            rider=self.rider_no_name,
            driver=self.driver_no_name,
            pickup_address='Electronic City, Bangalore',
            pickup_lat=Decimal('12.9716'),
            pickup_lng=Decimal('77.5946'),
            dropoff_address='Koramangala, Bangalore',
            drop_lat=Decimal('13.0000'),
            drop_lng=Decimal('77.7000'),
            status='COMPLETED',
            fare=Decimal('350.00'),
            payment_method='CASH',
            completed_at=datetime(2025, 7, 12, 14, 45, 0, tzinfo=timezone.utc)
        )

    def test_receipt_structure_all_fields_present(self):
        """Test that receipt contains all required fields."""
        serializer = TripReceiptSerializer(self.completed_ride)
        data = serializer.data
        
        # Verify all required fields are present
        required_fields = [
            'ride_id', 'rider', 'driver', 'origin', 'destination',
            'fare', 'payment_method', 'status', 'completed_at'
        ]
        
        for field in required_fields:
            self.assertIn(field, data, f"Field '{field}' missing from receipt")

    def test_ride_id_matches_database_id(self):
        """Test that ride_id field matches the database ID."""
        serializer = TripReceiptSerializer(self.completed_ride)
        data = serializer.data
        
        self.assertEqual(data['ride_id'], self.completed_ride.id)
        self.assertIsInstance(data['ride_id'], int)

    def test_rider_name_uses_first_name(self):
        """Test that rider field uses first name when available."""
        serializer = TripReceiptSerializer(self.completed_ride)
        data = serializer.data
        
        # Should use first name "Sneha" not full name or username
        self.assertEqual(data['rider'], 'Sneha')
        self.assertNotEqual(data['rider'], 'sneha_rider')  # Not username
        self.assertNotEqual(data['rider'], 'Sneha Patel')  # Not full name

    def test_driver_name_uses_first_name(self):
        """Test that driver field uses first name when available."""
        serializer = TripReceiptSerializer(self.completed_ride)
        data = serializer.data
        
        # Should use first name "Karan" not full name or username
        self.assertEqual(data['driver'], 'Karan')
        self.assertNotEqual(data['driver'], 'karan_driver')  # Not username
        self.assertNotEqual(data['driver'], 'Karan Singh')  # Not full name

    def test_rider_name_fallback_to_username(self):
        """Test that rider field falls back to username when no first name."""
        serializer = TripReceiptSerializer(self.ride_no_names)
        data = serializer.data
        
        # Should fall back to username when no first name available
        self.assertEqual(data['rider'], 'rider_username_only')

    def test_driver_name_fallback_to_username(self):
        """Test that driver field falls back to username when no first name."""
        serializer = TripReceiptSerializer(self.ride_no_names)
        data = serializer.data
        
        # Should fall back to username when no first name available
        self.assertEqual(data['driver'], 'driver_username_only')

    def test_origin_destination_included(self):
        """Test that origin and destination are included in receipt."""
        serializer = TripReceiptSerializer(self.completed_ride)
        data = serializer.data
        
        self.assertEqual(data['origin'], 'Indiranagar, Bangalore')
        self.assertEqual(data['destination'], 'HSR Layout, Bangalore')

    def test_fare_decimal_precision(self):
        """Test that fare maintains proper decimal precision."""
        serializer = TripReceiptSerializer(self.completed_ride)
        data = serializer.data
        
        # Fare should be decimal with 2 places
        self.assertEqual(data['fare'], '275.00')
        
        # Test with different fare value
        serializer2 = TripReceiptSerializer(self.ride_precise_fare)
        data2 = serializer2.data
        self.assertEqual(data2['fare'], '456.75')

    def test_payment_method_included(self):
        """Test that payment method is included in receipt."""
        serializer = TripReceiptSerializer(self.completed_ride)
        data = serializer.data
        
        self.assertEqual(data['payment_method'], 'UPI')
        
        # Test with different payment method
        serializer2 = TripReceiptSerializer(self.ride_precise_fare)
        data2 = serializer2.data
        self.assertEqual(data2['payment_method'], 'CARD')

    def test_status_included(self):
        """Test that ride status is included in receipt."""
        serializer = TripReceiptSerializer(self.completed_ride)
        data = serializer.data
        
        self.assertEqual(data['status'], 'COMPLETED')

    def test_completed_at_timestamp_format(self):
        """Test that completed_at timestamp is properly formatted."""
        serializer = TripReceiptSerializer(self.completed_ride)
        data = serializer.data
        
        # Should be ISO 8601 formatted timestamp
        self.assertIn('completed_at', data)
        self.assertEqual(data['completed_at'], '2025-07-10T18:15:00Z')

    def test_multiple_receipts_serialization(self):
        """Test serializing multiple rides for batch receipt generation."""
        rides = [self.completed_ride, self.ride_precise_fare, self.ride_no_names]
        serializer = TripReceiptSerializer(rides, many=True)
        data = serializer.data
        
        # Should return list of 3 receipts
        self.assertEqual(len(data), 3)
        
        # Each should have all required fields
        for receipt in data:
            self.assertIn('ride_id', receipt)
            self.assertIn('rider', receipt)
            self.assertIn('driver', receipt)
            self.assertIn('fare', receipt)

    def test_receipt_matches_sample_format(self):
        """Test that receipt structure matches the specification sample."""
        serializer = TripReceiptSerializer(self.completed_ride)
        data = serializer.data
        
        # Verify structure matches sample from spec
        expected_structure = {
            'ride_id': 'int',
            'rider': 'str',
            'driver': 'str',
            'origin': 'str',
            'destination': 'str',
            'fare': 'decimal',
            'payment_method': 'str',
            'status': 'str',
            'completed_at': 'timestamp'
        }
        
        for field, expected_type in expected_structure.items():
            self.assertIn(field, data, f"Missing field: {field}")

    def test_receipt_read_only_fields(self):
        """Test that all receipt fields are read-only."""
        serializer = TripReceiptSerializer(self.completed_ride)
        
        # All fields should be read-only
        for field_name in serializer.fields:
            field = serializer.fields[field_name]
            self.assertTrue(
                field.read_only,
                f"Field '{field_name}' should be read-only for receipts"
            )

    def test_missing_driver_handled_gracefully(self):
        """Test that receipts handle rides with no assigned driver."""
        # Create ride without driver
        ride_no_driver = Ride.objects.create(
            rider=self.rider,
            driver=None,
            pickup_address='Test Origin',
            pickup_lat=Decimal('12.9716'),
            pickup_lng=Decimal('77.5946'),
            dropoff_address='Test Destination',
            drop_lat=Decimal('12.9000'),
            drop_lng=Decimal('77.6000'),
            status='CANCELLED',
            fare=Decimal('0.00'),
            payment_method='NONE'
        )
        
        serializer = TripReceiptSerializer(ride_no_driver)
        data = serializer.data
        
        # Should return "Not Assigned" for missing driver
        self.assertEqual(data['driver'], 'Not Assigned')

    def test_fare_zero_handling(self):
        """Test that receipts handle zero fare correctly."""
        ride_free = Ride.objects.create(
            rider=self.rider,
            driver=self.driver,
            pickup_address='Promo Origin',
            pickup_lat=Decimal('12.9716'),
            pickup_lng=Decimal('77.5946'),
            dropoff_address='Promo Destination',
            drop_lat=Decimal('12.9000'),
            drop_lng=Decimal('77.6000'),
            status='COMPLETED',
            fare=Decimal('0.00'),
            payment_method='PROMO',
            completed_at=datetime.now(timezone.utc)
        )
        
        serializer = TripReceiptSerializer(ride_free)
        data = serializer.data
        
        self.assertEqual(data['fare'], '0.00')
        self.assertEqual(data['payment_method'], 'PROMO')


def run_tests():
    """Execute the test suite and print detailed results."""
    import unittest
    from io import StringIO
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TaskC16ATripReceiptSerializerTests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*60)
    print("TASK 16A TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError: ')[-1].split()[0] if 'AssertionError:' in traceback else 'See details above'}")
    
    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            error_msg = traceback.strip().split('\n')[-1]
            print(f"- {test}: {error_msg}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
