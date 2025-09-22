"""
Test script for the enhanced Menu Item API with ViewSet
This script demonstrates all the functionality of the new MenuItemViewSet
"""

import json
import os
import sys

# Setup Django test environment
def setup_django():
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_management.settings')
    
    import django
    django.setup()

def test_menu_item_api():
    """Test the MenuItemViewSet functionality"""
    from django.test import Client
    from django.contrib.auth.models import User
    from home.models import Restaurant, MenuItem
    
    # Create test client
    client = Client()
    
    print("=== Menu Item API Test Suite ===")
    
    # Setup test data
    print("\n1. Setting up test data...")
    
    # Create a restaurant if none exists
    restaurant, created = Restaurant.objects.get_or_create(
        name="Test Restaurant",
        defaults={
            'owner_name': 'Test Owner',
            'email': 'test@restaurant.com',
            'phone_number': '555-1234'
        }
    )
    print(f"✅ Restaurant: {restaurant.name} ({'created' if created else 'existing'})")
    
    # Create admin user for testing
    admin_user, created = User.objects.get_or_create(
        username='testadmin',
        defaults={
            'email': 'admin@test.com',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin_user.set_password('testpass123')
        admin_user.save()
    print(f"✅ Admin user: {admin_user.username} ({'created' if created else 'existing'})")
    
    # Test 2: GET /api/menu-items/ (public access)
    print("\n2. Testing GET /api/menu-items/ (public access)...")
    response = client.get('/PerpexBistro/api/menu-items/')
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 3: POST /api/menu-items/ (should fail without authentication)
    print("\n3. Testing POST /api/menu-items/ (no auth - should fail)...")
    test_item = {
        'name': 'Test Pizza',
        'description': 'A delicious test pizza',
        'price': 15.99,
        'restaurant': restaurant.id,
        'is_available': True
    }
    response = client.post('/PerpexBistro/api/menu-items/', 
                          json.dumps(test_item), 
                          content_type='application/json')
    print(f"Status: {response.status_code} (should be 401/403)")
    
    # Test 4: Login and POST /api/menu-items/ (should succeed)
    print("\n4. Testing POST /api/menu-items/ (with admin auth)...")
    client.force_login(admin_user)
    response = client.post('/PerpexBistro/api/menu-items/', 
                          json.dumps(test_item), 
                          content_type='application/json')
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        created_item = response.json()
        print(f"✅ Created item: {created_item['name']} - ${created_item['price']}")
        item_id = created_item['id']
    else:
        print(f"❌ Error: {response.json()}")
        return
    
    # Test 5: PUT /api/menu-items/{id}/ (update)
    print(f"\n5. Testing PUT /api/menu-items/{item_id}/ (update)...")
    updated_item = test_item.copy()
    updated_item['price'] = 18.99
    updated_item['name'] = 'Updated Test Pizza'
    
    response = client.put(f'/PerpexBistro/api/menu-items/{item_id}/', 
                         json.dumps(updated_item), 
                         content_type='application/json')
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        updated = response.json()
        print(f"✅ Updated: {updated['name']} - ${updated['price']}")
    
    # Test 6: Custom action - toggle availability
    print(f"\n6. Testing PATCH /api/menu-items/{item_id}/toggle_availability/...")
    response = client.patch(f'/PerpexBistro/api/menu-items/{item_id}/toggle_availability/')
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ {result['message']}")
    
    # Test 7: Validation - negative price
    print("\n7. Testing validation (negative price)...")
    invalid_item = test_item.copy()
    invalid_item['price'] = -5.00
    invalid_item['name'] = 'Invalid Item'
    
    response = client.post('/PerpexBistro/api/menu-items/', 
                          json.dumps(invalid_item), 
                          content_type='application/json')
    print(f"Status: {response.status_code} (should be 400)")
    if response.status_code == 400:
        errors = response.json()
        print(f"✅ Validation error caught: {errors}")
    
    # Test 8: GET with filters
    print(f"\n8. Testing GET /api/menu-items/?restaurant={restaurant.id}...")
    response = client.get(f'/PerpexBistro/api/menu-items/?restaurant={restaurant.id}')
    print(f"Status: {response.status_code}")
    filtered_items = response.json()
    print(f"✅ Found {len(filtered_items)} items for restaurant {restaurant.id}")
    
    # Test 9: DELETE
    print(f"\n9. Testing DELETE /api/menu-items/{item_id}/...")
    response = client.delete(f'/PerpexBistro/api/menu-items/{item_id}/')
    print(f"Status: {response.status_code} (should be 204)")
    
    print("\n=== Test Suite Complete ===")

if __name__ == '__main__':
    setup_django()
    test_menu_item_api()