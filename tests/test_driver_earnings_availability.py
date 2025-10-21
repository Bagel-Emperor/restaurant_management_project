"""
Comprehensive test suite for Driver Earnings and Availability serializers.

Tests cover:
- Task 12A: DriverEarningsSerializer
  - Earnings calculation over 7 days
  - Payment method breakdown
  - Average fare calculation
  - Edge cases (no rides, different statuses)

- Task 13A: DriverAvailabilitySerializer
  - Toggling availability on/off
  - Validation for non-driver users
  - Authentication requirements
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from orders.models import Driver, Rider, Ride
from orders.serializers import DriverEarningsSerializer, DriverAvailabilitySerializer


class DriverEarningsSerializerTestCase(TestCase):
    """Test cases for DriverEarningsSerializer (Task 12A)."""
    
    def setUp(self):
        """Set up test data."""
        # Create users
        self.driver_user = User.objects.create_user(
            username='testdriver',
            password='testpass123'
        )
        self.rider_user = User.objects.create_user(
            username='testrider',
            password='testpass123'
        )
        
        # Create driver
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
        self.rider = Rider.objects.create(
            user=self.rider_user,
            phone='+1987654321'
        )
    
    def create_ride(self, days_ago=0, fare='100.00', payment_method='CASH', 
                    status='COMPLETED', payment_status='PAID'):
        """Helper to create a ride with specific parameters."""
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
    
    def test_earnings_no_rides(self):
        """Test earnings serializer when driver has no rides."""
        serializer = DriverEarningsSerializer(self.driver)
        data = serializer.data
        
        self.assertEqual(data['total_rides'], 0)
        self.assertEqual(Decimal(data['total_earnings']), Decimal('0.00'))
        self.assertEqual(data['payment_breakdown']['CASH'], 0)
        self.assertEqual(data['payment_breakdown']['UPI'], 0)
        self.assertEqual(data['payment_breakdown']['CARD'], 0)
        self.assertEqual(Decimal(data['average_fare']), Decimal('0.00'))
    
    def test_earnings_single_ride(self):
        """Test earnings with a single completed ride."""
        self.create_ride(days_ago=1, fare='250.50', payment_method='CASH')
        
        serializer = DriverEarningsSerializer(self.driver)
        data = serializer.data
        
        self.assertEqual(data['total_rides'], 1)
        self.assertEqual(Decimal(data['total_earnings']), Decimal('250.50'))
        self.assertEqual(data['payment_breakdown']['CASH'], 1)
        self.assertEqual(data['payment_breakdown']['UPI'], 0)
        self.assertEqual(data['payment_breakdown']['CARD'], 0)
        self.assertEqual(Decimal(data['average_fare']), Decimal('250.50'))
    
    def test_earnings_multiple_rides_different_payment_methods(self):
        """Test earnings with multiple rides using different payment methods."""
        # Create rides with different payment methods
        self.create_ride(days_ago=1, fare='100.00', payment_method='CASH')
        self.create_ride(days_ago=2, fare='150.00', payment_method='UPI')
        self.create_ride(days_ago=3, fare='200.00', payment_method='CARD')
        self.create_ride(days_ago=4, fare='120.00', payment_method='CASH')
        self.create_ride(days_ago=5, fare='180.00', payment_method='UPI')
        
        serializer = DriverEarningsSerializer(self.driver)
        data = serializer.data
        
        self.assertEqual(data['total_rides'], 5)
        self.assertEqual(Decimal(data['total_earnings']), Decimal('750.00'))
        self.assertEqual(data['payment_breakdown']['CASH'], 2)
        self.assertEqual(data['payment_breakdown']['UPI'], 2)
        self.assertEqual(data['payment_breakdown']['CARD'], 1)
        # Average: 750 / 5 = 150.00
        self.assertEqual(Decimal(data['average_fare']), Decimal('150.00'))
    
    def test_earnings_only_counts_completed_rides(self):
        """Test that only COMPLETED rides are included in earnings."""
        self.create_ride(days_ago=1, fare='100.00', status='COMPLETED')
        self.create_ride(days_ago=2, fare='200.00', status='REQUESTED')
        self.create_ride(days_ago=3, fare='300.00', status='CANCELLED')
        
        serializer = DriverEarningsSerializer(self.driver)
        data = serializer.data
        
        # Only 1 completed ride should count
        self.assertEqual(data['total_rides'], 1)
        self.assertEqual(Decimal(data['total_earnings']), Decimal('100.00'))
    
    def test_earnings_only_counts_paid_rides(self):
        """Test that only PAID rides are included in earnings."""
        self.create_ride(days_ago=1, fare='100.00', payment_status='PAID')
        self.create_ride(days_ago=2, fare='200.00', payment_status='UNPAID')
        
        serializer = DriverEarningsSerializer(self.driver)
        data = serializer.data
        
        # Only 1 paid ride should count
        self.assertEqual(data['total_rides'], 1)
        self.assertEqual(Decimal(data['total_earnings']), Decimal('100.00'))
    
    def test_earnings_only_last_7_days(self):
        """Test that only rides from last 7 days are included."""
        # Recent rides (within 7 days)
        self.create_ride(days_ago=1, fare='100.00')
        self.create_ride(days_ago=6, fare='150.00')
        
        # Old rides (more than 7 days ago)
        self.create_ride(days_ago=8, fare='200.00')
        self.create_ride(days_ago=30, fare='300.00')
        
        serializer = DriverEarningsSerializer(self.driver)
        data = serializer.data
        
        # Only 2 recent rides should count
        self.assertEqual(data['total_rides'], 2)
        self.assertEqual(Decimal(data['total_earnings']), Decimal('250.00'))
    
    def test_earnings_average_fare_rounding(self):
        """Test that average fare is properly rounded to 2 decimal places."""
        # Create rides with fares that will result in repeating decimals
        self.create_ride(days_ago=1, fare='100.00')
        self.create_ride(days_ago=2, fare='100.00')
        self.create_ride(days_ago=3, fare='100.00')
        # Total: 300, Count: 3, Average: 100.00 (exact)
        
        serializer = DriverEarningsSerializer(self.driver)
        data = serializer.data
        
        self.assertEqual(Decimal(data['average_fare']), Decimal('100.00'))
        
        # Test with non-exact division
        self.create_ride(days_ago=4, fare='50.00')
        # Total: 350, Count: 4, Average: 87.50
        
        serializer = DriverEarningsSerializer(self.driver)
        data = serializer.data
        
        self.assertEqual(Decimal(data['average_fare']), Decimal('87.50'))
    
    def test_earnings_realistic_scenario(self):
        """Test earnings with a realistic scenario matching task example."""
        # Create 18 rides total with mixed payment methods
        # 8 CASH, 6 UPI, 4 CARD
        for i in range(8):
            self.create_ride(days_ago=i % 7, fare='250.00', payment_method='CASH')
        for i in range(6):
            self.create_ride(days_ago=i % 7, fare='275.00', payment_method='UPI')
        for i in range(4):
            self.create_ride(days_ago=i % 7, fare='300.00', payment_method='CARD')
        
        serializer = DriverEarningsSerializer(self.driver)
        data = serializer.data
        
        self.assertEqual(data['total_rides'], 18)
        # Total: (8 * 250) + (6 * 275) + (4 * 300) = 2000 + 1650 + 1200 = 4850
        self.assertEqual(Decimal(data['total_earnings']), Decimal('4850.00'))
        self.assertEqual(data['payment_breakdown']['CASH'], 8)
        self.assertEqual(data['payment_breakdown']['UPI'], 6)
        self.assertEqual(data['payment_breakdown']['CARD'], 4)
        # Average: 4850 / 18 = 269.44 (rounded)
        self.assertEqual(Decimal(data['average_fare']), Decimal('269.44'))


class DriverAvailabilitySerializerTestCase(TestCase):
    """Test cases for DriverAvailabilitySerializer (Task 13A)."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        
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
    
    def test_toggle_availability_to_available(self):
        """Test toggling driver availability from offline to available."""
        request = self.factory.post('/api/driver/availability/')
        request.user = self.driver_user
        
        serializer = DriverAvailabilitySerializer(
            data={'is_available': True},
            context={'request': request}
        )
        
        self.assertTrue(serializer.is_valid())
        driver = serializer.save()
        
        self.assertEqual(driver.availability_status, Driver.STATUS_AVAILABLE)
        
        # Check representation
        data = serializer.to_representation(driver)
        self.assertTrue(data['is_available'])
        self.assertEqual(data['availability_status'], 'available')
    
    def test_toggle_availability_to_offline(self):
        """Test toggling driver availability from available to offline."""
        # Set driver to available first
        self.driver.availability_status = Driver.STATUS_AVAILABLE
        self.driver.save()
        
        request = self.factory.post('/api/driver/availability/')
        request.user = self.driver_user
        
        serializer = DriverAvailabilitySerializer(
            data={'is_available': False},
            context={'request': request}
        )
        
        self.assertTrue(serializer.is_valid())
        driver = serializer.save()
        
        self.assertEqual(driver.availability_status, Driver.STATUS_OFFLINE)
        
        # Check representation
        data = serializer.to_representation(driver)
        self.assertFalse(data['is_available'])
        self.assertEqual(data['availability_status'], 'offline')
    
    def test_availability_requires_authentication(self):
        """Test that unauthenticated requests are rejected."""
        request = self.factory.post('/api/driver/availability/')
        request.user = None  # No authenticated user
        
        serializer = DriverAvailabilitySerializer(
            data={'is_available': True},
            context={'request': request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('Authentication required', str(serializer.errors))
    
    def test_availability_requires_driver_profile(self):
        """Test that only users with driver profiles can toggle availability."""
        request = self.factory.post('/api/driver/availability/')
        request.user = self.regular_user  # User without driver profile
        
        serializer = DriverAvailabilitySerializer(
            data={'is_available': True},
            context={'request': request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('driver profile', str(serializer.errors))
    
    def test_availability_is_available_required(self):
        """Test that is_available field is required."""
        request = self.factory.post('/api/driver/availability/')
        request.user = self.driver_user
        
        serializer = DriverAvailabilitySerializer(
            data={},  # Missing is_available
            context={'request': request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('is_available', serializer.errors)
    
    def test_availability_multiple_toggles(self):
        """Test multiple availability toggles in sequence."""
        request = self.factory.post('/api/driver/availability/')
        request.user = self.driver_user
        
        # Start offline, go online
        serializer = DriverAvailabilitySerializer(
            data={'is_available': True},
            context={'request': request}
        )
        self.assertTrue(serializer.is_valid())
        driver = serializer.save()
        self.assertEqual(driver.availability_status, Driver.STATUS_AVAILABLE)
        
        # Go offline
        serializer = DriverAvailabilitySerializer(
            data={'is_available': False},
            context={'request': request}
        )
        self.assertTrue(serializer.is_valid())
        driver = serializer.save()
        self.assertEqual(driver.availability_status, Driver.STATUS_OFFLINE)
        
        # Go online again
        serializer = DriverAvailabilitySerializer(
            data={'is_available': True},
            context={'request': request}
        )
        self.assertTrue(serializer.is_valid())
        driver = serializer.save()
        self.assertEqual(driver.availability_status, Driver.STATUS_AVAILABLE)
    
    def test_availability_representation_reflects_current_status(self):
        """Test that to_representation correctly reflects driver's current status."""
        # Test offline representation
        self.driver.availability_status = Driver.STATUS_OFFLINE
        self.driver.save()
        
        serializer = DriverAvailabilitySerializer()
        data = serializer.to_representation(self.driver)
        
        self.assertFalse(data['is_available'])
        self.assertEqual(data['availability_status'], 'offline')
        
        # Test available representation
        self.driver.availability_status = Driver.STATUS_AVAILABLE
        self.driver.save()
        
        data = serializer.to_representation(self.driver)
        
        self.assertTrue(data['is_available'])
        self.assertEqual(data['availability_status'], 'available')
