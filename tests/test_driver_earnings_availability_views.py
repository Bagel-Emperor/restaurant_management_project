"""
Integration test suite for Driver Earnings and Availability API views.

Tests cover:
- Task 12B: DriverEarningsSummaryView
  - GET /api/driver/earnings/
  - Authentication and permission checks
  - Response format and data accuracy

- Task 13B: DriverAvailabilityToggleView
  - POST /api/driver/availability/
  - Authentication and permission checks
  - Availability status updates
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status as http_status
from datetime import timedelta
from decimal import Decimal
from orders.models import Driver, Rider, Ride


class DriverEarningsSummaryViewTestCase(TestCase):
    """Integration tests for DriverEarningsSummaryView (Task 12B)."""
    
    def setUp(self):
        """Set up test data and API client."""
        self.client = APIClient()
        
        # Create driver user and authenticate
        self.driver_user = User.objects.create_user(
            username='testdriver',
            password='testpass123'
        )
        
        self.driver = Driver.objects.create(
            user=self.driver_user,
            phone='+1234567890',
            license_number='ABC12345',
            license_expiry=timezone.now().date() + timedelta(days=365),
            vehicle_make='Toyota',
            vehicle_model='Camry',
            vehicle_year=2020,
            vehicle_color='Blue',
            license_plate='XYZ123',
            availability_status=Driver.STATUS_AVAILABLE
        )
        
        # Create rider
        self.rider_user = User.objects.create_user(
            username='testrider',
            password='testpass123'
        )
        
        self.rider = Rider.objects.create(
            user=self.rider_user,
            phone='+1987654321'
        )
        
        # Create non-driver user
        self.regular_user = User.objects.create_user(
            username='regularuser',
            password='testpass123'
        )
    
    def create_ride(self, days_ago=0, fare='100.00', payment_method='CASH',
                    status='COMPLETED', payment_status='PAID'):
        """Helper to create a ride."""
        completed_time = timezone.now() - timedelta(days=days_ago)
        
        ride = Ride.objects.create(
            rider=self.rider,
            driver=self.driver,
            pickup_address='123 Start St',
            pickup_lat=Decimal('40.7128'),
            pickup_lng=Decimal('-74.0060'),
            dropoff_address='456 End Ave',
            drop_lat=Decimal('40.7589'),
            drop_lng=Decimal('-73.9851'),
            status=status,
            fare=Decimal(fare),
            payment_method=payment_method,
            payment_status=payment_status,
            completed_at=completed_time if status == 'COMPLETED' else None
        )
        return ride
    
    def test_get_earnings_unauthenticated(self):
        """Test that unauthenticated requests are rejected."""
        response = self.client.get('/PerpexBistro/orders/driver/earnings/')
        
        self.assertEqual(response.status_code, http_status.HTTP_401_UNAUTHORIZED)
    
    def test_get_earnings_non_driver_user(self):
        """Test that non-driver users are rejected."""
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.get('/PerpexBistro/orders/driver/earnings/')
        
        self.assertEqual(response.status_code, http_status.HTTP_403_FORBIDDEN)
        self.assertIn('NO_DRIVER_PROFILE', response.data['error_code'])
    
    def test_get_earnings_no_rides(self):
        """Test earnings endpoint when driver has no rides."""
        self.client.force_authenticate(user=self.driver_user)
        
        response = self.client.get('/PerpexBistro/orders/driver/earnings/')
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data['total_rides'], 0)
        self.assertEqual(Decimal(response.data['total_earnings']), Decimal('0.00'))
        self.assertEqual(response.data['payment_breakdown']['CASH'], 0)
        self.assertEqual(response.data['payment_breakdown']['UPI'], 0)
        self.assertEqual(response.data['payment_breakdown']['CARD'], 0)
        self.assertEqual(Decimal(response.data['average_fare']), Decimal('0.00'))
    
    def test_get_earnings_with_rides(self):
        """Test earnings endpoint with multiple rides."""
        self.client.force_authenticate(user=self.driver_user)
        
        # Create rides with different payment methods
        self.create_ride(days_ago=1, fare='100.00', payment_method='CASH')
        self.create_ride(days_ago=2, fare='150.00', payment_method='UPI')
        self.create_ride(days_ago=3, fare='200.00', payment_method='CARD')
        
        response = self.client.get('/PerpexBistro/orders/driver/earnings/')
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data['total_rides'], 3)
        self.assertEqual(Decimal(response.data['total_earnings']), Decimal('450.00'))
        self.assertEqual(response.data['payment_breakdown']['CASH'], 1)
        self.assertEqual(response.data['payment_breakdown']['UPI'], 1)
        self.assertEqual(response.data['payment_breakdown']['CARD'], 1)
        self.assertEqual(Decimal(response.data['average_fare']), Decimal('150.00'))
    
    def test_get_earnings_filters_unpaid_rides(self):
        """Test that unpaid rides are excluded from earnings."""
        self.client.force_authenticate(user=self.driver_user)
        
        self.create_ride(days_ago=1, fare='100.00', payment_status='PAID')
        self.create_ride(days_ago=2, fare='200.00', payment_status='UNPAID')
        
        response = self.client.get('/PerpexBistro/orders/driver/earnings/')
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data['total_rides'], 1)
        self.assertEqual(Decimal(response.data['total_earnings']), Decimal('100.00'))
    
    def test_get_earnings_filters_incomplete_rides(self):
        """Test that incomplete rides are excluded from earnings."""
        self.client.force_authenticate(user=self.driver_user)
        
        self.create_ride(days_ago=1, fare='100.00', status='COMPLETED')
        self.create_ride(days_ago=2, fare='200.00', status='REQUESTED')
        self.create_ride(days_ago=3, fare='300.00', status='CANCELLED')
        
        response = self.client.get('/PerpexBistro/orders/driver/earnings/')
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data['total_rides'], 1)
        self.assertEqual(Decimal(response.data['total_earnings']), Decimal('100.00'))
    
    def test_get_earnings_time_window(self):
        """Test that only last 7 days rides are included."""
        self.client.force_authenticate(user=self.driver_user)
        
        # Recent rides
        self.create_ride(days_ago=1, fare='100.00')
        self.create_ride(days_ago=6, fare='150.00')
        
        # Old rides (should be excluded)
        self.create_ride(days_ago=8, fare='200.00')
        self.create_ride(days_ago=30, fare='300.00')
        
        response = self.client.get('/PerpexBistro/orders/driver/earnings/')
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertEqual(response.data['total_rides'], 2)
        self.assertEqual(Decimal(response.data['total_earnings']), Decimal('250.00'))


class DriverAvailabilityToggleViewTestCase(TestCase):
    """Integration tests for DriverAvailabilityToggleView (Task 13B)."""
    
    def setUp(self):
        """Set up test data and API client."""
        self.client = APIClient()
        
        # Create driver user
        self.driver_user = User.objects.create_user(
            username='testdriver',
            password='testpass123'
        )
        
        self.driver = Driver.objects.create(
            user=self.driver_user,
            phone='+1234567890',
            license_number='ABC12345',
            license_expiry=timezone.now().date() + timedelta(days=365),
            vehicle_make='Toyota',
            vehicle_model='Camry',
            vehicle_year=2020,
            vehicle_color='Blue',
            license_plate='XYZ123',
            availability_status=Driver.STATUS_OFFLINE
        )
        
        # Create non-driver user
        self.regular_user = User.objects.create_user(
            username='regularuser',
            password='testpass123'
        )
    
    def test_toggle_availability_unauthenticated(self):
        """Test that unauthenticated requests are rejected."""
        response = self.client.post('/PerpexBistro/orders/driver/availability/', {'is_available': True})
        
        self.assertEqual(response.status_code, http_status.HTTP_401_UNAUTHORIZED)
    
    def test_toggle_availability_non_driver_user(self):
        """Test that non-driver users are rejected."""
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.post('/PerpexBistro/orders/driver/availability/', {'is_available': True})
        
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn('driver profile', str(response.data))
    
    def test_toggle_availability_missing_field(self):
        """Test that missing is_available field returns validation error."""
        self.client.force_authenticate(user=self.driver_user)
        
        response = self.client.post('/PerpexBistro/orders/driver/availability/', {}, format='json')
        
        self.assertEqual(
            response.status_code, 
            http_status.HTTP_400_BAD_REQUEST,
            f"Expected 400, got {response.status_code}. Response data: {response.data}"
        )
        self.assertIn('is_available', response.data)
    
    def test_toggle_availability_to_available(self):
        """Test toggling availability from offline to available."""
        self.client.force_authenticate(user=self.driver_user)
        
        # Driver starts offline
        self.assertEqual(self.driver.availability_status, Driver.STATUS_OFFLINE)
        
        response = self.client.post('/PerpexBistro/orders/driver/availability/', {'is_available': True})
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertTrue(response.data['is_available'])
        self.assertEqual(response.data['availability_status'], 'available')
        
        # Verify database was updated
        self.driver.refresh_from_db()
        self.assertEqual(self.driver.availability_status, Driver.STATUS_AVAILABLE)
    
    def test_toggle_availability_to_offline(self):
        """Test toggling availability from available to offline."""
        self.client.force_authenticate(user=self.driver_user)
        
        # Set driver to available first
        self.driver.availability_status = Driver.STATUS_AVAILABLE
        self.driver.save()
        
        response = self.client.post('/PerpexBistro/orders/driver/availability/', {'is_available': False})
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertFalse(response.data['is_available'])
        self.assertEqual(response.data['availability_status'], 'offline')
        
        # Verify database was updated
        self.driver.refresh_from_db()
        self.assertEqual(self.driver.availability_status, Driver.STATUS_OFFLINE)
    
    def test_toggle_availability_multiple_times(self):
        """Test multiple availability toggles in sequence."""
        self.client.force_authenticate(user=self.driver_user)
        
        # Go online
        response = self.client.post('/PerpexBistro/orders/driver/availability/', {'is_available': True})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertTrue(response.data['is_available'])
        
        # Go offline
        response = self.client.post('/PerpexBistro/orders/driver/availability/', {'is_available': False})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertFalse(response.data['is_available'])
        
        # Go online again
        response = self.client.post('/PerpexBistro/orders/driver/availability/', {'is_available': True})
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertTrue(response.data['is_available'])
        
        # Final state should be available
        self.driver.refresh_from_db()
        self.assertEqual(self.driver.availability_status, Driver.STATUS_AVAILABLE)
    
    def test_toggle_availability_invalid_value(self):
        """Test that invalid boolean values are rejected."""
        self.client.force_authenticate(user=self.driver_user)
        
        response = self.client.post('/PerpexBistro/orders/driver/availability/', {'is_available': 'maybe'})
        
        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertIn('is_available', response.data)
    
    def test_toggle_availability_response_format(self):
        """Test that response contains both fields with correct types."""
        self.client.force_authenticate(user=self.driver_user)
        
        response = self.client.post('/PerpexBistro/orders/driver/availability/', {'is_available': True})
        
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
        self.assertIn('is_available', response.data)
        self.assertIn('availability_status', response.data)
        self.assertIsInstance(response.data['is_available'], bool)
        self.assertIsInstance(response.data['availability_status'], str)
