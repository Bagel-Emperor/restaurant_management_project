#!/usr/bin/env python
"""
Simple script to test the registration endpoints manually.
"""
import os
import django
import requests
import json

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_management.settings')
django.setup()

def test_rider_registration():
    """Test rider registration endpoint"""
    url = 'http://127.0.0.1:8000/PerpexBistro/orders/register/rider/'
    data = {
        'username': 'test_rider_manual',
        'email': 'test_rider@example.com',
        'password': 'securepass123',
        'first_name': 'Test',
        'last_name': 'Rider',
        'phone': '+1234567890',
        'preferred_payment': 'card',
        'default_pickup_address': '123 Test Street',
        'default_pickup_latitude': 40.7128,
        'default_pickup_longitude': -74.0060,
    }
    
    print("Testing Rider Registration...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2) if response.content else 'No content'}")
        return response.status_code == 201
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_driver_registration():
    """Test driver registration endpoint"""
    url = 'http://127.0.0.1:8000/PerpexBistro/orders/register/driver/'
    data = {
        'username': 'test_driver_manual',
        'email': 'test_driver@example.com',
        'password': 'securepass123',
        'first_name': 'Test',
        'last_name': 'Driver',
        'phone': '+1987654321',
        'license_number': 'TEST123456',
        'license_expiry': '2026-12-31',
        'vehicle_make': 'Toyota',
        'vehicle_model': 'Camry',
        'vehicle_year': 2020,
        'vehicle_color': 'Silver',
        'vehicle_type': 'sedan',
        'license_plate': 'TEST123',
    }
    
    print("\nTesting Driver Registration...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2) if response.content else 'No content'}")
        return response.status_code == 201
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("MANUAL REGISTRATION ENDPOINT TESTING")
    print("=" * 50)
    
    rider_success = test_rider_registration()
    driver_success = test_driver_registration()
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Rider Registration: {'✓ PASSED' if rider_success else '✗ FAILED'}")
    print(f"Driver Registration: {'✓ PASSED' if driver_success else '✗ FAILED'}")
    
    if rider_success and driver_success:
        print("\n🎉 All registration endpoints working correctly!")
    else:
        print("\n❌ Some endpoints need attention.")