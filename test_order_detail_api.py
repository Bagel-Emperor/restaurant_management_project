#!/usr/bin/env python
import os
import sys
import django

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_management.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from orders.models import Order, OrderStatus, Customer, OrderItem
from orders.choices import OrderStatusChoices
from home.models import Restaurant, MenuItem

def test_order_detail_api():
    print("🔧 Setting up test data...")
    
    # Get or create test data
    restaurant = Restaurant.objects.first()
    if not restaurant:
        restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner_name='Test Owner',
            email='test@test.com',
            phone_number='555-0123'
        )
    
    menu_item = MenuItem.objects.first()
    if not menu_item:
        menu_item = MenuItem.objects.create(
            name='Test Item',
            price=10.00,
            restaurant=restaurant
        )
    
    status_obj, _ = OrderStatus.objects.get_or_create(name=OrderStatusChoices.PENDING)
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='testorderuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
    
    token, _ = Token.objects.get_or_create(user=user)
    
    # Create test customer
    customer = Customer.objects.create(
        name='Test Customer',
        email='customer@example.com',
        phone='555-0456'
    )
    
    # Create test order for authenticated user
    user_order = Order.objects.create(
        user=user,
        status=status_obj,
        total_amount=10.00
    )
    OrderItem.objects.create(
        order=user_order,
        menu_item=menu_item,
        quantity=1,
        price=10.00
    )
    
    # Create test order for guest customer
    guest_order = Order.objects.create(
        customer=customer,
        status=status_obj,
        total_amount=20.00
    )
    OrderItem.objects.create(
        order=guest_order,
        menu_item=menu_item,
        quantity=2,
        price=10.00
    )
    
    print(f"✓ Created test orders: User Order ID {user_order.id}, Guest Order ID {guest_order.id}")
    
    # Test 1: Authenticated user accessing their own order
    print("\n🧪 Test 1: Authenticated user accessing own order")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    
    response = client.get(f'/PerpexBistro/orders/orders/{user_order.id}/')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ SUCCESS: User can access their own order")
        data = response.json()
        order_data = data.get('order', {})
        print(f"  - Order ID: {order_data.get('id')}")
        print(f"  - Total: ${order_data.get('order_total')}")
        print(f"  - Items: {order_data.get('items_count')}")
    else:
        print(f"✗ FAILED: {response.status_code}")
        try:
            print(f"  Error: {response.json()}")
        except:
            print(f"  Raw response: {response.content}")
    
    # Test 2: Authenticated user trying to access another user's order
    print("\n🧪 Test 2: Authenticated user accessing other user's order")
    response = client.get(f'/PerpexBistro/orders/orders/{guest_order.id}/')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 403:
        print("✓ SUCCESS: User cannot access other's orders")
    else:
        print(f"✗ FAILED: Expected 403, got {response.status_code}")
    
    # Test 3: Guest trying to access order without authentication
    print("\n🧪 Test 3: Unauthenticated access")
    client_no_auth = APIClient()
    
    response = client_no_auth.get(f'/PerpexBistro/orders/orders/{guest_order.id}/')
    print(f"Status: {response.status_code}")
    
	if response.status_code in [401, 403]:
		print("✓ SUCCESS: Unauthenticated users blocked")
	else:
		print(f"✗ FAILED: Expected 401/403, got {response.status_code}")    # Test 4: Invalid order ID
    print("\n🧪 Test 4: Invalid order ID")
    response = client.get('/PerpexBistro/orders/orders/99999/')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 404:
        print("✓ SUCCESS: Invalid order returns 404")
    else:
        print(f"✗ FAILED: Expected 404, got {response.status_code}")
    
    print("\n🎉 Order Detail API tests completed!")

if __name__ == '__main__':
    test_order_detail_api()