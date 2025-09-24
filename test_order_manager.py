"""
Test script for the custom OrderManager.
This script creates test data and demonstrates the get_active_orders() functionality.
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_management.settings')
django.setup()

from django.contrib.auth.models import User
from orders.models import Order, OrderStatus, Customer
from orders.choices import OrderStatusChoices
from home.models import Restaurant, MenuItem
from decimal import Decimal


def create_test_data():
    """Create test data for testing the OrderManager."""
    print("Creating test data...")
    
    # Create a test restaurant if it doesn't exist
    restaurant, created = Restaurant.objects.get_or_create(
        name='Test Restaurant',
        defaults={
            'owner_name': 'Test Owner',
            'email': 'owner@test.com',
            'phone_number': '555-1234'
        }
    )
    
    # Create a test menu item if it doesn't exist
    menu_item, created = MenuItem.objects.get_or_create(
        name='Test Burger',
        defaults={
            'description': 'A delicious test burger',
            'price': Decimal('12.99'),
            'restaurant': restaurant,
            'is_available': True
        }
    )
    
    # Create test user if it doesn't exist
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    # Create test customer if it doesn't exist
    customer, created = Customer.objects.get_or_create(
        name='John Doe',
        defaults={
            'phone': '555-9876',
            'email': 'john@example.com'
        }
    )
    
    # Ensure all order statuses exist
    status_objects = {}
    for status_choice in [OrderStatusChoices.PENDING, OrderStatusChoices.PROCESSING, 
                         OrderStatusChoices.COMPLETED, OrderStatusChoices.CANCELLED]:
        status_obj, created = OrderStatus.objects.get_or_create(name=status_choice)
        status_objects[status_choice] = status_obj
        if created:
            print(f"Created status: {status_choice}")
    
    # Create test orders with different statuses
    test_orders = [
        {'status': OrderStatusChoices.PENDING, 'amount': Decimal('25.99')},
        {'status': OrderStatusChoices.PROCESSING, 'amount': Decimal('35.50')},
        {'status': OrderStatusChoices.PENDING, 'amount': Decimal('18.75')},
        {'status': OrderStatusChoices.COMPLETED, 'amount': Decimal('42.00')},
        {'status': OrderStatusChoices.PROCESSING, 'amount': Decimal('29.99')},
        {'status': OrderStatusChoices.CANCELLED, 'amount': Decimal('15.25')},
    ]
    
    # Clear existing test orders to avoid duplicates
    Order.objects.filter(user=user).delete()
    
    created_orders = []
    for i, order_data in enumerate(test_orders):
        order = Order.objects.create(
            user=user,
            customer=customer,
            status=status_objects[order_data['status']],
            total_amount=order_data['amount']
        )
        created_orders.append(order)
        print(f"Created Order {order.id} with status '{order.status.name}' and amount ${order.total_amount}")
    
    print(f"\nCreated {len(created_orders)} test orders")
    return created_orders


def test_order_manager():
    """Test the custom OrderManager functionality."""
    print("\n" + "="*50)
    print("TESTING CUSTOM ORDER MANAGER")
    print("="*50)
    
    # Test 1: Get all orders
    all_orders = Order.objects.all()
    print(f"\n📊 Total Orders: {all_orders.count()}")
    
    for order in all_orders:
        print(f"   Order {order.id}: {order.status.name} - ${order.total_amount}")
    
    # Test 2: Get active orders using our custom manager method
    active_orders = Order.objects.get_active_orders()
    print(f"\n🔄 Active Orders (Pending + Processing): {active_orders.count()}")
    
    for order in active_orders:
        print(f"   Order {order.id}: {order.status.name} - ${order.total_amount}")
    
    # Test 3: Verify that only pending and processing orders are returned
    expected_statuses = [OrderStatusChoices.PENDING, OrderStatusChoices.PROCESSING]
    for order in active_orders:
        if order.status.name not in expected_statuses:
            print(f"❌ ERROR: Order {order.id} has status '{order.status.name}' but should only have pending or processing!")
            return False
    
    print(f"\n✅ SUCCESS: All active orders have correct status (pending or processing)")
    
    # Test 4: Count verification
    pending_count = Order.objects.filter(status__name=OrderStatusChoices.PENDING).count()
    processing_count = Order.objects.filter(status__name=OrderStatusChoices.PROCESSING).count()
    expected_active_count = pending_count + processing_count
    
    print(f"\n📈 Status Breakdown:")
    print(f"   Pending: {pending_count}")
    print(f"   Processing: {processing_count}")
    print(f"   Expected Active Total: {expected_active_count}")
    print(f"   Actual Active Total: {active_orders.count()}")
    
    if active_orders.count() == expected_active_count:
        print("✅ Count verification passed!")
    else:
        print("❌ Count verification failed!")
        return False
    
    return True


def main():
    """Main function to run the test."""
    print("🧪 Testing Custom Order Manager")
    print("="*50)
    
    try:
        # Create test data
        create_test_data()
        
        # Test the manager
        success = test_order_manager()
        
        if success:
            print(f"\n🎉 All tests passed! The custom OrderManager is working correctly.")
            print(f"\n💡 You can now use Order.objects.get_active_orders() in your Django shell or views!")
        else:
            print(f"\n❌ Some tests failed. Please check the implementation.")
            
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()