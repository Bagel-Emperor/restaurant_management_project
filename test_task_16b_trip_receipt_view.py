#!/usr/bin/env python3
"""
Test Suite for Task 16B: Trip Receipt View

This module provides comprehensive test coverage for the trip receipt API
endpoint. Tests validate authentication, authorization, ride status validation,
and proper receipt delivery for riders and drivers.

Test Coverage:
- Authentication requirements
- Authorization (rider and driver access)
- Ride existence validation
- Ride completion status validation
- Unauthorized access prevention
- Receipt data structure

Run with: python test_task_16b_trip_receipt_view.py
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
from rest_framework.test import APIClient
from rest_framework import status
from orders.models import Ride, Driver, Rider


class TaskC16BTripReceiptViewTests(TestCase):
	"""
	Test cases for Trip Receipt View API endpoint.
	
	Tests validate the receipt retrieval endpoint that allows riders and
	drivers to view receipts for completed rides. Ensures proper authentication,
	authorization, and business rule enforcement.
	"""

	def setUp(self):
		"""Set up test data for trip receipt view tests."""
		# Create rider user
		self.rider_user = User.objects.create_user(
			username='rider_user',
			email='rider@test.com',
			password='riderpass123',
			first_name='Amit',
			last_name='Kumar'
		)
		
		# Create driver user
		self.driver_user = User.objects.create_user(
			username='driver_user',
			email='driver@test.com',
			password='driverpass123',
			first_name='Riya',
			last_name='Sharma'
		)
		
		# Create another rider (for unauthorized access tests)
		self.other_rider_user = User.objects.create_user(
			username='other_rider',
			email='other@test.com',
			password='otherpass123'
		)
		
		# Create rider profiles
		self.rider = Rider.objects.create(
			user=self.rider_user,
			phone='+919876543210'
		)
		
		self.other_rider = Rider.objects.create(
			user=self.other_rider_user,
			phone='+919876543211'
		)
		
		# Create driver profile
		self.driver = Driver.objects.create(
			user=self.driver_user,
			phone='+919876543212',
			license_number='DL1234567890',
			license_expiry=date(2026, 12, 31),
			vehicle_make='Honda',
			vehicle_model='City',
			vehicle_year=2023,
			vehicle_type='sedan',
			vehicle_color='White',
			license_plate='KA01AB1234',
			current_latitude=Decimal('12.9716'),
			current_longitude=Decimal('77.5946'),
			availability_status='available'
		)
		
		# Create completed ride
		self.completed_ride = Ride.objects.create(
			rider=self.rider,
			driver=self.driver,
			pickup_address='Koramangala, Bangalore',
			pickup_lat=Decimal('12.9350'),
			pickup_lng=Decimal('77.6244'),
			dropoff_address='Marathahalli, Bangalore',
			drop_lat=Decimal('12.9600'),
			drop_lng=Decimal('77.7000'),
			status='COMPLETED',
			fare=Decimal('310.75'),
			payment_method='UPI',
			completed_at=datetime(2025, 7, 10, 15, 32, 0, tzinfo=timezone.utc)
		)
		
		# Create ongoing ride (not completed)
		self.ongoing_ride = Ride.objects.create(
			rider=self.rider,
			driver=self.driver,
			pickup_address='Indiranagar, Bangalore',
			pickup_lat=Decimal('12.9716'),
			pickup_lng=Decimal('77.5946'),
			dropoff_address='HSR Layout, Bangalore',
			drop_lat=Decimal('12.9100'),
			drop_lng=Decimal('77.6400'),
			status='ONGOING',
			fare=Decimal('0.00'),
			payment_method='CASH'
		)
		
		# Create cancelled ride
		self.cancelled_ride = Ride.objects.create(
			rider=self.rider,
			driver=self.driver,
			pickup_address='MG Road, Bangalore',
			pickup_lat=Decimal('12.9750'),
			pickup_lng=Decimal('77.6060'),
			dropoff_address='Whitefield, Bangalore',
			drop_lat=Decimal('12.9698'),
			drop_lng=Decimal('77.7499'),
			status='CANCELLED',
			fare=Decimal('0.00'),
			payment_method='NONE'
		)
		
		# Initialize API client
		self.client = APIClient()
		
		# API endpoint pattern
		self.url_pattern = '/PerpexBistro/orders/ride/receipt/{}/'

	def test_unauthenticated_access_rejected(self):
		"""Test that unauthenticated users cannot access receipts."""
		url = self.url_pattern.format(self.completed_ride.id)
		response = self.client.get(url)
		
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_rider_can_view_own_receipt(self):
		"""Test that riders can view receipts for their own rides."""
		self.client.force_authenticate(user=self.rider_user)
		url = self.url_pattern.format(self.completed_ride.id)
		response = self.client.get(url)
		
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn('ride_id', response.data)
		self.assertEqual(response.data['ride_id'], self.completed_ride.id)
		self.assertEqual(response.data['rider'], 'Amit')
		self.assertEqual(response.data['driver'], 'Riya')

	def test_driver_can_view_assigned_ride_receipt(self):
		"""Test that drivers can view receipts for rides they drove."""
		self.client.force_authenticate(user=self.driver_user)
		url = self.url_pattern.format(self.completed_ride.id)
		response = self.client.get(url)
		
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn('ride_id', response.data)
		self.assertEqual(response.data['ride_id'], self.completed_ride.id)

	def test_unauthorized_user_cannot_view_receipt(self):
		"""Test that users who are neither rider nor driver are rejected."""
		self.client.force_authenticate(user=self.other_rider_user)
		url = self.url_pattern.format(self.completed_ride.id)
		response = self.client.get(url)
		
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
		self.assertIn('error', response.data)
		self.assertIn('not authorized', response.data['error'].lower())

	def test_nonexistent_ride_returns_404(self):
		"""Test that requesting receipt for nonexistent ride returns 404."""
		self.client.force_authenticate(user=self.rider_user)
		url = self.url_pattern.format(99999)  # Non-existent ID
		response = self.client.get(url)
		
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
		self.assertIn('error', response.data)
		self.assertIn('not found', response.data['error'].lower())

	def test_ongoing_ride_receipt_rejected(self):
		"""Test that receipts cannot be generated for ongoing rides."""
		self.client.force_authenticate(user=self.rider_user)
		url = self.url_pattern.format(self.ongoing_ride.id)
		response = self.client.get(url)
		
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('error', response.data)
		self.assertIn('completed', response.data['error'].lower())

	def test_cancelled_ride_receipt_rejected(self):
		"""Test that receipts cannot be generated for cancelled rides."""
		self.client.force_authenticate(user=self.rider_user)
		url = self.url_pattern.format(self.cancelled_ride.id)
		response = self.client.get(url)
		
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('error', response.data)
		self.assertIn('completed', response.data['error'].lower())

	def test_receipt_structure_complete(self):
		"""Test that receipt contains all required fields."""
		self.client.force_authenticate(user=self.rider_user)
		url = self.url_pattern.format(self.completed_ride.id)
		response = self.client.get(url)
		
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		
		# Verify all required fields present
		required_fields = [
			'ride_id', 'rider', 'driver', 'origin', 'destination',
			'fare', 'payment_method', 'status', 'completed_at'
		]
		for field in required_fields:
			self.assertIn(field, response.data, f"Missing field: {field}")

	def test_receipt_data_accuracy(self):
		"""Test that receipt data matches the ride data."""
		self.client.force_authenticate(user=self.rider_user)
		url = self.url_pattern.format(self.completed_ride.id)
		response = self.client.get(url)
		
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		
		# Verify data accuracy
		self.assertEqual(response.data['ride_id'], self.completed_ride.id)
		self.assertEqual(response.data['origin'], 'Koramangala, Bangalore')
		self.assertEqual(response.data['destination'], 'Marathahalli, Bangalore')
		self.assertEqual(response.data['fare'], '310.75')
		self.assertEqual(response.data['payment_method'], 'UPI')
		self.assertEqual(response.data['status'], 'COMPLETED')

	def test_receipt_rider_name_format(self):
		"""Test that rider name uses first name format."""
		self.client.force_authenticate(user=self.rider_user)
		url = self.url_pattern.format(self.completed_ride.id)
		response = self.client.get(url)
		
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['rider'], 'Amit')
		self.assertNotEqual(response.data['rider'], 'rider_user')  # Not username

	def test_receipt_driver_name_format(self):
		"""Test that driver name uses first name format."""
		self.client.force_authenticate(user=self.rider_user)
		url = self.url_pattern.format(self.completed_ride.id)
		response = self.client.get(url)
		
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['driver'], 'Riya')
		self.assertNotEqual(response.data['driver'], 'driver_user')  # Not username

	def test_receipt_completed_at_timestamp(self):
		"""Test that completed_at timestamp is properly formatted."""
		self.client.force_authenticate(user=self.rider_user)
		url = self.url_pattern.format(self.completed_ride.id)
		response = self.client.get(url)
		
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['completed_at'], '2025-07-10T15:32:00Z')

	def test_receipt_fare_decimal_precision(self):
		"""Test that fare maintains proper decimal precision."""
		self.client.force_authenticate(user=self.rider_user)
		url = self.url_pattern.format(self.completed_ride.id)
		response = self.client.get(url)
		
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['fare'], '310.75')

	def test_multiple_completed_rides_separate_receipts(self):
		"""Test that each completed ride has its own receipt."""
		# Create another completed ride
		ride2 = Ride.objects.create(
			rider=self.rider,
			driver=self.driver,
			pickup_address='Banashankari, Bangalore',
			pickup_lat=Decimal('12.9250'),
			pickup_lng=Decimal('77.5500'),
			dropoff_address='Jayanagar, Bangalore',
			drop_lat=Decimal('12.9250'),
			drop_lng=Decimal('77.5833'),
			status='COMPLETED',
			fare=Decimal('125.50'),
			payment_method='CASH',
			completed_at=datetime(2025, 7, 11, 10, 15, 0, tzinfo=timezone.utc)
		)
		
		self.client.force_authenticate(user=self.rider_user)
		
		# Get first receipt
		url1 = self.url_pattern.format(self.completed_ride.id)
		response1 = self.client.get(url1)
		
		# Get second receipt
		url2 = self.url_pattern.format(ride2.id)
		response2 = self.client.get(url2)
		
		self.assertEqual(response1.status_code, status.HTTP_200_OK)
		self.assertEqual(response2.status_code, status.HTTP_200_OK)
		
		# Verify receipts are different
		self.assertNotEqual(response1.data['ride_id'], response2.data['ride_id'])
		self.assertNotEqual(response1.data['fare'], response2.data['fare'])
		self.assertNotEqual(response1.data['origin'], response2.data['origin'])

	def test_ride_without_driver_receipt_handling(self):
		"""Test receipt handling for rides that somehow completed without driver."""
		# Create edge case: completed ride without driver
		ride_no_driver = Ride.objects.create(
			rider=self.rider,
			driver=None,
			pickup_address='Test Origin',
			pickup_lat=Decimal('12.9716'),
			pickup_lng=Decimal('77.5946'),
			dropoff_address='Test Destination',
			drop_lat=Decimal('12.9000'),
			drop_lng=Decimal('77.6000'),
			status='COMPLETED',
			fare=Decimal('100.00'),
			payment_method='CASH',
			completed_at=datetime.now(timezone.utc)
		)
		
		self.client.force_authenticate(user=self.rider_user)
		url = self.url_pattern.format(ride_no_driver.id)
		response = self.client.get(url)
		
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['driver'], 'Not Assigned')


def run_tests():
	"""Execute the test suite and print detailed results."""
	import unittest
	
	# Create test suite
	loader = unittest.TestLoader()
	suite = loader.loadTestsFromTestCase(TaskC16BTripReceiptViewTests)
	
	# Run tests with detailed output
	runner = unittest.TextTestRunner(verbosity=2)
	result = runner.run(suite)
	
	# Print summary
	print("\n" + "="*60)
	print("TASK 16B TEST SUMMARY")
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
