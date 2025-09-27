"""
Comprehensive test suite for Rider and Driver models.

Tests all functionality including model creation, validation, relationships,
and edge cases for the ride-sharing application models.
"""

import unittest
from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.db import IntegrityError
from orders.models import Rider, Driver


class TestRiderModel(TestCase):
    """Test cases for the Rider model."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='testrider',
            email='rider@test.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
    
    def test_rider_creation_valid(self):
        """Test creating a valid rider."""
        rider = Rider.objects.create(
            user=self.user,
            phone='+1234567890',
            preferred_payment=Rider.PAYMENT_CARD,
            default_pickup_address='123 Main St, City',
            default_pickup_latitude=Decimal('40.7128'),
            default_pickup_longitude=Decimal('-74.0060')
        )
        
        self.assertEqual(rider.user, self.user)
        self.assertEqual(rider.phone, '+1234567890')
        self.assertEqual(rider.preferred_payment, Rider.PAYMENT_CARD)
        self.assertEqual(rider.average_rating, Decimal('5.00'))
        self.assertEqual(rider.total_rides, 0)
        self.assertTrue(rider.is_active)
        self.assertIsNotNone(rider.created_at)
        self.assertIsNotNone(rider.updated_at)
    
    def test_rider_str_representation(self):
        """Test string representation of rider."""
        rider = Rider.objects.create(
            user=self.user,
            phone='+1234567890'
        )
        expected = f"Rider: {self.user.get_full_name()} (+1234567890)"
        self.assertEqual(str(rider), expected)
    
    def test_rider_phone_validation_invalid_format(self):
        """Test phone number validation with invalid format."""
        with self.assertRaises(ValidationError):
            rider = Rider(
                user=self.user,
                phone='invalid-phone',
                preferred_payment=Rider.PAYMENT_CARD
            )
            rider.full_clean()
    
    def test_rider_phone_validation_empty(self):
        """Test phone number validation when empty."""
        with self.assertRaises(ValidationError) as context:
            rider = Rider(
                user=self.user,
                phone='',
                preferred_payment=Rider.PAYMENT_CARD
            )
            rider.full_clean()
        
        self.assertIn('Phone number is required', str(context.exception))
    
    def test_rider_coordinates_validation_partial(self):
        """Test coordinate validation when only one coordinate is provided."""
        with self.assertRaises(ValidationError) as context:
            rider = Rider(
                user=self.user,
                phone='+1234567890',
                default_pickup_latitude=Decimal('40.7128')
                # Missing longitude
            )
            rider.full_clean()
        
        self.assertIn('Both latitude and longitude must be provided together', str(context.exception))
    
    def test_rider_coordinates_validation_zero_zero(self):
        """Test coordinate validation for (0,0) coordinates."""
        with self.assertRaises(ValidationError) as context:
            rider = Rider(
                user=self.user,
                phone='+1234567890',
                default_pickup_latitude=Decimal('0.0'),
                default_pickup_longitude=Decimal('0.0')
            )
            rider.full_clean()
        
        self.assertIn('Coordinates cannot be (0,0)', str(context.exception))
    
    def test_rider_coordinates_validation_out_of_bounds(self):
        """Test coordinate validation for out-of-bounds values."""
        # Test latitude too high
        with self.assertRaises(ValidationError):
            rider = Rider(
                user=self.user,
                phone='+1234567890',
                default_pickup_latitude=Decimal('91.0'),
                default_pickup_longitude=Decimal('-74.0060')
            )
            rider.full_clean()
        
        # Test longitude too low
        with self.assertRaises(ValidationError):
            rider = Rider(
                user=self.user,
                phone='+1234567890',
                default_pickup_latitude=Decimal('40.7128'),
                default_pickup_longitude=Decimal('-181.0')
            )
            rider.full_clean()
    
    def test_rider_rating_validation(self):
        """Test rating validation for negative and excessive values."""
        # Test negative rating
        with self.assertRaises(ValidationError):
            rider = Rider(
                user=self.user,
                phone='+1234567890',
                average_rating=Decimal('-1.0')
            )
            rider.full_clean()
        
        # Test rating too high
        with self.assertRaises(ValidationError):
            rider = Rider(
                user=self.user,
                phone='+1234567890',
                average_rating=Decimal('6.0')
            )
            rider.full_clean()
    
    def test_rider_onetoone_relationship(self):
        """Test OneToOne relationship constraint."""
        # Create first rider
        Rider.objects.create(
            user=self.user,
            phone='+1234567890'
        )
        
        # Try to create second rider with same user should fail
        # Our validation catches this before database constraint
        with self.assertRaises(ValidationError):
            Rider.objects.create(
                user=self.user,
                phone='+0987654321'
            )


class TestDriverModel(TestCase):
    """Test cases for the Driver model."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username='testdriver',
            email='driver@test.com',
            password='testpass123',
            first_name='Jane',
            last_name='Smith'
        )
        
        # Future date for license expiry
        self.future_date = date.today() + timedelta(days=365)
    
    def test_driver_creation_valid(self):
        """Test creating a valid driver."""
        driver = Driver.objects.create(
            user=self.user,
            phone='+1234567890',
            license_number='DL123456789',
            license_expiry=self.future_date,
            vehicle_make='Toyota',
            vehicle_model='Camry',
            vehicle_year=2020,
            vehicle_color='Silver',
            vehicle_type=Driver.VEHICLE_SEDAN,
            license_plate='ABC123'
        )
        
        self.assertEqual(driver.user, self.user)
        self.assertEqual(driver.phone, '+1234567890')
        self.assertEqual(driver.license_number, 'DL123456789')
        self.assertEqual(driver.vehicle_make, 'Toyota')
        self.assertEqual(driver.average_rating, Decimal('5.00'))
        self.assertEqual(driver.total_rides, 0)
        self.assertTrue(driver.is_active)
        self.assertFalse(driver.is_verified)
        self.assertEqual(driver.availability_status, Driver.STATUS_OFFLINE)
    
    def test_driver_str_representation(self):
        """Test string representation of driver."""
        driver = Driver.objects.create(
            user=self.user,
            phone='+1234567890',
            license_number='DL123456789',
            license_expiry=self.future_date,
            vehicle_make='Toyota',
            vehicle_model='Camry',
            vehicle_year=2020,
            vehicle_color='Silver',
            license_plate='ABC123'
        )
        expected = f"Driver: {self.user.get_full_name()} (2020 Toyota Camry)"
        self.assertEqual(str(driver), expected)
    
    def test_driver_full_vehicle_name_property(self):
        """Test full_vehicle_name property."""
        driver = Driver.objects.create(
            user=self.user,
            phone='+1234567890',
            license_number='DL123456789',
            license_expiry=self.future_date,
            vehicle_make='Honda',
            vehicle_model='Civic',
            vehicle_year=2022,
            vehicle_color='Blue',
            license_plate='XYZ789'
        )
        self.assertEqual(driver.full_vehicle_name, '2022 Honda Civic')
    
    def test_driver_is_available_for_rides_property(self):
        """Test is_available_for_rides property."""
        driver = Driver.objects.create(
            user=self.user,
            phone='+1234567890',
            license_number='DL123456789',
            license_expiry=self.future_date,
            vehicle_make='Toyota',
            vehicle_model='Camry',
            vehicle_year=2020,
            vehicle_color='Silver',
            license_plate='ABC123'
        )
        
        # Initially not available (not verified, offline)
        self.assertFalse(driver.is_available_for_rides)
        
        # Set verified and available
        driver.is_verified = True
        driver.availability_status = Driver.STATUS_AVAILABLE
        self.assertTrue(driver.is_available_for_rides)
        
        # Set inactive
        driver.is_active = False
        self.assertFalse(driver.is_available_for_rides)
    
    def test_driver_required_fields_validation(self):
        """Test validation for required fields."""
        required_fields = [
            ('phone', ''),
            ('license_number', ''),
            ('vehicle_make', ''),
            ('vehicle_model', ''),
            ('vehicle_color', ''),
            ('license_plate', '')
        ]
        
        for field_name, invalid_value in required_fields:
            with self.subTest(field=field_name):
                kwargs = {
                    'user': self.user,
                    'phone': '+1234567890',
                    'license_number': 'DL123456789',
                    'license_expiry': self.future_date,
                    'vehicle_make': 'Toyota',
                    'vehicle_model': 'Camry',
                    'vehicle_year': 2020,
                    'vehicle_color': 'Silver',
                    'license_plate': 'ABC123'
                }
                kwargs[field_name] = invalid_value
                
                with self.assertRaises(ValidationError):
                    driver = Driver(**kwargs)
                    driver.full_clean()
    
    def test_driver_phone_validation(self):
        """Test phone number validation."""
        with self.assertRaises(ValidationError):
            driver = Driver(
                user=self.user,
                phone='invalid-phone',
                license_number='DL123456789',
                license_expiry=self.future_date,
                vehicle_make='Toyota',
                vehicle_model='Camry',
                vehicle_year=2020,
                vehicle_color='Silver',
                license_plate='ABC123'
            )
            driver.full_clean()
    
    def test_driver_license_number_validation(self):
        """Test license number validation."""
        # Test invalid format (lowercase)
        with self.assertRaises(ValidationError):
            driver = Driver(
                user=self.user,
                phone='+1234567890',
                license_number='dl123456789',  # lowercase not allowed
                license_expiry=self.future_date,
                vehicle_make='Toyota',
                vehicle_model='Camry',
                vehicle_year=2020,
                vehicle_color='Silver',
                license_plate='ABC123'
            )
            driver.full_clean()
        
        # Test too short
        with self.assertRaises(ValidationError):
            driver = Driver(
                user=self.user,
                phone='+1234567890',
                license_number='A1',  # too short
                license_expiry=self.future_date,
                vehicle_make='Toyota',
                vehicle_model='Camry',
                vehicle_year=2020,
                vehicle_color='Silver',
                license_plate='ABC123'
            )
            driver.full_clean()
    
    def test_driver_license_expiry_validation(self):
        """Test license expiry date validation."""
        past_date = date.today() - timedelta(days=1)
        
        with self.assertRaises(ValidationError) as context:
            driver = Driver(
                user=self.user,
                phone='+1234567890',
                license_number='DL123456789',
                license_expiry=past_date,
                vehicle_make='Toyota',
                vehicle_model='Camry',
                vehicle_year=2020,
                vehicle_color='Silver',
                license_plate='ABC123'
            )
            driver.full_clean()
        
        self.assertIn('License expiry date must be in the future', str(context.exception))
    
    def test_driver_vehicle_year_validation(self):
        """Test vehicle year validation."""
        # Test year too old
        with self.assertRaises(ValidationError):
            driver = Driver(
                user=self.user,
                phone='+1234567890',
                license_number='DL123456789',
                license_expiry=self.future_date,
                vehicle_make='Toyota',
                vehicle_model='Camry',
                vehicle_year=1979,  # too old
                vehicle_color='Silver',
                license_plate='ABC123'
            )
            driver.full_clean()
        
        # Test future year
        from django.utils import timezone
        future_year = timezone.now().year + 2
        with self.assertRaises(ValidationError):
            driver = Driver(
                user=self.user,
                phone='+1234567890',
                license_number='DL123456789',
                license_expiry=self.future_date,
                vehicle_make='Toyota',
                vehicle_model='Camry',
                vehicle_year=future_year,
                vehicle_color='Silver',
                license_plate='ABC123'
            )
            driver.full_clean()
    
    def test_driver_license_plate_validation(self):
        """Test license plate validation."""
        # Test invalid format (lowercase)
        with self.assertRaises(ValidationError):
            driver = Driver(
                user=self.user,
                phone='+1234567890',
                license_number='DL123456789',
                license_expiry=self.future_date,
                vehicle_make='Toyota',
                vehicle_model='Camry',
                vehicle_year=2020,
                vehicle_color='Silver',
                license_plate='abc123'  # lowercase not allowed
            )
            driver.full_clean()
    
    def test_driver_coordinates_validation(self):
        """Test current location coordinate validation."""
        # Test partial coordinates
        with self.assertRaises(ValidationError):
            driver = Driver(
                user=self.user,
                phone='+1234567890',
                license_number='DL123456789',
                license_expiry=self.future_date,
                vehicle_make='Toyota',
                vehicle_model='Camry',
                vehicle_year=2020,
                vehicle_color='Silver',
                license_plate='ABC123',
                current_latitude=Decimal('40.7128')
                # Missing longitude
            )
            driver.full_clean()
        
        # Test (0,0) coordinates
        with self.assertRaises(ValidationError):
            driver = Driver(
                user=self.user,
                phone='+1234567890',
                license_number='DL123456789',
                license_expiry=self.future_date,
                vehicle_make='Toyota',
                vehicle_model='Camry',
                vehicle_year=2020,
                vehicle_color='Silver',
                license_plate='ABC123',
                current_latitude=Decimal('0.0'),
                current_longitude=Decimal('0.0')
            )
            driver.full_clean()
    
    def test_driver_unique_constraints(self):
        """Test unique constraints for license_number and license_plate."""
        # Create first driver
        Driver.objects.create(
            user=self.user,
            phone='+1234567890',
            license_number='DL123456789',
            license_expiry=self.future_date,
            vehicle_make='Toyota',
            vehicle_model='Camry',
            vehicle_year=2020,
            vehicle_color='Silver',
            license_plate='ABC123'
        )
        
        # Create second user
        user2 = User.objects.create_user(
            username='testdriver2',
            email='driver2@test.com',
            password='testpass123'
        )
        
        # Test duplicate license number
        # Our validation catches this before database constraint
        with self.assertRaises(ValidationError):
            Driver.objects.create(
                user=user2,
                phone='+0987654321',
                license_number='DL123456789',  # duplicate
                license_expiry=self.future_date,
                vehicle_make='Honda',
                vehicle_model='Civic',
                vehicle_year=2021,
                vehicle_color='Blue',
                license_plate='XYZ789'
            )
        
        # Test duplicate license plate
        # Our validation catches this before database constraint
        with self.assertRaises(ValidationError):
            Driver.objects.create(
                user=user2,
                phone='+0987654321',
                license_number='DL987654321',
                license_expiry=self.future_date,
                vehicle_make='Honda',
                vehicle_model='Civic',
                vehicle_year=2021,
                vehicle_color='Blue',
                license_plate='ABC123'  # duplicate
            )


