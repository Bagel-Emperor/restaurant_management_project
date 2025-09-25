#!/usr/bin/env python
import os
import sys
import django

# Set up Django
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_management.settings')
django.setup()

from orders.email_utils import send_order_confirmation_email, send_bulk_order_notifications
from orders.models import Order
from django.contrib.auth.models import User

def test_email_functionality():
    print("🧪 TESTING ORDER CONFIRMATION EMAIL FUNCTIONALITY\n")
    
    # Test 1: Valid order with user email
    print("Test 1: Send confirmation email for user order")
    user_order = Order.objects.filter(user__isnull=False, user__email__isnull=False).first()
    
    if user_order and user_order.user.email:
        result = send_order_confirmation_email(
            order_id=user_order.id,
            customer_email=user_order.user.email,
            customer_name=user_order.user.get_full_name() or user_order.user.username
        )
        print(f"  Result: {result}")
        print(f"  ✅ Success: {result['success']}")
        print(f"  📧 Email sent: {result['email_sent']}")
        print(f"  💬 Message: {result['message']}\n")
    else:
        print("  ⚠️  No user orders with email found, creating test email...\n")
        # Test with dummy data
        test_order = Order.objects.first()
        if test_order:
            result = send_order_confirmation_email(
                order_id=test_order.id,
                customer_email="test@example.com",
                customer_name="Test Customer"
            )
            print(f"  Result: {result}")
            print(f"  ✅ Success: {result['success']}")
            print(f"  📧 Email sent: {result['email_sent']}")
            print(f"  💬 Message: {result['message']}\n")
    
    # Test 2: Invalid email address
    print("Test 2: Invalid email address handling")
    test_order = Order.objects.first()
    if test_order:
        result = send_order_confirmation_email(
            order_id=test_order.id,
            customer_email="invalid-email",
            customer_name="Test Customer"
        )
        print(f"  Result: {result}")
        print(f"  ✅ Success: {result['success']} (should be False)")
        print(f"  💬 Message: {result['message']}\n")
    
    # Test 3: Non-existent order
    print("Test 3: Non-existent order handling")
    result = send_order_confirmation_email(
        order_id=99999,
        customer_email="test@example.com",
        customer_name="Test Customer"
    )
    print(f"  Result: {result}")
    print(f"  ✅ Success: {result['success']} (should be False)")
    print(f"  💬 Message: {result['message']}\n")
    
    # Test 4: Bulk email sending
    print("Test 4: Bulk email notifications")
    order_ids = list(Order.objects.values_list('id', flat=True)[:3])
    if order_ids:
        bulk_results = send_bulk_order_notifications(
            orders=order_ids,
            email_type='confirmation'
        )
        print(f"  Bulk Results: {bulk_results}")
        print(f"  📊 Total orders: {bulk_results['total_orders']}")
        print(f"  ✅ Successful: {bulk_results['successful_emails']}")
        print(f"  ❌ Failed: {bulk_results['failed_emails']}")
        if bulk_results['errors']:
            print(f"  🚨 Errors: {bulk_results['errors']}")
    
    print("\n🎉 Email functionality testing completed!")
    
    # Show current email settings
    print("\n📧 CURRENT EMAIL CONFIGURATION:")
    from django.conf import settings
    print(f"  Backend: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
    print(f"  Host: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
    print(f"  Port: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
    print(f"  From Email: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")

if __name__ == '__main__':
    test_email_functionality()