"""
Script to create sample payment methods for testing the PaymentMethod API.

Run this script to populate the database with common payment methods.
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_management.settings')
django.setup()

from orders.models import PaymentMethod

def create_sample_payment_methods():
    """Create sample payment methods for testing."""
    
    payment_methods_data = [
        {
            'name': 'Credit Card',
            'description': 'Pay securely with Visa, Mastercard, or American Express',
            'is_active': True
        },
        {
            'name': 'Debit Card',
            'description': 'Pay directly from your bank account',
            'is_active': True
        },
        {
            'name': 'Cash',
            'description': 'Pay with physical currency upon delivery',
            'is_active': True
        },
        {
            'name': 'PayPal',
            'description': 'Pay securely with your PayPal account',
            'is_active': True
        },
        {
            'name': 'Apple Pay',
            'description': 'Quick payment with Apple devices',
            'is_active': True
        },
        {
            'name': 'Google Pay',
            'description': 'Quick payment with Google wallet',
            'is_active': True
        },
        {
            'name': 'Check',
            'description': 'Pay with personal or cashier check (deprecated)',
            'is_active': False  # Inactive example
        },
    ]
    
    created_count = 0
    skipped_count = 0
    
    for data in payment_methods_data:
        payment_method, created = PaymentMethod.objects.get_or_create(
            name=data['name'],
            defaults={
                'description': data['description'],
                'is_active': data['is_active']
            }
        )
        
        if created:
            print(f"✅ Created: {payment_method.name} (Active: {payment_method.is_active})")
            created_count += 1
        else:
            print(f"⏭️  Already exists: {payment_method.name}")
            skipped_count += 1
    
    print(f"\n📊 Summary:")
    print(f"   Created: {created_count}")
    print(f"   Skipped: {skipped_count}")
    print(f"   Total: {PaymentMethod.objects.count()}")
    print(f"   Active: {PaymentMethod.objects.filter(is_active=True).count()}")
    print(f"   Inactive: {PaymentMethod.objects.filter(is_active=False).count()}")

if __name__ == '__main__':
    print("🔧 Creating sample payment methods...\n")
    create_sample_payment_methods()
    print("\n✨ Done!")