class TestModelIntegration(TestCase):
    """Test integration between models and Django User."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.rider_user = User.objects.create_user(
            username='testrider',
            email='rider@test.com',
            password='testpass123'
        )
        
        self.driver_user = User.objects.create_user(
            username='testdriver',
            email='driver@test.com',
            password='testpass123'
        )
    
    def test_user_can_have_both_profiles(self):
        """Test that theoretically we could extend to allow both profiles."""
        # This tests the relationship setup is correct
        rider = Rider.objects.create(
            user=self.rider_user,
            phone='+1234567890'
        )
        
        driver = Driver.objects.create(
            user=self.driver_user,
            phone='+0987654321',
            license_number='DL123456789',
            license_expiry=date.today() + timedelta(days=365),
            vehicle_make='Toyota',
            vehicle_model='Camry',
            vehicle_year=2020,
            vehicle_color='Silver',
            license_plate='ABC123'
        )
        
        # Test reverse relationships
        self.assertEqual(self.rider_user.rider_profile, rider)
        self.assertEqual(self.driver_user.driver_profile, driver)
    
    def test_cascade_deletion(self):
        """Test that profiles are deleted when user is deleted."""
        rider = Rider.objects.create(
            user=self.rider_user,
            phone='+1234567890'
        )
        
        rider_id = rider.id
        
        # Delete user
        self.rider_user.delete()
        
        # Rider should be deleted too
        with self.assertRaises(Rider.DoesNotExist):
            Rider.objects.get(id=rider_id)


if __name__ == '__main__':
    unittest.main()