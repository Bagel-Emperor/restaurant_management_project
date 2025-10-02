#!/usr/bin/env python
"""
Test script for Table API endpoints.
"""
import requests
import json

BASE_URL = 'http://127.0.0.1:8000'

def test_table_list_api():
    """Test the table list API endpoint."""
    print("🧪 Testing Table List API...")
    
    try:
        response = requests.get(f'{BASE_URL}/api/tables/')
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            tables = response.json()
            print(f"✅ SUCCESS: Found {len(tables)} tables")
            
            # Print first table as example
            if tables:
                print("\n📋 Sample table data:")
                print(json.dumps(tables[0], indent=2))
            
            return tables
        else:
            print(f"❌ ERROR: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to server. Make sure Django is running on port 8000")
        return None
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None

def test_table_detail_api(table_id=1):
    """Test the table detail API endpoint."""
    print(f"\n🧪 Testing Table Detail API for table ID {table_id}...")
    
    try:
        response = requests.get(f'{BASE_URL}/api/tables/{table_id}/')
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            table = response.json()
            print(f"✅ SUCCESS: Retrieved table {table['number']}")
            print("\n📋 Table details:")
            print(json.dumps(table, indent=2))
            return table
        elif response.status_code == 404:
            print(f"❌ Table with ID {table_id} not found")
            return None
        else:
            print(f"❌ ERROR: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to server. Make sure Django is running on port 8000")
        return None
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None

def test_table_filtering():
    """Test table filtering parameters."""
    print("\n🧪 Testing Table List API with filters...")
    
    filters = [
        ('status=available', 'Available tables only'),
        ('capacity=4', 'Tables with 4+ capacity'),
        ('location=outdoor', 'Outdoor tables only'),
        ('active_only=true', 'Active tables only'),
    ]
    
    for filter_param, description in filters:
        try:
            response = requests.get(f'{BASE_URL}/api/tables/?{filter_param}')
            
            if response.status_code == 200:
                tables = response.json()
                print(f"✅ {description}: {len(tables)} tables found")
            else:
                print(f"❌ {description}: Error {response.status_code}")
                
        except Exception as e:
            print(f"❌ {description}: {str(e)}")

def main():
    """Run all table API tests."""
    print("🚀 Starting Table API Tests")
    print("=" * 50)
    
    # Test list endpoint
    tables = test_table_list_api()
    
    # Test detail endpoint
    if tables:
        # Test with first table's ID
        first_table_id = tables[0]['id']
        test_table_detail_api(first_table_id)
        
        # Test with non-existent ID
        test_table_detail_api(999)
    else:
        # Fallback test with ID 1
        test_table_detail_api(1)
    
    # Test filtering
    test_table_filtering()
    
    print("\n🎉 Table API tests completed!")

if __name__ == "__main__":
    main()