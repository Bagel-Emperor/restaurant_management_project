"""
Quick test script to demonstrate Order coupon validation.

This script tests:
1. Only one coupon per order (enforced by ForeignKey)
2. Cannot change coupon on finalized orders
3. Coupon must be valid when assigned
"""

import os
import django
from decimal import Decimal
from datetime import date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_management.settings')
django.setup()

from django.core.exceptions import ValidationError
from orders.models import Order, OrderStatus, Coupon
from orders.choices import OrderStatusChoices

print("=" * 70)
print("TESTING ORDER COUPON VALIDATION")
print("=" * 70)

# Get or create order statuses
pending_status, _ = OrderStatus.objects.get_or_create(name=OrderStatusChoices.PENDING)
completed_status, _ = OrderStatus.objects.get_or_create(name=OrderStatusChoices.COMPLETED)

# Create test coupons
today = date.today()

# Valid coupon
valid_coupon, _ = Coupon.objects.get_or_create(
    code='VALID10',
    defaults={
        'discount_percentage': Decimal('10.00'),
        'is_active': True,
        'valid_from': today - timedelta(days=1),
        'valid_until': today + timedelta(days=30),
        'usage_count': 0,
        'max_usage': 100
    }
)

# Expired coupon
expired_coupon, _ = Coupon.objects.get_or_create(
    code='EXPIRED20',
    defaults={
        'discount_percentage': Decimal('20.00'),
        'is_active': True,
        'valid_from': today - timedelta(days=60),
        'valid_until': today - timedelta(days=1),  # Expired yesterday
        'usage_count': 0,
        'max_usage': 100
    }
)

# Inactive coupon
inactive_coupon, _ = Coupon.objects.get_or_create(
    code='INACTIVE15',
    defaults={
        'discount_percentage': Decimal('15.00'),
        'is_active': False,  # Not active
        'valid_from': today - timedelta(days=1),
        'valid_until': today + timedelta(days=30),
        'usage_count': 0,
        'max_usage': 100
    }
)

# Maxed out coupon
maxed_coupon, _ = Coupon.objects.get_or_create(
    code='MAXED25',
    defaults={
        'discount_percentage': Decimal('25.00'),
        'is_active': True,
        'valid_from': today - timedelta(days=1),
        'valid_until': today + timedelta(days=30),
        'usage_count': 50,
        'max_usage': 50  # Already at limit
    }
)

print("\n✅ Test 1: One coupon per order (ForeignKey enforcement)")
print("-" * 70)
try:
    order = Order(status=pending_status, total_amount=Decimal('100.00'))
    order.coupon = valid_coupon
    order.save()
    print(f"✓ Order created with coupon: {order.coupon.code}")
    
    # Try to assign a different coupon (this replaces the previous one)
    order.coupon = None
    order.save()
    print(f"✓ Coupon can be changed to None on pending order")
    
    # Clean up
    order.delete()
except Exception as e:
    print(f"✗ FAILED: {e}")

print("\n✅ Test 2: Cannot change coupon on completed orders")
print("-" * 70)
try:
    # Create completed order with a coupon
    order = Order(status=completed_status, total_amount=Decimal('100.00'), coupon=valid_coupon)
    order.save()
    print(f"✓ Completed order created with coupon: {order.coupon.code}")
    
    # Try to change coupon on completed order
    order.coupon = None
    order.save()
    print(f"✗ FAILED: Should not allow coupon change on completed order")
    order.delete()
except ValidationError as e:
    print(f"✓ Validation prevented coupon change: {e.message_dict.get('coupon', e)}")
    # Clean up
    Order.objects.filter(coupon=valid_coupon, status=completed_status).delete()

print("\n✅ Test 3: Cannot use expired coupon")
print("-" * 70)
try:
    order = Order(status=pending_status, total_amount=Decimal('100.00'), coupon=expired_coupon)
    order.save()
    print(f"✗ FAILED: Should not allow expired coupon")
    order.delete()
except ValidationError as e:
    print(f"✓ Validation prevented expired coupon: {e.message_dict.get('coupon', e)}")

print("\n✅ Test 4: Cannot use inactive coupon")
print("-" * 70)
try:
    order = Order(status=pending_status, total_amount=Decimal('100.00'), coupon=inactive_coupon)
    order.save()
    print(f"✗ FAILED: Should not allow inactive coupon")
    order.delete()
except ValidationError as e:
    print(f"✓ Validation prevented inactive coupon: {e.message_dict.get('coupon', e)}")

print("\n✅ Test 5: Cannot use maxed out coupon")
print("-" * 70)
try:
    order = Order(status=pending_status, total_amount=Decimal('100.00'), coupon=maxed_coupon)
    order.save()
    print(f"✗ FAILED: Should not allow maxed out coupon")
    order.delete()
except ValidationError as e:
    print(f"✓ Validation prevented maxed out coupon: {e.message_dict.get('coupon', e)}")

print("\n✅ Test 6: Valid coupon works correctly")
print("-" * 70)
try:
    order = Order(status=pending_status, total_amount=Decimal('100.00'), coupon=valid_coupon)
    order.save()
    print(f"✓ Order created successfully with valid coupon: {order.coupon.code}")
    print(f"  Order ID: {order.order_id}")
    print(f"  Status: {order.status.name}")
    
    # Clean up
    order.delete()
except Exception as e:
    print(f"✗ FAILED: {e}")

print("\n" + "=" * 70)
print("VALIDATION TESTS COMPLETED")
print("=" * 70)
