#!/usr/bin/env python
import os
import sys
import django

# Set up Django
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_management.settings')
django.setup()

from django.contrib.auth.models import User
from orders.models import Order, UserProfile, Customer

def analyze_order_user_tracking():
    print("=== ORDER-USER TRACKING ANALYSIS ===\n")
    
    # Check total counts
    total_users = User.objects.count()
    total_orders = Order.objects.count()
    users_with_profiles = User.objects.filter(profile__isnull=False).count()
    
    print(f"📊 Database Overview:")
    print(f"   Total Users: {total_users}")
    print(f"   Users with Profiles: {users_with_profiles}")
    print(f"   Total Orders: {total_orders}")
    
    # Check order distribution
    user_orders = Order.objects.filter(user__isnull=False).count()
    guest_orders = Order.objects.filter(user__isnull=True, customer__isnull=False).count()
    orphan_orders = Order.objects.filter(user__isnull=True, customer__isnull=True).count()
    
    print(f"\n🔗 Order Attribution:")
    print(f"   Orders linked to Users: {user_orders}")
    print(f"   Guest Orders: {guest_orders}") 
    print(f"   Orphaned Orders: {orphan_orders}")
    
    # Analyze the tracking relationship
    print(f"\n🎯 Order-User Relationship Details:")
    
    # Show foreign key relationship
    print("   ✅ Order Model has 'user' ForeignKey to Django User model")
    print("   ✅ Order Model has 'customer' ForeignKey for guest orders")
    print("   ✅ UserProfile extends User with OneToOneField relationship")
    
    # Show examples of tracked orders
    print(f"\n📋 Sample Order Tracking:")
    
    # User orders
    user_orders_sample = Order.objects.filter(user__isnull=False).select_related('user')[:3]
    if user_orders_sample:
        print("   User Orders:")
        for order in user_orders_sample:
            profile = getattr(order.user, 'profile', None)
            profile_info = f" (Profile: {profile.name})" if profile and profile.name else ""
            print(f"     Order #{order.id} -> User: {order.user.username}{profile_info}")
    
    # Guest orders  
    guest_orders_sample = Order.objects.filter(customer__isnull=False).select_related('customer')[:3]
    if guest_orders_sample:
        print("   Guest Orders:")
        for order in guest_orders_sample:
            customer_name = order.customer.name or f"Guest {order.customer.id}"
            print(f"     Order #{order.id} -> Customer: {customer_name}")
    
    # Check if orders are properly tracked through relationships
    print(f"\n🔍 Relationship Integrity:")
    
    # Test reverse relationship
    users_with_orders = User.objects.filter(orders__isnull=False).distinct().count()
    print(f"   Users who have placed orders: {users_with_orders}")
    
    # Test if we can access orders through user
    if users_with_orders > 0:
        sample_user = User.objects.filter(orders__isnull=False).first()
        user_order_count = sample_user.orders.count()
        print(f"   Sample: User '{sample_user.username}' has {user_order_count} orders")
        
        # Check if profile information is accessible
        profile = getattr(sample_user, 'profile', None)
        if profile:
            print(f"   Profile Info: Name='{profile.name}', Phone='{profile.phone}'")
    
    print(f"\n✅ CONCLUSION:")
    print(f"   The system DOES track orders to user profiles in the database!")
    print(f"   - Orders are linked to Django Users via ForeignKey")
    print(f"   - Users can be extended with UserProfile for additional info")
    print(f"   - Both authenticated user orders and guest orders are supported")
    print(f"   - Reverse relationships allow accessing user's order history")

if __name__ == '__main__':
    analyze_order_user_tracking()