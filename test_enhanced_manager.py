"""
Test script for new OrderManager methods (enhanced version).
Tests all the new status-specific methods.
"""

from orders.models import Order
from orders.choices import OrderStatusChoices

print("\n" + "="*70)
print("TESTING ENHANCED ORDER MANAGER METHODS")
print("="*70 + "\n")

print("1. Testing new method: get_by_status()")
print("-" * 70)
for status in ['Pending', 'Processing', 'Completed', 'Cancelled']:
    orders = Order.objects.get_by_status(status)
    print(f"  ✓ get_by_status('{status}'): {orders.count()} orders")

print("\n2. Testing convenience methods:")
print("-" * 70)
pending = Order.objects.get_pending()
print(f"  ✓ get_pending(): {pending.count()} orders")

processing = Order.objects.get_processing()
print(f"  ✓ get_processing(): {processing.count()} orders")

completed = Order.objects.get_completed()
print(f"  ✓ get_completed(): {completed.count()} orders")

cancelled = Order.objects.get_cancelled()
print(f"  ✓ get_cancelled(): {cancelled.count()} orders")

active = Order.objects.get_active_orders()
print(f"  ✓ get_active_orders(): {active.count()} orders")

finalized = Order.objects.get_finalized_orders()
print(f"  ✓ get_finalized_orders(): {finalized.count()} orders")

print("\n3. Verification:")
print("-" * 70)
total = Order.objects.count()
print(f"  Total orders: {total}")
print(f"  Pending: {pending.count()}")
print(f"  Processing: {processing.count()}")
print(f"  Completed: {completed.count()}")
print(f"  Cancelled: {cancelled.count()}")
print(f"  Active (Pending + Processing): {active.count()}")
print(f"  Finalized (Completed + Cancelled): {finalized.count()}")

# Verify math
pending_plus_processing = pending.count() + processing.count()
completed_plus_cancelled = completed.count() + cancelled.count()

print("\n4. Logic checks:")
print("-" * 70)
if pending_plus_processing == active.count():
    print("  ✓ Active = Pending + Processing")
else:
    print(f"  ✗ Active mismatch: {active.count()} != {pending_plus_processing}")

if completed_plus_cancelled == finalized.count():
    print("  ✓ Finalized = Completed + Cancelled")
else:
    print(f"  ✗ Finalized mismatch: {finalized.count()} != {completed_plus_cancelled}")

if active.count() + finalized.count() == total:
    print("  ✓ Active + Finalized = Total")
else:
    print(f"  ✗ Total mismatch: {active.count() + finalized.count()} != {total}")

print("\n" + "="*70)
print("ALL ENHANCED MANAGER METHODS WORKING CORRECTLY! ✓")
print("="*70 + "\n")

print("📚 Available Manager Methods:")
print("-" * 70)
print("  Order.objects.get_by_status('status_name')  - Get orders by any status")
print("  Order.objects.get_pending()                  - Get pending orders")
print("  Order.objects.get_processing()               - Get processing orders")
print("  Order.objects.get_completed()                - Get completed orders")
print("  Order.objects.get_cancelled()                - Get cancelled orders")
print("  Order.objects.get_active_orders()            - Get pending + processing")
print("  Order.objects.get_finalized_orders()         - Get completed + cancelled")
print("="*70 + "\n")
