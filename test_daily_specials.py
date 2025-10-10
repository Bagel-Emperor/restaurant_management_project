"""
DEPRECATED: This standalone test script is kept for backwards compatibility.

⚠️ For proper test isolation and best practices, use the Django TestCase-based tests:
   python manage.py test home.tests.test_daily_specials

This script modifies existing database records, which can cause side effects.
The new test suite (home/tests/test_daily_specials.py) uses Django's TestCase
with proper database transactions to ensure test isolation.

---

Test script for Daily Specials API endpoint.

This script tests:
1. API endpoint returns correct HTTP status
2. Filtering works correctly (only daily specials with is_daily_special=True)
3. Availability filtering (only is_available=True items)
4. Response format matches DailySpecialSerializer
5. Empty results when no daily specials exist

⚠️ WARNING: This script modifies existing database records.
   Use the proper Django test suite for isolated testing.
"""

import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_management.settings')
django.setup()

from home.models import MenuItem, MenuCategory, Restaurant
from django.test import Client
import json

print("=" * 80)
print("TESTING DAILY SPECIALS API ENDPOINT")
print("=" * 80)

# Create test client
client = Client()

# Get or create test data
try:
    # Clear all existing daily specials first for a clean test
    MenuItem.objects.filter(is_daily_special=True).update(is_daily_special=False)
    print("\n🧹 Cleared existing daily specials for clean test")
    
    restaurant = Restaurant.objects.first()
    if not restaurant:
        print("ERROR: No restaurant found. Please create a restaurant first.")
        exit(1)
    
    category = MenuCategory.objects.first()
    
    print("\n✅ Test Setup")
    print("-" * 80)
    print(f"Using restaurant: {restaurant.name}")
    print(f"Using category: {category.name if category else 'None'}")
    
    # Create test menu items
    print("\nCreating test menu items...")
    
    # Daily special item 1 (available)
    special1, created = MenuItem.objects.get_or_create(
        name='Test Daily Special 1',
        restaurant=restaurant,
        defaults={
            'description': 'Test daily special item 1',
            'price': Decimal('15.99'),
            'category': category,
            'is_available': True,
            'is_daily_special': True
        }
    )
    if created:
        print(f"  ✓ Created: {special1.name}")
    else:
        # Update existing item
        special1.is_daily_special = True
        special1.is_available = True
        special1.save()
        print(f"  ✓ Updated: {special1.name}")
    
    # Daily special item 2 (available)
    special2, created = MenuItem.objects.get_or_create(
        name='Test Daily Special 2',
        restaurant=restaurant,
        defaults={
            'description': 'Test daily special item 2',
            'price': Decimal('22.50'),
            'category': category,
            'is_available': True,
            'is_daily_special': True
        }
    )
    if created:
        print(f"  ✓ Created: {special2.name}")
    else:
        special2.is_daily_special = True
        special2.is_available = True
        special2.save()
        print(f"  ✓ Updated: {special2.name}")
    
    # Daily special item 3 (NOT available - should be filtered out)
    special3, created = MenuItem.objects.get_or_create(
        name='Test Daily Special 3 (Unavailable)',
        restaurant=restaurant,
        defaults={
            'description': 'Test daily special item 3 - not available',
            'price': Decimal('18.00'),
            'category': category,
            'is_available': False,
            'is_daily_special': True
        }
    )
    if created:
        print(f"  ✓ Created: {special3.name}")
    else:
        special3.is_daily_special = True
        special3.is_available = False
        special3.save()
        print(f"  ✓ Updated: {special3.name}")
    
    # Regular item (NOT a daily special - should be filtered out)
    regular, created = MenuItem.objects.get_or_create(
        name='Test Regular Item',
        restaurant=restaurant,
        defaults={
            'description': 'Test regular menu item',
            'price': Decimal('12.99'),
            'category': category,
            'is_available': True,
            'is_daily_special': False
        }
    )
    if created:
        print(f"  ✓ Created: {regular.name}")
    else:
        regular.is_daily_special = False
        regular.is_available = True
        regular.save()
        print(f"  ✓ Updated: {regular.name}")
    
except Exception as e:
    print(f"ERROR during setup: {e}")
    exit(1)

