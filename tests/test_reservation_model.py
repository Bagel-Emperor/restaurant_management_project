"""
Comprehensive test suite for the Reservation model and find_available_slots method.

Tests cover:
- Model creation and validation
- Past date/time validation
- Party size validation
- Duration validation
- Finding available time slots
- Overlap detection
- Edge cases
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import datetime, timedelta, time, date
from home.models import Reservation, Table, Restaurant


class ReservationModelTestCase(TestCase):
	"""Test cases for the Reservation model."""
	
	def setUp(self):
		"""Set up test data."""
		# Create a restaurant
		self.restaurant = Restaurant.objects.create(
			name="Test Restaurant",
			owner_name="Test Owner",
			email="owner@test.com",
			phone_number="555-0100"
		)
		
		# Create tables
		self.table_2_seats = Table.objects.create(
			restaurant=self.restaurant,
			number=1,
			capacity=2,
			location='indoor',
			status='available'
		)
		
		self.table_4_seats = Table.objects.create(
			restaurant=self.restaurant,
			number=2,
			capacity=4,
			location='indoor',
			status='available'
		)
		
		# Create a test user
		self.user = User.objects.create_user(
			username='testuser',
			email='test@example.com',
			password='testpass123'
		)
	
	def test_create_valid_reservation(self):
		"""Test creating a valid reservation."""
		future_date = timezone.now() + timedelta(days=7)
		reservation = Reservation.objects.create(
			customer_name="John Doe",
			customer_email="john@example.com",
			customer_phone="555-0123",
			table=self.table_2_seats,
			party_size=2,
			reservation_date=future_date.date(),
			reservation_time=time(18, 0),
			duration_minutes=120,
			status='pending'
		)
		
		self.assertIsNotNone(reservation.id)
		self.assertEqual(reservation.customer_name, "John Doe")
		self.assertEqual(reservation.party_size, 2)
		self.assertEqual(reservation.status, 'pending')
	
	def test_reservation_with_user(self):
		"""Test creating a reservation linked to a user account."""
		future_date = timezone.now() + timedelta(days=3)
		reservation = Reservation.objects.create(
			customer_name="Test User",
			customer_email="test@example.com",
			customer_phone="555-0456",
			table=self.table_4_seats,
			party_size=3,
			reservation_date=future_date.date(),
			reservation_time=time(19, 30),
			user=self.user
		)
		
		self.assertEqual(reservation.user, self.user)
		self.assertIn(reservation, self.user.reservations.all())
	
	def test_reservation_datetime_property(self):
		"""Test that reservation_datetime property combines date and time correctly."""
		future_date = timezone.now() + timedelta(days=5)
		reservation = Reservation.objects.create(
			customer_name="Jane Smith",
			customer_email="jane@example.com",
			customer_phone="555-0789",
			table=self.table_2_seats,
			party_size=2,
			reservation_date=future_date.date(),
			reservation_time=time(20, 0),
		)
		
		expected_datetime = timezone.make_aware(
			datetime.combine(future_date.date(), time(20, 0))
		)
		self.assertEqual(reservation.reservation_datetime, expected_datetime)
	
	def test_end_datetime_property(self):
		"""Test that end_datetime calculates correctly based on duration."""
		future_date = timezone.now() + timedelta(days=2)
		reservation = Reservation.objects.create(
			customer_name="Bob Johnson",
			customer_email="bob@example.com",
			customer_phone="555-0321",
			table=self.table_4_seats,
			party_size=4,
			reservation_date=future_date.date(),
			reservation_time=time(18, 30),
			duration_minutes=90
		)
		
		expected_end = reservation.reservation_datetime + timedelta(minutes=90)
		self.assertEqual(reservation.end_datetime, expected_end)
	
	def test_is_past_property(self):
		"""Test is_past property for past reservations."""
		past_date = timezone.now() - timedelta(days=1)
		# Note: This will fail validation, so we need to bypass it
		reservation = Reservation(
			customer_name="Past Customer",
			customer_email="past@example.com",
			customer_phone="555-0111",
			table=self.table_2_seats,
			party_size=2,
			reservation_date=past_date.date(),
			reservation_time=time(12, 0),
		)
		# Save without validation
		reservation.save = lambda: super(Reservation, reservation).save()
		
		# Just test the property logic without saving
		self.assertTrue(reservation.is_past)
		self.assertFalse(reservation.is_upcoming)
	
	def test_is_upcoming_property(self):
		"""Test is_upcoming property for future reservations."""
		future_date = timezone.now() + timedelta(days=10)
		reservation = Reservation.objects.create(
			customer_name="Future Customer",
			customer_email="future@example.com",
			customer_phone="555-0222",
			table=self.table_2_seats,
			party_size=2,
			reservation_date=future_date.date(),
			reservation_time=time(19, 0),
		)
		
		self.assertTrue(reservation.is_upcoming)
		self.assertFalse(reservation.is_past)
	
	def test_prevent_past_reservation(self):
		"""Test that creating a reservation in the past raises ValidationError."""
		past_date = timezone.now() - timedelta(days=1)
		
		with self.assertRaises(ValidationError) as context:
			Reservation.objects.create(
				customer_name="Past Attempt",
				customer_email="past@example.com",
				customer_phone="555-0333",
				table=self.table_2_seats,
				party_size=2,
				reservation_date=past_date.date(),
				reservation_time=time(12, 0),
			)
		
		self.assertIn("past date and time", str(context.exception))
	
	def test_party_size_exceeds_table_capacity(self):
		"""Test that party size exceeding table capacity raises ValidationError."""
		future_date = timezone.now() + timedelta(days=3)
		
		with self.assertRaises(ValidationError) as context:
			Reservation.objects.create(
				customer_name="Large Party",
				customer_email="large@example.com",
				customer_phone="555-0444",
				table=self.table_2_seats,  # Capacity: 2
				party_size=5,  # Too many people
				reservation_date=future_date.date(),
				reservation_time=time(18, 0),
			)
		
		self.assertIn("exceeds table capacity", str(context.exception))
	
	def test_minimum_duration_validation(self):
		"""Test that duration less than 30 minutes raises ValidationError."""
		future_date = timezone.now() + timedelta(days=2)
		
		with self.assertRaises(ValidationError) as context:
			Reservation.objects.create(
				customer_name="Quick Visit",
				customer_email="quick@example.com",
				customer_phone="555-0555",
				table=self.table_2_seats,
				party_size=2,
				reservation_date=future_date.date(),
				reservation_time=time(12, 0),
				duration_minutes=15  # Too short
			)
		
		self.assertIn("at least 30 minutes", str(context.exception))
	
	def test_maximum_duration_validation(self):
		"""Test that duration exceeding 8 hours raises ValidationError."""
		future_date = timezone.now() + timedelta(days=2)
		
		with self.assertRaises(ValidationError) as context:
			Reservation.objects.create(
				customer_name="Long Stay",
				customer_email="long@example.com",
				customer_phone="555-0666",
				table=self.table_4_seats,
				party_size=4,
				reservation_date=future_date.date(),
				reservation_time=time(10, 0),
				duration_minutes=500  # Over 8 hours
			)
		
		self.assertIn("cannot exceed 8 hours", str(context.exception))
	
	def test_reservation_str_representation(self):
		"""Test string representation of reservation."""
		future_date = timezone.now() + timedelta(days=1)
		reservation = Reservation.objects.create(
			customer_name="Test Customer",
			customer_email="test@example.com",
			customer_phone="555-0777",
			table=self.table_2_seats,
			party_size=2,
			reservation_date=future_date.date(),
			reservation_time=time(19, 30),
		)
		
		expected_str = f"Test Customer - Table {self.table_2_seats.number} on {future_date.date()} at 19:30:00"
		self.assertEqual(str(reservation), expected_str)
	
	def test_unique_table_datetime_constraint(self):
		"""Test that same table cannot be double-booked at the same time."""
		future_date = timezone.now() + timedelta(days=4)
		
		# Create first reservation
		Reservation.objects.create(
			customer_name="First Customer",
			customer_email="first@example.com",
			customer_phone="555-0888",
			table=self.table_2_seats,
			party_size=2,
			reservation_date=future_date.date(),
			reservation_time=time(18, 0),
		)
		
		# Attempt to create second reservation at same time
		# Should raise ValidationError from full_clean() or IntegrityError from database
		with self.assertRaises((ValidationError, Exception)):
			Reservation.objects.create(
				customer_name="Second Customer",
				customer_email="second@example.com",
				customer_phone="555-0999",
				table=self.table_2_seats,
				party_size=2,
				reservation_date=future_date.date(),
				reservation_time=time(18, 0),
			)
	
	def test_special_requests_field(self):
		"""Test that special requests are saved correctly."""
		future_date = timezone.now() + timedelta(days=6)
		special_request = "Window seat preferred, celebrating anniversary"
		
		reservation = Reservation.objects.create(
			customer_name="Anniversary Couple",
			customer_email="couple@example.com",
			customer_phone="555-1000",
			table=self.table_2_seats,
			party_size=2,
			reservation_date=future_date.date(),
			reservation_time=time(20, 0),
			special_requests=special_request
		)
		
		self.assertEqual(reservation.special_requests, special_request)
	
	def test_default_duration(self):
		"""Test that default duration is 120 minutes."""
		future_date = timezone.now() + timedelta(days=1)
		reservation = Reservation.objects.create(
			customer_name="Default Duration",
			customer_email="default@example.com",
			customer_phone="555-1100",
			table=self.table_2_seats,
			party_size=2,
			reservation_date=future_date.date(),
			reservation_time=time(18, 0),
		)
		
		self.assertEqual(reservation.duration_minutes, 120)


class FindAvailableSlotsTestCase(TestCase):
	"""Test cases for the find_available_slots class method."""
	
	def setUp(self):
		"""Set up test data."""
		# Create a restaurant
		self.restaurant = Restaurant.objects.create(
			name="Slot Test Restaurant",
			owner_name="Slot Owner",
			email="slots@test.com",
			phone_number="555-2000"
		)
		
		# Create a test table
		self.table = Table.objects.create(
			restaurant=self.restaurant,
			number=10,
			capacity=4,
			location='indoor',
			status='available'
		)
	
	def test_find_slots_no_existing_reservations(self):
		"""Test finding slots when no reservations exist."""
		start = timezone.now() + timedelta(days=1)
		start = start.replace(hour=17, minute=0, second=0, microsecond=0)
		end = start.replace(hour=22, minute=0)
		
		slots = Reservation.find_available_slots(
			table=self.table,
			start_datetime=start,
			end_datetime=end,
			duration_minutes=120,
			slot_interval_minutes=30
		)
		
		# Should have multiple slots available
		self.assertGreater(len(slots), 0)
		# Each slot should have required keys
		for slot in slots:
			self.assertIn('start_time', slot)
			self.assertIn('end_time', slot)
			self.assertIn('formatted_start', slot)
			self.assertIn('formatted_end', slot)
	
	def test_find_slots_with_existing_reservation(self):
		"""Test finding slots when a reservation exists."""
		# Create a reservation from 18:00 to 20:00
		future_date = timezone.now() + timedelta(days=2)
		future_date = future_date.replace(hour=18, minute=0, second=0, microsecond=0)
		
		Reservation.objects.create(
			customer_name="Existing Customer",
			customer_email="existing@example.com",
			customer_phone="555-2100",
			table=self.table,
			party_size=4,
			reservation_date=future_date.date(),
			reservation_time=time(18, 0),
			duration_minutes=120,
			status='confirmed'
		)
		
		# Search for slots on the same day
		start = future_date.replace(hour=17, minute=0)
		end = future_date.replace(hour=22, minute=0)
		
		slots = Reservation.find_available_slots(
			table=self.table,
			start_datetime=start,
			end_datetime=end,
			duration_minutes=120,
			slot_interval_minutes=30
		)
		
		# Verify that none of the available slots overlap with 18:00-20:00
		occupied_start = future_date.replace(hour=18, minute=0)
		occupied_end = future_date.replace(hour=20, minute=0)
		
		for slot in slots:
			slot_start = slot['start_time']
			slot_end = slot['end_time']
			# Ensure no overlap
			overlaps = (slot_start < occupied_end and slot_end > occupied_start)
			self.assertFalse(overlaps, f"Slot {slot['formatted_start']} to {slot['formatted_end']} overlaps with existing reservation")
	
	def test_find_slots_multiple_reservations(self):
		"""Test finding slots with multiple existing reservations."""
		future_date = timezone.now() + timedelta(days=3)
		future_date = future_date.replace(hour=12, minute=0, second=0, microsecond=0)
		
		# Create two reservations
		Reservation.objects.create(
			customer_name="Lunch Customer 1",
			customer_email="lunch1@example.com",
			customer_phone="555-2200",
			table=self.table,
			party_size=2,
			reservation_date=future_date.date(),
			reservation_time=time(12, 0),
			duration_minutes=90,
			status='confirmed'
		)
		
		Reservation.objects.create(
			customer_name="Dinner Customer",
			customer_email="dinner@example.com",
			customer_phone="555-2300",
			table=self.table,
			party_size=4,
			reservation_date=future_date.date(),
			reservation_time=time(18, 30),
			duration_minutes=120,
			status='pending'
		)
		
		# Search for slots
		start = future_date.replace(hour=11, minute=0)
		end = future_date.replace(hour=22, minute=0)
		
		slots = Reservation.find_available_slots(
			table=self.table,
			start_datetime=start,
			end_datetime=end,
			duration_minutes=120,
			slot_interval_minutes=30
		)
		
		# Should find some available slots between and around the reservations
		self.assertGreater(len(slots), 0)
	
	def test_find_slots_cancelled_reservations_ignored(self):
		"""Test that cancelled reservations don't block availability."""
		future_date = timezone.now() + timedelta(days=4)
		future_date = future_date.replace(hour=19, minute=0, second=0, microsecond=0)
		
		# Create a cancelled reservation
		Reservation.objects.create(
			customer_name="Cancelled Customer",
			customer_email="cancelled@example.com",
			customer_phone="555-2400",
			table=self.table,
			party_size=3,
			reservation_date=future_date.date(),
			reservation_time=time(19, 0),
			duration_minutes=120,
			status='cancelled'  # This shouldn't block slots
		)
		
		# Search for slots
		start = future_date.replace(hour=18, minute=0)
		end = future_date.replace(hour=21, minute=0)
		
		slots = Reservation.find_available_slots(
			table=self.table,
			start_datetime=start,
			end_datetime=end,
			duration_minutes=120,
			slot_interval_minutes=30
		)
		
		# The 19:00 slot should be available since the reservation is cancelled
		slot_at_19 = any(
			slot['start_time'].hour == 19 and slot['start_time'].minute == 0
			for slot in slots
		)
		self.assertTrue(slot_at_19, "19:00 slot should be available since reservation is cancelled")
	
	def test_find_slots_past_range_returns_empty(self):
		"""Test that searching for slots entirely in the past returns empty list."""
		past_start = timezone.now() - timedelta(days=2)
		past_end = timezone.now() - timedelta(days=1)
		
		slots = Reservation.find_available_slots(
			table=self.table,
			start_datetime=past_start,
			end_datetime=past_end,
			duration_minutes=120
		)
		
		self.assertEqual(len(slots), 0)
	
	def test_find_slots_adjusts_past_start_time(self):
		"""Test that if start time is in the past, it's adjusted to now."""
		past_start = timezone.now() - timedelta(hours=2)
		future_end = timezone.now() + timedelta(hours=4)
		
		# Record the time before calling find_available_slots
		time_before_call = timezone.now()
		
		slots = Reservation.find_available_slots(
			table=self.table,
			start_datetime=past_start,
			end_datetime=future_end,
			duration_minutes=120,
			slot_interval_minutes=60
		)
		
		# Should still find slots (starting from now, not past)
		# Verify that first slot starts after the time_before_call
		if len(slots) > 0:
			first_slot_start = slots[0]['start_time']
			self.assertGreaterEqual(first_slot_start, time_before_call)
	
	def test_find_slots_custom_duration(self):
		"""Test finding slots with custom duration."""
		future_date = timezone.now() + timedelta(days=5)
		start = future_date.replace(hour=18, minute=0, second=0, microsecond=0)
		end = start + timedelta(hours=3)
		
		# Request 60-minute slots instead of default 120
		slots = Reservation.find_available_slots(
			table=self.table,
			start_datetime=start,
			end_datetime=end,
			duration_minutes=60,
			slot_interval_minutes=30
		)
		
		# Verify slot durations are correct
		for slot in slots:
			duration = slot['end_time'] - slot['start_time']
			self.assertEqual(duration.total_seconds() / 60, 60)
	
	def test_find_slots_custom_interval(self):
		"""Test finding slots with custom interval."""
		future_date = timezone.now() + timedelta(days=6)
		start = future_date.replace(hour=12, minute=0, second=0, microsecond=0)
		end = start + timedelta(hours=2)
		
		# Request 15-minute intervals
		slots = Reservation.find_available_slots(
			table=self.table,
			start_datetime=start,
			end_datetime=end,
			duration_minutes=60,
			slot_interval_minutes=15
		)
		
		# Should have more slots with smaller interval
		self.assertGreater(len(slots), 0)
	
	def test_find_slots_formatting(self):
		"""Test that formatted strings are correct."""
		future_date = timezone.now() + timedelta(days=7)
		start = future_date.replace(hour=19, minute=30, second=0, microsecond=0)
		end = start + timedelta(hours=1)
		
		slots = Reservation.find_available_slots(
			table=self.table,
			start_datetime=start,
			end_datetime=end,
			duration_minutes=30,
			slot_interval_minutes=30
		)
		
		if len(slots) > 0:
			slot = slots[0]
			# Check format: 'YYYY-MM-DD HH:MM'
			self.assertRegex(slot['formatted_start'], r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}')
			self.assertRegex(slot['formatted_end'], r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}')
	
	def test_find_slots_edge_case_exact_fit(self):
		"""Test when existing reservation exactly fills a potential slot."""
		future_date = timezone.now() + timedelta(days=8)
		
		# Create reservation from 18:00 to 20:00
		Reservation.objects.create(
			customer_name="Exact Fit",
			customer_email="exact@example.com",
			customer_phone="555-2500",
			table=self.table,
			party_size=4,
			reservation_date=future_date.date(),
			reservation_time=time(18, 0),
			duration_minutes=120,
			status='confirmed'
		)
		
		# Search for 120-minute slots from 17:00 to 21:00
		start = future_date.replace(hour=17, minute=0, second=0, microsecond=0)
		end = future_date.replace(hour=21, minute=0)
		
		slots = Reservation.find_available_slots(
			table=self.table,
			start_datetime=start,
			end_datetime=end,
			duration_minutes=120,
			slot_interval_minutes=30
		)
		
		# The 18:00 slot should NOT be available
		slot_at_18 = any(
			slot['start_time'].hour == 18 and slot['start_time'].minute == 0
			for slot in slots
		)
		self.assertFalse(slot_at_18)
	
	def test_find_slots_different_table_not_affected(self):
		"""Test that reservations for other tables don't affect availability."""
		# Create another table
		other_table = Table.objects.create(
			restaurant=self.restaurant,
			number=20,
			capacity=2,
			location='outdoor',
			status='available'
		)
		
		future_date = timezone.now() + timedelta(days=9)
		
		# Create reservation for OTHER table
		Reservation.objects.create(
			customer_name="Other Table Customer",
			customer_email="other@example.com",
			customer_phone="555-2600",
			table=other_table,  # Different table
			party_size=2,
			reservation_date=future_date.date(),
			reservation_time=time(19, 0),
			duration_minutes=120,
			status='confirmed'
		)
		
		# Search for slots on our original table
		start = future_date.replace(hour=18, minute=0, second=0, microsecond=0)
		end = future_date.replace(hour=21, minute=0)
		
		slots = Reservation.find_available_slots(
			table=self.table,  # Our original table
			start_datetime=start,
			end_datetime=end,
			duration_minutes=120,
			slot_interval_minutes=30
		)
		
		# The 19:00 slot should be available on our table
		slot_at_19 = any(
			slot['start_time'].hour == 19 and slot['start_time'].minute == 0
			for slot in slots
		)
		self.assertTrue(slot_at_19, "19:00 slot should be available on different table")
