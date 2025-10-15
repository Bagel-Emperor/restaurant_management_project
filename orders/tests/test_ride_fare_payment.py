"""
Django TestCase for Ride Fare Calculation and Payment Flow (Tasks 10A, 10B, 11A, 11B).

This comprehensive test suite covers:
- Task 10A: FareCalculationSerializer logic and validation
- Task 10B: calculate_fare API endpoint
- Task 11A: RidePaymentSerializer logic and validation
- Task 11B: mark_ride_as_paid API endpoint

Uses Django TestCase with automatic database rollback for test isolation.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
import math

from orders.models import Ride, Rider, Driver
from orders.serializers import FareCalculationSerializer, RidePaymentSerializer


class FareCalculationSerializerTest(TestCase):
    """
    Test suite for FareCalculationSerializer (Task 10A).
    
    Tests the fare calculation logic, Haversine distance formula,
    validation rules, and error handling.
    """
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all test methods."""
        # Create test users
        cls.rider_user = User.objects.create_user(
            username='test_rider',
            password='testpass123',
            email='rider@test.com'
        )
        cls.driver_user = User.objects.create_user(
            username='test_driver',
            password='testpass123',
            email='driver@test.com'
        )
        
        # Create rider and driver profiles
        from datetime import date, timedelta
        cls.rider = Rider.objects.create(
            user=cls.rider_user,
            phone='1234567890'
        )
        cls.driver = Driver.objects.create(
            user=cls.driver_user,
            phone='0987654321',
            license_number='DL123456',
            license_expiry=date.today() + timedelta(days=365),
            vehicle_make='Toyota',
            vehicle_model='Camry',
            vehicle_year=2020,
            vehicle_color='Black',
            vehicle_type='sedan',
            license_plate='ABC1234'
        )
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a completed ride for fare calculation
        self.completed_ride = Ride.objects.create(
            rider=self.rider,
            driver=self.driver,
            pickup_address='Test Pickup',
            pickup_lat=Decimal('28.7041'),  # New Delhi
            pickup_lng=Decimal('77.1025'),
            dropoff_address='Test Dropoff',
            drop_lat=Decimal('28.5355'),  # Noida
            drop_lng=Decimal('77.3910'),
            status=Ride.STATUS_COMPLETED,
            surge_multiplier=Decimal('1.0')
        )
    
    def test_fare_calculation_success(self):
        """Test successful fare calculation for a completed ride."""
        serializer = FareCalculationSerializer(instance=self.completed_ride, data={})
        
        # Run validation which triggers fare calculation
        self.assertTrue(serializer.is_valid(raise_exception=True))
        
        # Reload ride from database to get updated fare
        self.completed_ride.refresh_from_db()
        
        # Fare should be calculated and saved
        self.assertIsNotNone(self.completed_ride.fare)
        self.assertGreater(self.completed_ride.fare, 0)
        
        # Verify fare formula: base_fare (50) + (distance × per_km_rate (10)) × surge (1.0)
        # Distance between New Delhi and Noida is approximately 33.8 km
        # Expected fare ≈ 50 + (33.8 * 10) * 1.0 = 388
        self.assertGreaterEqual(self.completed_ride.fare, 385)
        self.assertLessEqual(self.completed_ride.fare, 391)
    
    def test_fare_calculation_with_surge_multiplier(self):
        """Test fare calculation with surge pricing (1.5x)."""
        # Create ride with 1.5x surge
        surge_ride = Ride.objects.create(
            rider=self.rider,
            driver=self.driver,
            pickup_address='Test Pickup',
            pickup_lat=Decimal('28.7041'),
            pickup_lng=Decimal('77.1025'),
            dropoff_address='Test Dropoff',
            drop_lat=Decimal('28.5355'),
            drop_lng=Decimal('77.3910'),
            status=Ride.STATUS_COMPLETED,
            surge_multiplier=Decimal('1.5')
        )
        
        serializer = FareCalculationSerializer(instance=surge_ride, data={})
        serializer.is_valid(raise_exception=True)
        
        surge_ride.refresh_from_db()
        
        # With 1.5x surge, fare should be higher
        # Expected ≈ 50 + (33.8 * 10) * 1.5 = 557
        self.assertGreaterEqual(surge_ride.fare, 554)
        self.assertLessEqual(surge_ride.fare, 560)
    
    def test_fare_calculation_incomplete_ride_error(self):
        """Test that fare calculation fails for incomplete rides."""
        # Create ride in ONGOING status
        ongoing_ride = Ride.objects.create(
            rider=self.rider,
            driver=self.driver,
            pickup_address='Test Pickup',
            pickup_lat=Decimal('28.7041'),
            pickup_lng=Decimal('77.1025'),
            dropoff_address='Test Dropoff',
            drop_lat=Decimal('28.5355'),
            drop_lng=Decimal('77.3910'),
            status=Ride.STATUS_ONGOING,
            surge_multiplier=Decimal('1.0')
        )
        
        serializer = FareCalculationSerializer(instance=ongoing_ride, data={})
        
        # Should raise validation error
        with self.assertRaises(Exception) as context:
            serializer.is_valid(raise_exception=True)
        
        self.assertIn('must be completed', str(context.exception).lower())
    
    def test_fare_already_calculated_error(self):
        """Test that fare calculation prevents re-calculation."""
        # Set fare manually
        self.completed_ride.fare = Decimal('150.00')
        self.completed_ride.save()
        
        serializer = FareCalculationSerializer(instance=self.completed_ride, data={})
        
        # Should raise validation error
        with self.assertRaises(Exception) as context:
            serializer.is_valid(raise_exception=True)
        
        self.assertIn('already been calculated', str(context.exception).lower())
    
    def test_haversine_distance_calculation(self):
        """Test the accuracy of Haversine distance calculation."""
        serializer = FareCalculationSerializer(instance=self.completed_ride, data={})
        
        # Calculate distance between New Delhi and Noida
        distance = serializer._calculate_distance(
            28.7041, 77.1025,  # New Delhi
            28.5355, 77.3910   # Noida
        )
        
        # Distance should be approximately 33.8 km
        self.assertGreaterEqual(distance, 33)
        self.assertLessEqual(distance, 35)


