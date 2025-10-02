#!/usr/bin/env python
"""
Simple debug test for Table API.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_management.settings')
django.setup()

from django.test import Client

def debug_table_api():
    """Debug the table API response."""
    print("🧪 Debugging Table API...")
    
    client = Client()
    response = client.get('/PerpexBistro/api/tables/')
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Type: {type(response.json() if response.status_code == 200 else 'Not JSON')}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response Data: {data}")
        print(f"Data Type: {type(data)}")
        print(f"Length: {len(data) if hasattr(data, '__len__') else 'No length'}")
        
        if hasattr(data, '__len__') and len(data) > 0:
            print(f"First item: {data[0]}")
        
    else:
        print(f"Error Response: {response.content.decode()[:200]}...")

if __name__ == "__main__":
    debug_table_api()