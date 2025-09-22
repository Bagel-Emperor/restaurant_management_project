#!/usr/bin/env python3
"""
Test script for Category-based Menu Item API endpoints.
Tests the new category filtering functionality.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8001/PerpexBistro/api"

def test_api_endpoints():
    """Test all category-related API endpoints"""
    
    print("=== Testing Category-based Menu Item API ===\n")
    
    # Test 1: List all menu categories
    print("1. Testing Menu Categories endpoint:")
    print("   GET /api/menu-categories/")
    try:
        response = requests.get(f"{BASE_URL}/menu-categories/")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            categories = response.json()
            print(f"   Found {len(categories)} categories:")
            for cat in categories:
                print(f"     - ID: {cat['id']}, Name: {cat['name']}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {str(e)}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: List all menu items (check if category field is included)
    print("2. Testing Menu Items endpoint (with category data):")
    print("   GET /api/menu-items/")
    try:
        response = requests.get(f"{BASE_URL}/menu-items/")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            menu_items = response.json()
            print(f"   Found {len(menu_items)} menu items:")
            for item in menu_items[:3]:  # Show first 3 items
                category_info = item.get('category_name', 'No category')
                print(f"     - {item['name']} (Category: {category_info})")
            if len(menu_items) > 3:
                print(f"     ... and {len(menu_items) - 3} more items")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {str(e)}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Filter menu items by category ID (if categories exist)
    print("3. Testing Category filtering by ID:")
    print("   GET /api/menu-items/?category=1")
    try:
        response = requests.get(f"{BASE_URL}/menu-items/?category=1")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            filtered_items = response.json()
            print(f"   Found {len(filtered_items)} items in category ID 1:")
            for item in filtered_items:
                category_info = item.get('category_name', 'No category')
                print(f"     - {item['name']} (Category: {category_info})")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {str(e)}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 4: Filter menu items by category name
    print("4. Testing Category filtering by name:")
    print("   GET /api/menu-items/?category=appetizers")
    try:
        response = requests.get(f"{BASE_URL}/menu-items/?category=appetizers")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            filtered_items = response.json()
            print(f"   Found {len(filtered_items)} items matching 'appetizers':")
            for item in filtered_items:
                category_info = item.get('category_name', 'No category')
                print(f"     - {item['name']} (Category: {category_info})")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {str(e)}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 5: Test combined filtering (category + availability)
    print("5. Testing Combined filtering (category + availability):")
    print("   GET /api/menu-items/?category=1&available=true")
    try:
        response = requests.get(f"{BASE_URL}/menu-items/?category=1&available=true")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            filtered_items = response.json()
            print(f"   Found {len(filtered_items)} available items in category 1:")
            for item in filtered_items:
                category_info = item.get('category_name', 'No category')
                availability = "Available" if item['is_available'] else "Unavailable"
                print(f"     - {item['name']} (Category: {category_info}, {availability})")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {str(e)}")
    
    print("\n" + "="*50 + "\n")
    print("API testing completed!")

if __name__ == "__main__":
    test_api_endpoints()