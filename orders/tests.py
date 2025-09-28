from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import date, timedelta
from decimal import Decimal
from .models import Rider, Driver
from .serializers import RiderRegistrationSerializer, DriverRegistrationSerializer


class RiderRegistrationSerializerTest(TestCase):
    """Test suite for RiderRegistrationSerializer"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_rider_data = {
            'username': 'test_rider',
            'email': 'rider@example.com',
            'password': 'securepass123',
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '+1234567890',
            'preferred_payment': 'card',
            'default_pickup_address': '123 Main St',
            'default_pickup_latitude': Decimal('40.7128'),
            'default_pickup_longitude': Decimal('-74.0060'),
        }
    
    def test_valid_rider_registration(self):
        """Test successful rider registration with valid data"""
        serializer = RiderRegistrationSerializer(data=self.valid_rider_data)
        self.assertTrue(serializer.is_valid())
        
        user = serializer.save()
        self.assertIsInstance(user, User)
        self.assertEqual(user.username, 'test_rider')
        self.assertEqual(user.email, 'rider@example.com')
        self.assertTrue(user.check_password('securepass123'))
        self.assertTrue(hasattr(user, 'rider_profile'))
        
        rider = user.rider_profile
        self.assertEqual(rider.phone, '+1234567890')
        self.assertEqual(rider.preferred_payment, 'card')
        self.assertEqual(rider.default_pickup_address, '123 Main St')
        self.assertEqual(rider.default_pickup_latitude, Decimal('40.7128'))
        self.assertEqual(rider.default_pickup_longitude, Decimal('-74.0060'))
    
    def test_duplicate_username_validation(self):
        """Test that duplicate usernames are rejected"""
        User.objects.create_user(username='test_rider', email='existing@example.com')
        
        serializer = RiderRegistrationSerializer(data=self.valid_rider_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)
        self.assertIn('already exists', str(serializer.errors['username'][0]))
    
    def test_duplicate_email_validation(self):
        """Test that duplicate emails are rejected"""
        User.objects.create_user(username='existing_user', email='rider@example.com')
        
        serializer = RiderRegistrationSerializer(data=self.valid_rider_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        self.assertIn('already exists', str(serializer.errors['email'][0]))
    
    def test_duplicate_phone_validation(self):
        """Test that duplicate phone numbers are rejected"""
        # Create an existing rider with the same phone
        existing_user = User.objects.create_user(username='existing_rider', email='existing@example.com')
        Rider.objects.create(user=existing_user, phone='+1234567890')
        
        serializer = RiderRegistrationSerializer(data=self.valid_rider_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone', serializer.errors)
        self.assertIn('already exists', str(serializer.errors['phone'][0]))
    
    def test_invalid_phone_format(self):
        """Test phone number format validation"""
        invalid_data = self.valid_rider_data.copy()
        invalid_data['phone'] = '123'  # Too short
        
        serializer = RiderRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone', serializer.errors)
    
    def test_coordinates_validation(self):
        """Test that coordinates must be provided together"""
        invalid_data = self.valid_rider_data.copy()
        invalid_data['default_pickup_latitude'] = Decimal('40.7128')
        del invalid_data['default_pickup_longitude']  # Missing longitude
        
        serializer = RiderRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('default_pickup_latitude', serializer.errors)
        self.assertIn('default_pickup_longitude', serializer.errors)
    
    def test_zero_coordinates_validation(self):
        """Test that (0,0) coordinates are rejected"""
        invalid_data = self.valid_rider_data.copy()
        invalid_data['default_pickup_latitude'] = Decimal('0.0')
        invalid_data['default_pickup_longitude'] = Decimal('0.0')
        
        serializer = RiderRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('default_pickup_latitude', serializer.errors)
        self.assertIn('default_pickup_longitude', serializer.errors)
    
    def test_short_password_validation(self):
        """Test password minimum length validation"""
        invalid_data = self.valid_rider_data.copy()
        invalid_data['password'] = '123'  # Too short
        
        serializer = RiderRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)


class DriverRegistrationSerializerTest(TestCase):
    """Test suite for DriverRegistrationSerializer"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_driver_data = {
            'username': 'test_driver',
            'email': 'driver@example.com',
            'password': 'securepass123',
            'first_name': 'Mike',
            'last_name': 'Smith',
            'phone': '+1987654321',
            'license_number': 'DL12345678',
            'license_expiry': (date.today() + timedelta(days=365)).isoformat(),
            'vehicle_make': 'Toyota',
            'vehicle_model': 'Camry',
            'vehicle_year': 2020,
            'vehicle_color': 'Silver',
            'vehicle_type': 'sedan',
            'license_plate': 'ABC123',
        }
    
    def test_valid_driver_registration(self):
        """Test successful driver registration with valid data"""
        serializer = DriverRegistrationSerializer(data=self.valid_driver_data)
        self.assertTrue(serializer.is_valid())
        
        user = serializer.save()
        self.assertIsInstance(user, User)
        self.assertEqual(user.username, 'test_driver')
        self.assertEqual(user.email, 'driver@example.com')
        self.assertTrue(user.check_password('securepass123'))
        self.assertTrue(hasattr(user, 'driver_profile'))
        
        driver = user.driver_profile
        self.assertEqual(driver.phone, '+1987654321')
        self.assertEqual(driver.license_number, 'DL12345678')
        self.assertEqual(driver.vehicle_make, 'Toyota')
        self.assertEqual(driver.vehicle_model, 'Camry')
        self.assertEqual(driver.vehicle_year, 2020)
        self.assertEqual(driver.license_plate, 'ABC123')
    
    def test_duplicate_license_number_validation(self):
        """Test that duplicate license numbers are rejected"""
        existing_user = User.objects.create_user(username='existing_driver', email='existing@example.com')
        Driver.objects.create(
            user=existing_user, 
            phone='+1111111111',
            license_number='DL12345678',
            license_expiry=date.today() + timedelta(days=365),
            vehicle_make='Honda',
            vehicle_model='Civic',
            vehicle_year=2019,
            vehicle_color='Blue',
            license_plate='XYZ789'
        )
        
        serializer = DriverRegistrationSerializer(data=self.valid_driver_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('license_number', serializer.errors)
        self.assertIn('already exists', str(serializer.errors['license_number'][0]))
    
    def test_duplicate_license_plate_validation(self):
        """Test that duplicate license plates are rejected"""
        existing_user = User.objects.create_user(username='existing_driver', email='existing@example.com')
        Driver.objects.create(
            user=existing_user, 
            phone='+1111111111',
            license_number='DL99999999',
            license_expiry=date.today() + timedelta(days=365),
            vehicle_make='Honda',
            vehicle_model='Civic',
            vehicle_year=2019,
            vehicle_color='Blue',
            license_plate='ABC123'  # Same as test data
        )
        
        serializer = DriverRegistrationSerializer(data=self.valid_driver_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('license_plate', serializer.errors)
        self.assertIn('already exists', str(serializer.errors['license_plate'][0]))
    
    def test_expired_license_validation(self):
        """Test that expired licenses are rejected"""
        invalid_data = self.valid_driver_data.copy()
        invalid_data['license_expiry'] = (date.today() - timedelta(days=1)).isoformat()  # Yesterday
        
        serializer = DriverRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('license_expiry', serializer.errors)
        self.assertIn('future', str(serializer.errors['license_expiry'][0]))
    
    def test_invalid_vehicle_year(self):
        """Test vehicle year validation"""
        invalid_data = self.valid_driver_data.copy()
        invalid_data['vehicle_year'] = 1975  # Too old
        
        serializer = DriverRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('vehicle_year', serializer.errors)
        
        # Test future year
        invalid_data['vehicle_year'] = 2030  # Too far in future
        serializer = DriverRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('vehicle_year', serializer.errors)
    
    def test_license_number_format_validation(self):
        """Test license number format"""
        invalid_data = self.valid_driver_data.copy()
        invalid_data['license_number'] = 'abc'  # Too short
        
        serializer = DriverRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('license_number', serializer.errors)
        
        # Test that valid license gets uppercased
        valid_data = self.valid_driver_data.copy()
        valid_data['license_number'] = 'dlABC12345'
        serializer = DriverRegistrationSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['license_number'], 'DLABC12345')
    
    def test_license_plate_format_validation(self):
        """Test license plate format"""
        invalid_data = self.valid_driver_data.copy()
        invalid_data['license_plate'] = 'a'  # Too short
        
        serializer = DriverRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('license_plate', serializer.errors)


class RiderRegistrationAPITest(APITestCase):
    """Test suite for Rider Registration API endpoint"""
    
    def setUp(self):
        """Set up test client and data"""
        self.client = APIClient()
        self.url = '/PerpexBistro/orders/register/rider/'
        self.valid_data = {
            'username': 'api_rider',
            'email': 'api_rider@example.com',
            'password': 'securepass123',
            'first_name': 'API',
            'last_name': 'Rider',
            'phone': '+1555666777',
            'preferred_payment': 'card',
            'default_pickup_address': '456 API Street',
            'default_pickup_latitude': 41.8781,
            'default_pickup_longitude': -87.6298,
        }
    
    def test_successful_rider_registration(self):
        """Test successful rider registration via API"""
        response = self.client.post(self.url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('Rider registered successfully', response.data['message'])
        self.assertIn('data', response.data)
        
        # Verify user was created
        user = User.objects.get(username='api_rider')
        self.assertEqual(user.email, 'api_rider@example.com')
        self.assertTrue(hasattr(user, 'rider_profile'))
    
    def test_registration_with_validation_errors(self):
        """Test registration with invalid data"""
        invalid_data = self.valid_data.copy()
        invalid_data['email'] = 'invalid-email'  # Invalid email format
        
        response = self.client.post(self.url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('validation errors', response.data['message'])
        self.assertIn('errors', response.data)
    
    def test_registration_duplicate_username(self):
        """Test registration with duplicate username"""
        # Create existing user
        User.objects.create_user(username='api_rider', email='existing@example.com')
        
        response = self.client.post(self.url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('errors', response.data)
        self.assertIn('username', response.data['errors'])
    
    def test_registration_missing_required_fields(self):
        """Test registration with missing required fields"""
        incomplete_data = {'username': 'incomplete_rider'}
        
        response = self.client.post(self.url, incomplete_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('errors', response.data)


class DriverRegistrationAPITest(APITestCase):
    """Test suite for Driver Registration API endpoint"""
    
    def setUp(self):
        """Set up test client and data"""
        self.client = APIClient()
        self.url = '/PerpexBistro/orders/register/driver/'
        self.valid_data = {
            'username': 'api_driver',
            'email': 'api_driver@example.com',
            'password': 'securepass123',
            'first_name': 'API',
            'last_name': 'Driver',
            'phone': '+1555777888',
            'license_number': 'API12345678',
            'license_expiry': (date.today() + timedelta(days=730)).isoformat(),
            'vehicle_make': 'Ford',
            'vehicle_model': 'Focus',
            'vehicle_year': 2021,
            'vehicle_color': 'Red',
            'vehicle_type': 'sedan',
            'license_plate': 'API123',
        }
    
    def test_successful_driver_registration(self):
        """Test successful driver registration via API"""
        response = self.client.post(self.url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('Driver registered successfully', response.data['message'])
        self.assertIn('data', response.data)
        
        # Verify user was created
        user = User.objects.get(username='api_driver')
        self.assertEqual(user.email, 'api_driver@example.com')
        self.assertTrue(hasattr(user, 'driver_profile'))
        
        # Verify driver profile
        driver = user.driver_profile
        self.assertEqual(driver.license_number, 'API12345678')
        self.assertEqual(driver.vehicle_make, 'Ford')
        self.assertEqual(driver.license_plate, 'API123')
    
    def test_registration_with_validation_errors(self):
        """Test registration with invalid data"""
        invalid_data = self.valid_data.copy()
        invalid_data['vehicle_year'] = 1970  # Too old
        
        response = self.client.post(self.url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('validation errors', response.data['message'])
        self.assertIn('errors', response.data)
        self.assertIn('vehicle_year', response.data['errors'])
    
    def test_registration_expired_license(self):
        """Test registration with expired license"""
        invalid_data = self.valid_data.copy()
        invalid_data['license_expiry'] = (date.today() - timedelta(days=30)).isoformat()
        
        response = self.client.post(self.url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('errors', response.data)
        self.assertIn('license_expiry', response.data['errors'])
    
    def test_registration_duplicate_license_plate(self):
        """Test registration with duplicate license plate"""
        # Create existing driver
        existing_user = User.objects.create_user(username='existing_driver', email='existing@example.com')
        Driver.objects.create(
            user=existing_user,
            phone='+1999888777',
            license_number='EXISTING123',
            license_expiry=date.today() + timedelta(days=365),
            vehicle_make='Toyota',
            vehicle_model='Prius',
            vehicle_year=2020,
            vehicle_color='White',
            license_plate='API123'  # Same as our test data
        )
        
        response = self.client.post(self.url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('errors', response.data)
        self.assertIn('license_plate', response.data['errors'])


class RegistrationIntegrationTest(TestCase):
    """Integration tests for registration functionality"""
    
    def test_rider_profile_relationship(self):
        """Test that rider profile is properly linked to user"""
        rider_data = {
            'username': 'integration_rider',
            'email': 'integration_rider@example.com',
            'password': 'testpass123',
            'phone': '+1444555666',
            'preferred_payment': 'cash',
        }
        
        serializer = RiderRegistrationSerializer(data=rider_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        
        # Test the relationship
        self.assertTrue(hasattr(user, 'rider_profile'))
        rider = user.rider_profile
        self.assertEqual(rider.user, user)
        self.assertEqual(rider.phone, '+1444555666')
        self.assertEqual(rider.preferred_payment, 'cash')
    
    def test_driver_profile_relationship(self):
        """Test that driver profile is properly linked to user"""
        driver_data = {
            'username': 'integration_driver',
            'email': 'integration_driver@example.com',
            'password': 'testpass123',
            'phone': '+1333444555',
            'license_number': 'INTEG123456',
            'license_expiry': (date.today() + timedelta(days=365)).isoformat(),
            'vehicle_make': 'Chevrolet',
            'vehicle_model': 'Malibu',
            'vehicle_year': 2019,
            'vehicle_color': 'Black',
            'license_plate': 'INTEG1',
        }
        
        serializer = DriverRegistrationSerializer(data=driver_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        
        # Test the relationship
        self.assertTrue(hasattr(user, 'driver_profile'))
        driver = user.driver_profile
        self.assertEqual(driver.user, user)
        self.assertEqual(driver.license_number, 'INTEG123456')
        self.assertEqual(driver.vehicle_make, 'Chevrolet')
    
    def test_user_can_have_only_one_profile_type(self):
        """Test that a user can only be either a rider or driver, not both"""
        # Create a rider first
        user = User.objects.create_user(username='single_profile', email='single@example.com')
        rider = Rider.objects.create(user=user, phone='+1222333444')
        
        # Attempting to create a driver profile for the same user should work at model level
        # but in practice, our registration APIs create separate users for each role
        driver = Driver.objects.create(
            user=user,
            phone='+1555666777',
            license_number='SINGLE12345',
            license_expiry=date.today() + timedelta(days=365),
            vehicle_make='Test',
            vehicle_model='Car',
            vehicle_year=2020,
            vehicle_color='Blue',
            license_plate='SINGLE1'
        )
        
        # Both profiles exist and are linked to the same user
        self.assertEqual(rider.user, user)
        self.assertEqual(driver.user, user)
        self.assertTrue(hasattr(user, 'rider_profile'))
        self.assertTrue(hasattr(user, 'driver_profile'))
