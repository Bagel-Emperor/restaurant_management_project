#!/usr/bin/env python
"""
Script to create test table data for testing table API endpoints.
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_management.settings')
django.setup()

from home.models import Restaurant, Table

def create_test_tables():
    """Create test tables for API testing."""
    print("Creating test table data...")
    
    # Get or create a test restaurant
    restaurant, created = Restaurant.objects.get_or_create(
        name='PerpexBistro Test',
        defaults={
            'owner_name': 'Test Owner',
            'email': 'test@perpexbistro.com',
            'phone_number': '555-1234',
        }
    )
    
    if created:
        print(f"✅ Created restaurant: {restaurant.name}")
    else:
        print(f"✅ Using existing restaurant: {restaurant.name}")
    
    # Create test tables
    test_tables = [
        {
            'number': 1,
            'capacity': 2,
            'location': 'indoor',
            'status': 'available',
            'description': 'Cozy table for two by the window'
        },
        {
            'number': 2,
            'capacity': 4,
            'location': 'indoor', 
            'status': 'occupied',
            'description': 'Standard four-person table'
        },
        {
            'number': 3,
            'capacity': 6,
            'location': 'outdoor',
            'status': 'available', 
            'description': 'Large outdoor patio table'
        },
        {
            'number': 4,
            'capacity': 2,
            'location': 'bar',
            'status': 'reserved',
            'description': 'Bar-style high table'
        },
        {
            'number': 5,
            'capacity': 8,
            'location': 'private',
            'status': 'maintenance',
            'description': 'Private dining room table'
        }
    ]
    
    created_count = 0
    for table_data in test_tables:
        table, created = Table.objects.get_or_create(
            restaurant=restaurant,
            number=table_data['number'],
            defaults={
                'capacity': table_data['capacity'],
                'location': table_data['location'],
                'status': table_data['status'],
                'description': table_data['description'],
            }
        )
        
        if created:
            created_count += 1
            print(f"✅ Created Table {table.number}: {table.capacity} seats - {table.status}")
        else:
            print(f"ℹ️  Table {table.number} already exists")
    
    print(f"\n🎉 Test data creation complete!")
    print(f"📊 Total tables in database: {Table.objects.count()}")
    print(f"🆕 New tables created: {created_count}")
    
    return restaurant

if __name__ == "__main__":
    create_test_tables()