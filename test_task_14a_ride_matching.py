"""
Comprehensive test suite for Task 14A: Ride Matching Serializers.

This module tests the LocationInputSerializer and NearbyDriverSerializer
that handle ride matching functionality, including distance calculations
and driver filtering by availability and location.

Test Coverage:
- Location input validation (latitude/longitude ranges)
- Haversine distance calculation accuracy
- Driver filtering by availability status
- Driver sorting by distance (closest first)
- Edge cases and error scenarios
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework import serializers
from orders.models import Driver
from orders.serializers import LocationInputSerializer, NearbyDriverSerializer
from decimal import Decimal
import math


class LocationInputSerializerTest(TestCase):
    """Test suite for LocationInputSerializer validation."""
    
    def test_valid_coordinates(self):
        """Test validation with valid latitude and longitude values."""
        # Test typical coordinates (Bangalore, India)
        data = {'latitude': 12.9716, 'longitude': 77.5946}
        serializer = LocationInputSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Test edge case coordinates
        edge_data = {'latitude': -89.9, 'longitude': 179.9}
        edge_serializer = LocationInputSerializer(data=edge_data)
        self.assertTrue(edge_serializer.is_valid())
    
    def test_latitude_validation(self):
        """Test latitude range validation (-90 to 90)."""
        # Test invalid latitude (too high)
        invalid_high = {'latitude': 91.0, 'longitude': 77.5946}
        serializer = LocationInputSerializer(data=invalid_high)
        self.assertFalse(serializer.is_valid())
        self.assertIn('latitude', serializer.errors)
        
        # Test invalid latitude (too low)
        invalid_low = {'latitude': -91.0, 'longitude': 77.5946}
        serializer = LocationInputSerializer(data=invalid_low)
        self.assertFalse(serializer.is_valid())
        self.assertIn('latitude', serializer.errors)
    
    def test_longitude_validation(self):
        """Test longitude range validation (-180 to 180)."""
        # Test invalid longitude (too high)
        invalid_high = {'latitude': 12.9716, 'longitude': 181.0}
        serializer = LocationInputSerializer(data=invalid_high)
        self.assertFalse(serializer.is_valid())
        self.assertIn('longitude', serializer.errors)
        
        # Test invalid longitude (too low)
        invalid_low = {'latitude': 12.9716, 'longitude': -181.0}
        serializer = LocationInputSerializer(data=invalid_low)
        self.assertFalse(serializer.is_valid())
        self.assertIn('longitude', serializer.errors)
    
    def test_missing_fields(self):
        """Test validation when required fields are missing."""
        # Missing latitude
        missing_lat = {'longitude': 77.5946}
        serializer = LocationInputSerializer(data=missing_lat)
        self.assertFalse(serializer.is_valid())
        self.assertIn('latitude', serializer.errors)
        
        # Missing longitude
        missing_lon = {'latitude': 12.9716}
        serializer = LocationInputSerializer(data=missing_lon)
        self.assertFalse(serializer.is_valid())
        self.assertIn('longitude', serializer.errors)


class NearbyDriverSerializerTest(TestCase):
    """Test suite for NearbyDriverSerializer and ride matching logic."""
    
    def setUp(self):
        """Set up test fixtures: users, drivers with different locations."""
        # Create test users
        self.user1 = User.objects.create_user(
            username='driver1',
            first_name='Amit',
            last_name='Kumar',
            email='amit@example.com'
        )
        self.user2 = User.objects.create_user(
            username='driver2',
            first_name='Fatima',
            last_name='Ali',
            email='fatima@example.com'
        )
        self.user3 = User.objects.create_user(
            username='driver3',
            first_name='Raj',
            last_name='Singh',
            email='raj@example.com'
        )
        
        # Create available driver near pickup (Bangalore coordinates)
        self.driver_nearby = Driver.objects.create(
            user=self.user1,
            phone='+919876543210',
            license_number='KA123456',
            license_expiry='2026-12-31',
            vehicle_make='Toyota',
            vehicle_model='Camry',
            vehicle_year=2020,
            vehicle_color='White',
            vehicle_type='sedan',
            license_plate='KA01AB123',
            current_latitude=Decimal('12.9716'),  # Bangalore
            current_longitude=Decimal('77.5946'),
            availability_status=Driver.STATUS_AVAILABLE
        )
        
        # Create available driver farther away
        self.driver_farther = Driver.objects.create(
            user=self.user2,
            phone='+919876543211',
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
        
        # Create unavailable driver (should be filtered out)
        self.driver_offline = Driver.objects.create(
            user=self.user3,
            phone='+919876543212',
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
    
    def test_haversine_distance_calculation(self):
        """Test accuracy of Haversine distance formula."""
        # Test known distance: Bangalore to Mysore (straight-line ~128 km)
        bangalore_lat, bangalore_lon = 12.9716, 77.5946
        mysore_lat, mysore_lon = 12.2958, 76.6394
        
        calculated_distance = NearbyDriverSerializer.haversine(
            bangalore_lat, bangalore_lon, mysore_lat, mysore_lon
        )
        
        # Haversine gives straight-line distance (~128 km), not road distance
        self.assertAlmostEqual(calculated_distance, 128, delta=10)
    
    def test_haversine_same_location(self):
        """Test Haversine formula with identical coordinates."""
        lat, lon = 12.9716, 77.5946
        distance = NearbyDriverSerializer.haversine(lat, lon, lat, lon)
        self.assertEqual(distance, 0.0)
    
    def test_get_nearby_drivers_filtering(self):
        """Test that only available drivers are returned."""
        pickup_lat, pickup_lon = 12.9716, 77.5946
        
        nearby_drivers = NearbyDriverSerializer.get_nearby_drivers(
            pickup_lat, pickup_lon
        )
        
        # Should return 2 available drivers (offline driver filtered out)
        self.assertEqual(len(nearby_drivers), 2)
        
        # Verify returned driver IDs
        driver_ids = [d['driver_id'] for d in nearby_drivers]
        self.assertIn(self.driver_nearby.id, driver_ids)
        self.assertIn(self.driver_farther.id, driver_ids)
        self.assertNotIn(self.driver_offline.id, driver_ids)  # Offline filtered out
    
    def test_get_nearby_drivers_sorting(self):
        """Test that drivers are sorted by distance (closest first)."""
        pickup_lat, pickup_lon = 12.9716, 77.5946
        
        nearby_drivers = NearbyDriverSerializer.get_nearby_drivers(
            pickup_lat, pickup_lon
        )
        
        # First driver should be the closer one
        self.assertEqual(nearby_drivers[0]['driver_id'], self.driver_nearby.id)
        self.assertEqual(nearby_drivers[1]['driver_id'], self.driver_farther.id)
        
        # Verify distances are in ascending order
        distances = [d['distance_km'] for d in nearby_drivers]
        self.assertEqual(distances, sorted(distances))
    
    def test_get_nearby_drivers_distance_accuracy(self):
        """Test accuracy of calculated distances in results."""
        pickup_lat, pickup_lon = 12.9716, 77.5946
        
        nearby_drivers = NearbyDriverSerializer.get_nearby_drivers(
            pickup_lat, pickup_lon
        )
        
        # Find the nearby driver result
        nearby_result = next(
            d for d in nearby_drivers 
            if d['driver_id'] == self.driver_nearby.id
        )
        
        # Distance should be very small (same coordinates)
        self.assertLess(nearby_result['distance_km'], 1.0)
        
        # Distance should be rounded to 2 decimal places
        self.assertEqual(
            nearby_result['distance_km'], 
            round(nearby_result['distance_km'], 2)
        )
    
    def test_get_nearby_drivers_max_results(self):
        """Test that max_results parameter limits returned drivers."""
        pickup_lat, pickup_lon = 12.9716, 77.5946
        
        # Test with limit of 1
        nearby_drivers = NearbyDriverSerializer.get_nearby_drivers(
            pickup_lat, pickup_lon, max_results=1
        )
        
        self.assertEqual(len(nearby_drivers), 1)
        # Should return the closest driver
        self.assertEqual(nearby_drivers[0]['driver_id'], self.driver_nearby.id)
    
    def test_get_nearby_drivers_name_handling(self):
        """Test driver name extraction from User model."""
        pickup_lat, pickup_lon = 12.9716, 77.5946
        
        nearby_drivers = NearbyDriverSerializer.get_nearby_drivers(
            pickup_lat, pickup_lon
        )
        
        # Find driver with full name
        amit_result = next(
            d for d in nearby_drivers 
            if d['driver_id'] == self.driver_nearby.id
        )
        
        # Should use get_full_name() result
        self.assertEqual(amit_result['name'], 'Amit Kumar')
    
    def test_get_nearby_drivers_no_available_drivers(self):
        """Test behavior when no drivers are available."""
        # Set all drivers to offline
        Driver.objects.update(availability_status=Driver.STATUS_OFFLINE)
        
        pickup_lat, pickup_lon = 12.9716, 77.5946
        
        nearby_drivers = NearbyDriverSerializer.get_nearby_drivers(
            pickup_lat, pickup_lon
        )
        
        # Should return empty list
        self.assertEqual(len(nearby_drivers), 0)
    
    def test_get_nearby_drivers_null_coordinates(self):
        """Test filtering out drivers with null coordinates."""
        # Create driver without coordinates
        user4 = User.objects.create_user(username='driver4')
        driver_no_coords = Driver.objects.create(
            user=user4,
            phone='+919876543213',
            license_number='KA111111',
            license_expiry='2026-12-31',
            vehicle_make='Tata',
            vehicle_model='Nexon',
            vehicle_year=2021,
            vehicle_color='Blue',
            vehicle_type='suv',
            license_plate='KA01GH123',
            current_latitude=None,  # No coordinates
            current_longitude=None,
            availability_status=Driver.STATUS_AVAILABLE
        )
        
        pickup_lat, pickup_lon = 12.9716, 77.5946
        
        nearby_drivers = NearbyDriverSerializer.get_nearby_drivers(
            pickup_lat, pickup_lon
        )
        
        # Should not include driver without coordinates
        driver_ids = [d['driver_id'] for d in nearby_drivers]
        self.assertNotIn(driver_no_coords.id, driver_ids)
    
    def test_serializer_output_format(self):
        """Test that serializer produces expected output format."""
        # Test serializer with sample data
        data = {
            'driver_id': 1,
            'name': 'Test Driver',
            'distance_km': 1.23
        }
        
        serializer = NearbyDriverSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Verify all expected fields present
        self.assertIn('driver_id', serializer.validated_data)
        self.assertIn('name', serializer.validated_data)
        self.assertIn('distance_km', serializer.validated_data)


if __name__ == '__main__':
    import unittest
    unittest.main()