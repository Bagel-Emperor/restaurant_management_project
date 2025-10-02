#!/usr/bin/env python
"""
Django-based test script for Table API endpoints.
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_management.settings')
django.setup()

from django.test import Client
from django.urls import reverse
import json

def test_table_endpoints():
    """Test both table list and detail API endpoints."""
    print("🚀 Testing Table API Endpoints")
    print("=" * 50)
    
    # Create test client
    client = Client()
    
    # Test 1: Table List API
    print("\n🧪 Test 1: Table List API")
    try:
        response = client.get('/PerpexBistro/api/tables/')
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            tables = data.get('results', [])
            total_count = data.get('count', 0)
            
            print(f"✅ SUCCESS: Found {total_count} tables total, showing {len(tables)} on this page")
            
            if tables:
                print(f"\n📋 Sample table data (Table {tables[0]['number']}):")
                print(f"   ID: {tables[0]['id']}")
                print(f"   Number: {tables[0]['number']}")
                print(f"   Capacity: {tables[0]['capacity']} seats")
                print(f"   Location: {tables[0]['location_display']}")
                print(f"   Status: {tables[0]['status_display']}")
                print(f"   Available: {tables[0]['is_available']}")
                print(f"   Restaurant: {tables[0]['restaurant_name']}")
                
                # Store first table ID for detail test
                first_table_id = tables[0]['id']
            else:
                print("⚠️  No tables found in database")
                first_table_id = None
                
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"Response: {response.content.decode()}")
            return
            
    except Exception as e:
        print(f"❌ ERROR in table list test: {str(e)}")
        return
    
    # Test 2: Table Detail API
    if first_table_id is None:
        print("\n⚠️  Skipping detail tests - no tables found")
        return
        
    print(f"\n🧪 Test 2: Table Detail API (ID: {first_table_id})")
    try:
        response = client.get(f'/PerpexBistro/api/tables/{first_table_id}/')
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            table = response.json()
            print(f"✅ SUCCESS: Retrieved Table {table['number']}")
            
            print(f"\n📋 Complete table details:")
            print(f"   ID: {table['id']}")
            print(f"   Number: {table['number']}")
            print(f"   Capacity: {table['capacity']} seats")
            print(f"   Location: {table['location']} ({table['location_display']})")
            print(f"   Status: {table['status']} ({table['status_display']})")
            print(f"   Is Available: {table['is_available']}")
            print(f"   Is Active: {table['is_active']}")
            print(f"   Description: {table['description']}")
            print(f"   Restaurant: {table['restaurant_name']}")
            print(f"   Created: {table['created_at']}")
            print(f"   Updated: {table['updated_at']}")
                
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"Response: {response.content.decode()}")
            
    except Exception as e:
        print(f"❌ ERROR in table detail test: {str(e)}")
    
    # Test 3: Table Detail API - Non-existent ID
    print(f"\n🧪 Test 3: Table Detail API - Non-existent ID (999)")
    try:
        response = client.get('/PerpexBistro/api/tables/999/')
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 404:
            print("✅ SUCCESS: Correctly returned 404 for non-existent table")
        else:
            print(f"⚠️  Expected 404, got {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR in 404 test: {str(e)}")
    
    # Test 4: Table List with Filters
    print(f"\n🧪 Test 4: Table List API with Filters")
    
    filters = [
        ('?status=available', 'Available tables'),
        ('?capacity=4', 'Tables with 4+ seats'),
        ('?location=outdoor', 'Outdoor tables'),
        ('?active_only=true', 'Active tables only'),
    ]
    
    for filter_param, description in filters:
        try:
            response = client.get(f'/PerpexBistro/api/tables/{filter_param}')
            
            if response.status_code == 200:
                data = response.json()
                filtered_tables = data.get('results', [])
                total_count = data.get('count', 0)
                print(f"✅ {description}: {total_count} tables found")
            else:
                print(f"❌ {description}: Error {response.status_code}")
                
        except Exception as e:
            print(f"❌ {description}: {str(e)}")
    
    print(f"\n🎉 All Table API tests completed!")
    print("\n📌 API Endpoints Available:")
    print("   📋 List all tables: GET /PerpexBistro/api/tables/")
    print("   🔍 Get table details: GET /PerpexBistro/api/tables/<id>/")
    print("   🔧 Filter options: ?status=available&capacity=4&location=outdoor")

if __name__ == "__main__":
    test_table_endpoints()