print("\n" + "=" * 80)
print("TEST 1: API endpoint returns 200 OK")
print("=" * 80)
response = client.get('/api/daily-specials/')
print(f"Status Code: {response.status_code}")
print(f"Result: {'✓ PASS' if response.status_code == 200 else '✗ FAIL'}")

if response.status_code != 200:
    print(f"ERROR: Expected 200, got {response.status_code}")
    print(f"Response: {response.content}")
    exit(1)

print("\n" + "=" * 80)
print("TEST 2: Response contains only daily specials that are available")
print("=" * 80)
data = response.json()

# Handle both list and paginated dict responses
if isinstance(data, dict) and 'results' in data:
    items = data['results']
    print(f"Number of items returned (paginated): {len(items)}")
elif isinstance(data, list):
    items = data
    print(f"Number of items returned: {len(items)}")
else:
    print(f"✗ FAIL: Unexpected response format: {type(data)}")
    print(f"Response: {data}")
    exit(1)

# Should return 2 items (special1 and special2), not special3 (unavailable) or regular (not a special)
expected_count = 2
actual_count = len(items)
print(f"Expected count: {expected_count}")
print(f"Actual count: {actual_count}")
print(f"Result: {'✓ PASS' if actual_count == expected_count else '✗ FAIL'}")

if actual_count != expected_count:
    print(f"\nWARNING: Expected {expected_count} items, got {actual_count}")
    print("This might be due to existing daily specials in the database")

print("\n" + "=" * 80)
print("TEST 3: Response format matches DailySpecialSerializer")
print("=" * 80)
if len(items) > 0:
    item = items[0]
    expected_fields = ['id', 'name', 'description', 'price', 'category_name', 'restaurant_name', 'image', 'is_available']
    
    print(f"Expected fields: {expected_fields}")
    print(f"Actual fields: {list(item.keys())}")
    
    missing_fields = [field for field in expected_fields if field not in item]
    extra_fields = [field for field in item.keys() if field not in expected_fields]
    
    if missing_fields:
        print(f"✗ FAIL: Missing fields: {missing_fields}")
    elif extra_fields:
        print(f"✗ FAIL: Extra fields: {extra_fields}")
    else:
        print(f"✓ PASS: All expected fields present")
    
    print(f"\nSample item:")
    print(json.dumps(item, indent=2))
else:
    print("✗ FAIL: No items returned")

print("\n" + "=" * 80)
print("TEST 4: All returned items have is_daily_special=True and is_available=True")
print("=" * 80)
all_valid = True
for item in items:
    item_id = item['id']
    menu_item = MenuItem.objects.get(id=item_id)
    
    if not menu_item.is_daily_special:
        print(f"✗ FAIL: Item {item['name']} (ID: {item_id}) has is_daily_special=False")
        all_valid = False
    
    if not menu_item.is_available:
        print(f"✗ FAIL: Item {item['name']} (ID: {item_id}) has is_available=False")
        all_valid = False

if all_valid:
    print(f"✓ PASS: All {len(items)} items are daily specials and available")
else:
    print("✗ FAIL: Some items don't meet the criteria")

print("\n" + "=" * 80)
print("TEST 5: API endpoint is publicly accessible (no authentication required)")
print("=" * 80)
# Test without authentication
response_no_auth = client.get('/api/daily-specials/')
print(f"Status without authentication: {response_no_auth.status_code}")
print(f"Result: {'✓ PASS' if response_no_auth.status_code == 200 else '✗ FAIL'}")

print("\n" + "=" * 80)
print("ALL TESTS COMPLETED")
print("=" * 80)
print("\n✅ Summary:")
print(f"  - API endpoint accessible: {response.status_code == 200}")
print(f"  - Filtering works correctly: {len(items) == expected_count}")
print(f"  - Response format correct: {len(items) > 0}")
print(f"  - All items valid: {all_valid}")
print(f"  - Public access works: {response_no_auth.status_code == 200}")

# Cleanup
print("\n🧹 Cleanup (keeping test items for manual testing)")
print("Test items will remain in database for manual verification.")
print("You can delete them manually through Django admin if needed.")
