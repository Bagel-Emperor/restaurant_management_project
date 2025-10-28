"""
Comprehensive test suite for Task 14B: Nearby Drivers API View.

This module tests the get_nearby_drivers API endpoint that allows authenticated
riders to find available drivers within their vicinity for ride requests.

Test Coverage:
- Authentication and authorization (riders only)
- Location input validation
- Successful nearby driver retrieval
- Permission checks (blocking drivers and unauthenticated users)
- HTTP method restrictions
- Error handling and edge cases
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient
from orders.models import Driver, Rider
from decimal import Decimal


class NearbyDriversAPITest(TestCase):
    """Test suite for nearby drivers API endpoint."""
    
    def setUp(self):
        """Set up test fixtures: users, riders, drivers, and API client."""
        self.client = APIClient()
        
        # Create test users
        self.rider_user = User.objects.create_user(
            username='testrider',
            email='rider@example.com',
            password='testpass123'
        )
        
        self.driver_user = User.objects.create_user(
            username='testdriver',
            email='driver@example.com',
            password='testpass123'
        )
        
        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='testpass123'
        )
        
        # Create rider profile
        self.rider = Rider.objects.create(
            user=self.rider_user,
            phone='+919876543210'
        )
        
        # Create driver profiles for testing
        self.driver1 = Driver.objects.create(
            user=self.driver_user,
            phone='+919876543211',
            license_number='KA123456',
            license_expiry='2026-12-31',
            vehicle_make='Toyota',
            vehicle_model='Camry',
            vehicle_year=2020,
            vehicle_color='White',
            vehicle_type='sedan',
            license_plate='KA01AB123',
            current_latitude=Decimal('12.9716'),  # Bangalore coordinates
            current_longitude=Decimal('77.5946'),
            availability_status=Driver.STATUS_AVAILABLE
        )
        
        # Create another available driver farther away
        self.driver2_user = User.objects.create_user(
            username='driver2',
            first_name='Fatima',
            last_name='Ali'
        )
        self.driver2 = Driver.objects.create(
            user=self.driver2_user,
            phone='+919876543212',
            license_number='KA654321',
            license_expiry='2026-12-31',
            vehicle_make='Honda',
            vehicle_model='City',
            vehicle_year=2019,
            vehicle_color='Silver',
            vehicle_type='sedan',
            license_plate='KA01CD456',
            current_latitude=Decimal('13.0000'),  # ~3km away
            current_longitude=Decimal('77.6000'),
            availability_status=Driver.STATUS_AVAILABLE
        )
        
        # Create offline driver (should be filtered out)
        self.driver3_user = User.objects.create_user(username='driver3')
        self.driver3 = Driver.objects.create(
            user=self.driver3_user,
            phone='+919876543213',
            license_number='KA987654',
            license_expiry='2026-12-31',
            vehicle_make='Maruti',
            vehicle_model='Swift',
            vehicle_year=2018,
            vehicle_color='Red',
            vehicle_type='hatchback',
            license_plate='KA01EF789',
            current_latitude=Decimal('12.9500'),  # Close but offline
            current_longitude=Decimal('77.5800'),
            availability_status=Driver.STATUS_OFFLINE
        )
        
        # API endpoint URL
        self.url = reverse('nearby-drivers')
        
        # Valid location data for testing
        self.valid_location_data = {
            'latitude': 12.9716,
            'longitude': 77.5946
        }
    
    def test_successful_nearby_drivers_request(self):
        """Test successful retrieval of nearby drivers by authenticated rider."""
        self.client.force_authenticate(user=self.rider_user)
        
        response = self.client.post(self.url, self.valid_location_data, format='json')
        
        # Verify successful response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify response is a list
        self.assertIsInstance(response.data, list)
        
        # Should return 2 available drivers (offline driver filtered out)
        self.assertEqual(len(response.data), 2)
        
        # Verify response format
        for driver_data in response.data:
            self.assertIn('driver_id', driver_data)
            self.assertIn('name', driver_data)
            self.assertIn('distance_km', driver_data)
    
    def test_drivers_sorted_by_distance(self):
        """Test that returned drivers are sorted by distance (closest first)."""
        self.client.force_authenticate(user=self.rider_user)
        
        response = self.client.post(self.url, self.valid_location_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Extract distances from response
        distances = [driver['distance_km'] for driver in response.data]
        
        # Verify distances are in ascending order (closest first)
        self.assertEqual(distances, sorted(distances))
        
        # First driver should be driver1 (same coordinates)
        self.assertEqual(response.data[0]['driver_id'], self.driver1.id)
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access the endpoint."""
        # Don't authenticate the client
        response = self.client.post(self.url, self.valid_location_data, format='json')
        
        # Should return 401 Unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_non_rider_access_denied(self):
        """Test that non-rider users cannot access the endpoint."""
        # Authenticate with regular user (no rider profile)
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.post(self.url, self.valid_location_data, format='json')
        
        # Should return 403 Forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Only riders can fetch nearby drivers.')
    
    def test_driver_access_denied(self):
        """Test that drivers cannot access the nearby drivers endpoint."""
        # Authenticate with driver user
        self.client.force_authenticate(user=self.driver_user)
        
        response = self.client.post(self.url, self.valid_location_data, format='json')
        
        # Should return 403 Forbidden (drivers don't have rider profile)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Only riders can fetch nearby drivers.')
    
    def test_invalid_latitude_validation(self):
        """Test validation error for invalid latitude values."""
        self.client.force_authenticate(user=self.rider_user)
        
        # Test latitude too high
        invalid_data = {
            'latitude': 91.0,  # Invalid: > 90
            'longitude': 77.5946
        }
        
        response = self.client.post(self.url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('latitude', response.data)
    
    def test_invalid_longitude_validation(self):
        """Test validation error for invalid longitude values."""
        self.client.force_authenticate(user=self.rider_user)
        
        # Test longitude too low
        invalid_data = {
            'latitude': 12.9716,
            'longitude': -181.0  # Invalid: < -180
        }
        
        response = self.client.post(self.url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('longitude', response.data)
    
    def test_missing_latitude_field(self):
        """Test validation error when latitude is missing."""
        self.client.force_authenticate(user=self.rider_user)
        
        incomplete_data = {
            'longitude': 77.5946
            # Missing latitude
        }
        
        response = self.client.post(self.url, incomplete_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('latitude', response.data)
    
    def test_missing_longitude_field(self):
        """Test validation error when longitude is missing."""
        self.client.force_authenticate(user=self.rider_user)
        
        incomplete_data = {
            'latitude': 12.9716
            # Missing longitude
        }
        
        response = self.client.post(self.url, incomplete_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('longitude', response.data)
    
    def test_no_available_drivers(self):
        """Test response when no drivers are available."""
        # Set all drivers to offline
        Driver.objects.update(availability_status=Driver.STATUS_OFFLINE)
        
        self.client.force_authenticate(user=self.rider_user)
        
        response = self.client.post(self.url, self.valid_location_data, format='json')
        
        # Should return successful response with empty list
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
        self.assertEqual(response.data, [])
    
    def test_get_method_not_allowed(self):
        """Test that GET requests are not allowed."""
        self.client.force_authenticate(user=self.rider_user)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_put_method_not_allowed(self):
        """Test that PUT requests are not allowed."""
        self.client.force_authenticate(user=self.rider_user)
        
        response = self.client.put(self.url, self.valid_location_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_delete_method_not_allowed(self):
        """Test that DELETE requests are not allowed."""
        self.client.force_authenticate(user=self.rider_user)
        
        response = self.client.delete(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_response_content_type(self):
        """Test that response has correct content type."""
        self.client.force_authenticate(user=self.rider_user)
        
        response = self.client.post(self.url, self.valid_location_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
    
    def test_driver_data_format(self):
        """Test that each driver in response has correct data format."""
        self.client.force_authenticate(user=self.rider_user)
        
        response = self.client.post(self.url, self.valid_location_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        for driver_data in response.data:
            # Verify required fields
            self.assertIn('driver_id', driver_data)
            self.assertIn('name', driver_data)
            self.assertIn('distance_km', driver_data)
            
            # Verify data types
            self.assertIsInstance(driver_data['driver_id'], int)
            self.assertIsInstance(driver_data['name'], str)
            self.assertIsInstance(driver_data['distance_km'], (int, float))
            
            # Verify distance is non-negative
            self.assertGreaterEqual(driver_data['distance_km'], 0)
    
    def test_max_results_limit(self):
        """Test that response is limited to maximum results."""
        # Create many available drivers to test limit
        for i in range(10):
            user = User.objects.create_user(username=f'driver_bulk_{i}')
            Driver.objects.create(
                user=user,
                phone=f'+91987654{i:04d}',
                license_number=f'KA{i:06d}',
                license_expiry='2026-12-31',
                vehicle_make='TestCar',
                vehicle_model='Model',
                vehicle_year=2020,
                vehicle_color='Blue',
                vehicle_type='sedan',
                license_plate=f'KA{i:02d}XY{i:03d}',
                current_latitude=Decimal('12.9716'),
                current_longitude=Decimal('77.5946'),
                availability_status=Driver.STATUS_AVAILABLE
            )
        
        self.client.force_authenticate(user=self.rider_user)
        
        response = self.client.post(self.url, self.valid_location_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return maximum 5 drivers (as per max_results=5)
        self.assertLessEqual(len(response.data), 5)
    
    def test_empty_request_body(self):
        """Test handling of empty request body."""
        self.client.force_authenticate(user=self.rider_user)
        
        response = self.client.post(self.url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('latitude', response.data)
        self.assertIn('longitude', response.data)
    
    def test_url_pattern_correct(self):
        """Test that URL pattern matches expected format."""
        expected_url = '/PerpexBistro/orders/rider/nearby-drivers/'
        actual_url = reverse('nearby-drivers')
        
        # Verify URL contains correct segments
        self.assertIn('/rider/nearby-drivers/', actual_url)


if __name__ == '__main__':
    import unittest
    unittest.main()