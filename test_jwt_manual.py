"""
Simple test script to verify JWT authentication functionality.
"""

import os
import sys
import django

# Add the project root to Python path
project_root = os.path.dirname(__file__)
sys.path.insert(0, project_root)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_management.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.test import Client
import json

def test_jwt_functionality():
    """Test JWT authentication functionality."""
    
    print("=== JWT Authentication Test ===")
    
    # Create test user (recreate to ensure correct password)
    try:
        user = User.objects.get(username='testuser')
        user.delete()
        print("✓ Deleted existing test user")
    except User.DoesNotExist:
        pass
    
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpassword123'
    )
    print("✓ Created fresh test user")
    
    # Test JWT token generation programmatically
    try:
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        print(f"✓ JWT tokens generated successfully")
        print(f"  Access token preview: {str(access_token)[:50]}...")
        print(f"  Refresh token preview: {str(refresh)[:50]}...")
    except Exception as e:
        print(f"✗ JWT token generation failed: {e}")
        return False
    
    # Test Django API client
    client = Client()
    
    # Test token obtain endpoint
    try:
        data = json.dumps({
            'username': 'testuser',
            'password': 'testpassword123'
        })
        response = client.post('/api/token/', data, content_type='application/json')
        
        print(f"✓ API token obtain endpoint status: {response.status_code}")
        
        if response.status_code == 301:
            print(f"  Redirect location: {response.get('Location', 'No location header')}")
            # Follow redirect manually
            response2 = client.post('/api/token/', data, content_type='application/json')
            print(f"  After redirect status: {response2.status_code}")
            if response2.status_code == 200:
                response = response2
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Response keys: {list(data.keys())}")
            if 'access' in data and 'refresh' in data:
                print("✓ Token obtain endpoint working correctly")
            else:
                print("✗ Token obtain endpoint missing tokens")
        else:
            print(f"✗ Token obtain endpoint failed with status: {response.status_code}")
            print(f"  Response: {response.content.decode()}")
    
    except Exception as e:
        print(f"✗ Token obtain endpoint error: {e}")
    
    # Test custom login endpoint
    try:
        data = json.dumps({
            'username': 'testuser',
            'password': 'testpassword123'
        })
        response = client.post('/PerpexBistro/orders/auth/login/', data, content_type='application/json')
        
        print(f"✓ Custom login endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Response keys: {list(data.keys())}")
            if 'access' in data and 'refresh' in data and 'user' in data:
                print("✓ Custom login endpoint working correctly")
                return True
            else:
                print("✗ Custom login endpoint missing expected data")
        else:
            print(f"✗ Custom login endpoint failed with status: {response.status_code}")
            print(f"  Response: {response.content.decode()}")
    
    except Exception as e:
        print(f"✗ Custom login endpoint error: {e}")
    
    return False

if __name__ == '__main__':
    success = test_jwt_functionality()
    if success:
        print("\n✓ JWT authentication is working correctly!")
    else:
        print("\n✗ JWT authentication has issues that need to be fixed.")