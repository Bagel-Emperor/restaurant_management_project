#!/usr/bin/env python3
"""
Quick test to verify the Order Cancellation API fixes work correctly.
This tests the specific issues that were addressed based on Copilot feedback.
"""

import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_management.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from orders.models import Order, Customer, OrderStatus
from orders.choices import OrderStatusChoices
import json

def test_cancellation_fixes():
    """Test that the Order Cancellation API fixes work correctly."""
    
    print("🧪 Testing Order Cancellation API fixes...")
    
    # Create test data
    print("   📊 Setting up test data...")
    
    # Create user
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    
    # Create customer
    customer = Customer.objects.create(
        first_name='John',
        last_name='Doe',
        email='john@example.com',
        phone='1234567890'
    )
    
    # Create order statuses
    pending_status, _ = OrderStatus.objects.get_or_create(name=OrderStatusChoices.PENDING)
    cancelled_status, _ = OrderStatus.objects.get_or_create(name=OrderStatusChoices.CANCELLED)
    
    # Create test orders
    authenticated_order = Order.objects.create(
        user=user,
        total_amount=25.99,
        status=pending_status
    )
    
    guest_order = Order.objects.create(
        customer=customer,
        total_amount=15.50,
        status=pending_status
    )
    
    print(f"   ✅ Created test orders: {authenticated_order.order_id}, {guest_order.order_id}")
    
    # Initialize API client
    client = APIClient()
    
    # Test 1: Verify timestamp fix - cancelled_at should be current time
    print("\n   🕐 Test 1: Verifying cancelled_at timestamp uses current time...")
    
    client.force_authenticate(user=user)
    before_cancellation = timezone.now()
    
    response = client.delete(f'/api/orders/{authenticated_order.order_id}/cancel/')
    
    if response.status_code == 200:
        response_data = response.json()
        cancelled_at_str = response_data.get('cancelled_at')
        if cancelled_at_str:
            # Parse the timestamp
            cancelled_at = datetime.fromisoformat(cancelled_at_str.replace('Z', '+00:00'))
            
            # Check if timestamp is recent (within last minute)
            time_diff = abs((timezone.now() - cancelled_at).total_seconds())
            if time_diff < 60:  # Within 1 minute
                print("   ✅ PASS: cancelled_at timestamp correctly uses current time")
            else:
                print(f"   ❌ FAIL: cancelled_at timestamp is not current time (diff: {time_diff}s)")
        else:
            print("   ❌ FAIL: cancelled_at timestamp not found in response")
    else:
        print(f"   ❌ FAIL: Order cancellation failed with status {response.status_code}")
    
    # Test 2: Verify security fix - unauthorized guest orders should be rejected
    print("\n   🔒 Test 2: Verifying guest order security fix...")
    
    client.logout()  # Unauthenticated request
    
    # Try to cancel guest order without customer_id (should fail with our security fix)
    response = client.delete(f'/api/orders/{guest_order.order_id}/cancel/')
    
    if response.status_code == 403:
        print("   ✅ PASS: Unauthorized guest order cancellation correctly rejected")
    else:
        print(f"   ❌ FAIL: Expected 403, got {response.status_code}")
    
    # Test 3: Verify authorized guest order cancellation still works
    print("\n   🎫 Test 3: Verifying authorized guest order cancellation...")
    
    response = client.delete(
        f'/api/orders/{guest_order.order_id}/cancel/',
        data={'customer_id': customer.id},
        content_type='application/json'
    )
    
    if response.status_code == 200:
        print("   ✅ PASS: Authorized guest order cancellation works correctly")
    else:
        print(f"   ❌ FAIL: Authorized guest order cancellation failed with status {response.status_code}")
        print(f"   Response: {response.content.decode()}")
    
    # Test 4: Verify import organization - check that imports are at top
    print("\n   📦 Test 4: Verifying import organization...")
    
    with open('orders/views.py', 'r') as f:
        content = f.read()
        
    # Check if OrderStatusChoices and OrderStatus imports are at the top
    lines = content.split('\n')
    import_section = []
    for i, line in enumerate(lines):
        if line.strip().startswith('from') or line.strip().startswith('import'):
            import_section.append(line.strip())
        elif line.strip() and not line.strip().startswith('#'):
            break
    
    if 'from .choices import OrderStatusChoices' in import_section:
        print("   ✅ PASS: OrderStatusChoices import correctly moved to top")
    else:
        print("   ❌ FAIL: OrderStatusChoices import not found at top")
    
    if 'from .models import Order, Customer, UserProfile, OrderStatus' in import_section:
        print("   ✅ PASS: OrderStatus import correctly moved to top")
    else:
        print("   ❌ FAIL: OrderStatus import not found at top")
    
    print("\n🎉 All tests completed!")

if __name__ == '__main__':
    test_cancellation_fixes()