class CalculateFareAPITest(TestCase):
    """
    Test suite for calculate_fare API endpoint (Task 10B).
    
    Tests authentication, authorization, error handling, and
    successful fare calculation through the API.
    """
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all test methods."""
        # Create test users
        cls.rider_user = User.objects.create_user(
            username='test_rider',
            password='testpass123'
        )
        cls.driver_user = User.objects.create_user(
            username='test_driver',
            password='testpass123'
        )
        cls.other_user = User.objects.create_user(
            username='other_user',
            password='testpass123'
        )
        cls.admin_user = User.objects.create_user(
            username='admin',
            password='testpass123',
            is_staff=True
        )
        
        # Create profiles
        from datetime import date, timedelta
        cls.rider = Rider.objects.create(
            user=cls.rider_user,
            phone='1234567890'
        )
        cls.driver = Driver.objects.create(
            user=cls.driver_user,
            phone='0987654321',
            license_number='DL123456',
            license_expiry=date.today() + timedelta(days=365),
            vehicle_make='Toyota',
            vehicle_model='Camry',
            vehicle_year=2020,
            vehicle_color='Black',
            vehicle_type='sedan',
            license_plate='ABC1234'
        )
        cls.other_rider = Rider.objects.create(user=cls.other_user, phone='5555555555')
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.client = APIClient()
        
        # Create completed ride
        self.completed_ride = Ride.objects.create(
            rider=self.rider,
            driver=self.driver,
            pickup_address='Pickup',
            pickup_lat=Decimal('28.7041'),
            pickup_lng=Decimal('77.1025'),
            dropoff_address='Dropoff',
            drop_lat=Decimal('28.5355'),
            drop_lng=Decimal('77.3910'),
            status=Ride.STATUS_COMPLETED,
            surge_multiplier=Decimal('1.0')
        )
        
        # Get JWT tokens
        self.rider_token = self._get_token(self.rider_user)
        self.driver_token = self._get_token(self.driver_user)
        self.admin_token = self._get_token(self.admin_user)
        self.other_token = self._get_token(self.other_user)
    
    def _get_token(self, user):
        """Helper to get JWT token for a user."""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_calculate_fare_success_as_rider(self):
        """Test successful fare calculation by ride requester (rider)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.rider_token}')
        
        url = reverse('calculate-fare', kwargs={'ride_id': self.completed_ride.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('fare', response.data)
        self.assertIn('message', response.data)
        self.assertGreater(response.data['fare'], 0)
    
    def test_calculate_fare_success_as_driver(self):
        """Test successful fare calculation by assigned driver."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.driver_token}')
        
        url = reverse('calculate-fare', kwargs={'ride_id': self.completed_ride.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('fare', response.data)
    
    def test_calculate_fare_success_as_admin(self):
        """Test successful fare calculation by admin user."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        url = reverse('calculate-fare', kwargs={'ride_id': self.completed_ride.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('fare', response.data)
    
    def test_calculate_fare_unauthorized_user(self):
        """Test that unauthorized users cannot calculate fare."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.other_token}')
        
        url = reverse('calculate-fare', kwargs={'ride_id': self.completed_ride.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)
    
    def test_calculate_fare_no_authentication(self):
        """Test that authentication is required."""
        url = reverse('calculate-fare', kwargs={'ride_id': self.completed_ride.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_calculate_fare_nonexistent_ride(self):
        """Test error when ride doesn't exist."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.rider_token}')
        
        url = reverse('calculate-fare', kwargs={'ride_id': 99999})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_calculate_fare_incomplete_ride(self):
        """Test error when trying to calculate fare for incomplete ride."""
        # Create ongoing ride
        ongoing_ride = Ride.objects.create(
            rider=self.rider,
            driver=self.driver,
            pickup_address='Pickup',
            pickup_lat=Decimal('28.7041'),
            pickup_lng=Decimal('77.1025'),
            dropoff_address='Dropoff',
            drop_lat=Decimal('28.5355'),
            drop_lng=Decimal('77.3910'),
            status=Ride.STATUS_ONGOING
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.rider_token}')
        url = reverse('calculate-fare', kwargs={'ride_id': ongoing_ride.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('must be completed', response.data['error'].lower())
    
    def test_calculate_fare_already_set(self):
        """Test error when fare is already calculated."""
        # Set fare first
        self.completed_ride.fare = Decimal('200.00')
        self.completed_ride.save()
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.rider_token}')
        url = reverse('calculate-fare', kwargs={'ride_id': self.completed_ride.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already set', response.data['error'].lower())


class RidePaymentSerializerTest(TestCase):
    """
    Test suite for RidePaymentSerializer (Task 11A).
    
    Tests payment marking logic, validation rules, and
    timestamp recording.
    """
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all test methods."""
        from datetime import date, timedelta
        cls.rider_user = User.objects.create_user(username='rider', password='pass')
        cls.driver_user = User.objects.create_user(username='driver', password='pass')
        
        cls.rider = Rider.objects.create(user=cls.rider_user, phone='1234567890')
        cls.driver = Driver.objects.create(
            user=cls.driver_user,
            phone='0987654321',
            license_number='DL123',
            license_expiry=date.today() + timedelta(days=365),
            vehicle_make='Toyota',
            vehicle_model='Camry',
            vehicle_year=2020,
            vehicle_color='Black',
            vehicle_type='sedan',
            license_plate='ABC123'
        )
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.completed_ride = Ride.objects.create(
            rider=self.rider,
            driver=self.driver,
            pickup_address='Pickup',
            pickup_lat=Decimal('28.7041'),
            pickup_lng=Decimal('77.1025'),
            dropoff_address='Dropoff',
            drop_lat=Decimal('28.5355'),
            drop_lng=Decimal('77.3910'),
            status=Ride.STATUS_COMPLETED,
            fare=Decimal('150.00')
        )
    
    def test_mark_as_paid_success(self):
        """Test successfully marking a ride as paid."""
        data = {
            'payment_method': Ride.PAYMENT_METHOD_CASH,
            'payment_status': Ride.PAYMENT_STATUS_PAID
        }
        
        serializer = RidePaymentSerializer(instance=self.completed_ride, data=data)
        self.assertTrue(serializer.is_valid())
        
        updated_ride = serializer.save()
        
        self.assertEqual(updated_ride.payment_status, Ride.PAYMENT_STATUS_PAID)
        self.assertEqual(updated_ride.payment_method, Ride.PAYMENT_METHOD_CASH)
        self.assertIsNotNone(updated_ride.paid_at)
    
    def test_paid_at_timestamp_recorded(self):
        """Test that paid_at timestamp is set when marking as paid."""
        data = {
            'payment_method': Ride.PAYMENT_METHOD_UPI,
            'payment_status': Ride.PAYMENT_STATUS_PAID
        }
        
        before_time = timezone.now()
        
        serializer = RidePaymentSerializer(instance=self.completed_ride, data=data)
        serializer.is_valid(raise_exception=True)
        updated_ride = serializer.save()
        
        after_time = timezone.now()
        
        # Verify paid_at is between before and after times
        self.assertGreaterEqual(updated_ride.paid_at, before_time)
        self.assertLessEqual(updated_ride.paid_at, after_time)
    
    def test_payment_incomplete_ride_error(self):
        """Test that payment cannot be marked for incomplete rides."""
        ongoing_ride = Ride.objects.create(
            rider=self.rider,
            driver=self.driver,
            pickup_address='Pickup',
            pickup_lat=Decimal('28.7041'),
            pickup_lng=Decimal('77.1025'),
            dropoff_address='Dropoff',
            drop_lat=Decimal('28.5355'),
            drop_lng=Decimal('77.3910'),
            status=Ride.STATUS_ONGOING
        )
        
        data = {
            'payment_method': Ride.PAYMENT_METHOD_CASH,
            'payment_status': Ride.PAYMENT_STATUS_PAID
        }
        
        serializer = RidePaymentSerializer(instance=ongoing_ride, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('must be completed', str(serializer.errors).lower())
    
    def test_payment_already_paid_error(self):
        """Test that payment cannot be modified once paid."""
        # Mark as paid first
        self.completed_ride.payment_status = Ride.PAYMENT_STATUS_PAID
        self.completed_ride.payment_method = Ride.PAYMENT_METHOD_CASH
        self.completed_ride.paid_at = timezone.now()
        self.completed_ride.save()
        
        # Try to change payment method
        data = {
            'payment_method': Ride.PAYMENT_METHOD_UPI,
            'payment_status': Ride.PAYMENT_STATUS_PAID
        }
        
        serializer = RidePaymentSerializer(instance=self.completed_ride, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('already marked as paid', str(serializer.errors).lower())
    
    def test_payment_method_required_when_paid(self):
        """Test that payment_method is required when marking as paid."""
        data = {
            'payment_status': Ride.PAYMENT_STATUS_PAID
            # Missing payment_method
        }
        
        serializer = RidePaymentSerializer(instance=self.completed_ride, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('payment method', str(serializer.errors).lower())


class MarkRideAsPaidAPITest(TestCase):
    """
    Test suite for mark_ride_as_paid API endpoint (Task 11B).
    
    Tests authentication, authorization, payment recording,
    and error handling.
    """
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all test methods."""
        from datetime import date, timedelta
        cls.rider_user = User.objects.create_user(username='rider', password='pass')
        cls.driver_user = User.objects.create_user(username='driver', password='pass')
        cls.other_user = User.objects.create_user(username='other', password='pass')
        
        cls.rider = Rider.objects.create(user=cls.rider_user, phone='1234567890')
        cls.driver = Driver.objects.create(
            user=cls.driver_user,
            phone='0987654321',
            license_number='DL123',
            license_expiry=date.today() + timedelta(days=365),
            vehicle_make='Toyota',
            vehicle_model='Camry',
            vehicle_year=2020,
            vehicle_color='Black',
            vehicle_type='sedan',
            license_plate='ABC123'
        )
        cls.other_rider = Rider.objects.create(user=cls.other_user, phone='5555555555')
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.client = APIClient()
        
        self.completed_ride = Ride.objects.create(
            rider=self.rider,
            driver=self.driver,
            pickup_address='Pickup',
            pickup_lat=Decimal('28.7041'),
            pickup_lng=Decimal('77.1025'),
            dropoff_address='Dropoff',
            drop_lat=Decimal('28.5355'),
            drop_lng=Decimal('77.3910'),
            status=Ride.STATUS_COMPLETED,
            fare=Decimal('150.00')
        )
        
        self.rider_token = self._get_token(self.rider_user)
        self.driver_token = self._get_token(self.driver_user)
        self.other_token = self._get_token(self.other_user)
    
    def _get_token(self, user):
        """Helper to get JWT token."""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_mark_paid_success_as_rider(self):
        """Test rider can mark ride as paid."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.rider_token}')
        
        url = reverse('mark-ride-paid', kwargs={'ride_id': self.completed_ride.id})
        data = {
            'payment_method': 'CASH',
            'payment_status': 'PAID'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'PAID')
        self.assertEqual(response.data['method'], 'CASH')
        self.assertIn('message', response.data)
    
    def test_mark_paid_success_as_driver(self):
        """Test driver can mark ride as paid."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.driver_token}')
        
        url = reverse('mark-ride-paid', kwargs={'ride_id': self.completed_ride.id})
        data = {
            'payment_method': 'UPI',
            'payment_status': 'PAID'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['method'], 'UPI')
    
    def test_mark_paid_unauthorized_user(self):
        """Test that unauthorized users cannot mark payment."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.other_token}')
        
        url = reverse('mark-ride-paid', kwargs={'ride_id': self.completed_ride.id})
        data = {
            'payment_method': 'CASH',
            'payment_status': 'PAID'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_mark_paid_no_authentication(self):
        """Test that authentication is required."""
        url = reverse('mark-ride-paid', kwargs={'ride_id': self.completed_ride.id})
        data = {
            'payment_method': 'CASH',
            'payment_status': 'PAID'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_mark_paid_nonexistent_ride(self):
        """Test error for nonexistent ride."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.rider_token}')
        
        url = reverse('mark-ride-paid', kwargs={'ride_id': 99999})
        data = {
            'payment_method': 'CASH',
            'payment_status': 'PAID'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_mark_paid_validation_errors(self):
        """Test validation errors are returned properly."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.rider_token}')
        
        url = reverse('mark-ride-paid', kwargs={'ride_id': self.completed_ride.id})
        # Missing payment_method
        data = {
            'payment_status': 'PAID'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# Run tests with: python manage.py test orders.tests.test_ride_fare_payment
