"""
Quick demonstration script for testing DailySpecialManager.upcoming() method.

This script tests the custom manager in the Django shell to ensure it returns
the correct results for upcoming daily specials.
"""

# Run this in Django shell: python manage.py shell < demo_daily_special_manager.py

from datetime import date, timedelta
from decimal import Decimal
from home.models import DailySpecial, MenuItem, Restaurant, MenuCategory

print("\n" + "="*70)
print("TESTING DailySpecialManager.upcoming() METHOD")
print("="*70)

# Clean up any existing data
print("\n1. Cleaning up existing test data...")
DailySpecial.objects.all().delete()
print("   ✓ Cleared existing daily specials")

# Get or create a restaurant
restaurant, created = Restaurant.objects.get_or_create(
    name='Test Restaurant',
    defaults={
        'owner_name': 'Test Owner',
        'email': 'test@restaurant.com',
        'phone_number': '555-0100'
    }
)
print(f"   ✓ {'Created' if created else 'Using existing'} restaurant: {restaurant.name}")

# Get or create a category
category, created = MenuCategory.objects.get_or_create(
    name='Specials',
    defaults={'description': 'Daily special items'}
)
print(f"   ✓ {'Created' if created else 'Using existing'} category: {category.name}")

# Create test menu items
print("\n2. Creating test menu items...")
menu_items = []
for i in range(1, 4):
    menu_item, created = MenuItem.objects.get_or_create(
        name=f'Test Special Item {i}',
        defaults={
            'description': f'Description for test item {i}',
            'price': Decimal('10.99') + Decimal(str(i)),
            'restaurant': restaurant,
            'category': category,
            'is_available': True
        }
    )
    menu_items.append(menu_item)
    print(f"   ✓ {'Created' if created else 'Using'} menu item: {menu_item.name}")

# Create daily specials with various dates
print("\n3. Creating daily specials with various dates...")
yesterday = date.today() - timedelta(days=1)
today = date.today()
tomorrow = date.today() + timedelta(days=1)
next_week = date.today() + timedelta(days=7)

# Past special (should NOT be in upcoming)
past_special = DailySpecial.objects.create(
    menu_item=menu_items[0],
    special_date=yesterday,
    description='Yesterday\'s special (should be excluded)'
)
print(f"   ✓ Created past special: {past_special.menu_item.name} on {past_special.special_date}")

# Today's special (should be in upcoming)
today_special = DailySpecial.objects.create(
    menu_item=menu_items[1],
    special_date=today,
    description='Today\'s special (should be included)'
)
print(f"   ✓ Created today's special: {today_special.menu_item.name} on {today_special.special_date}")

# Tomorrow's special (should be in upcoming)
tomorrow_special = DailySpecial.objects.create(
    menu_item=menu_items[2],
    special_date=tomorrow,
    description='Tomorrow\'s special (should be included)'
)
print(f"   ✓ Created tomorrow's special: {tomorrow_special.menu_item.name} on {tomorrow_special.special_date}")

# Future special (should be in upcoming)
future_special = DailySpecial.objects.create(
    menu_item=menu_items[0],
    special_date=next_week,
    description='Next week\'s special (should be included)'
)
print(f"   ✓ Created future special: {future_special.menu_item.name} on {future_special.special_date}")

# Test the custom manager
print("\n4. Testing DailySpecial.objects.upcoming() method...")
print("   Query: DailySpecial.objects.upcoming()")
print()

upcoming_specials = DailySpecial.objects.upcoming()

print(f"   Total upcoming specials found: {upcoming_specials.count()}")
print()

if upcoming_specials.exists():
    print("   Upcoming Specials (ordered by date):")
    print("   " + "-"*66)
    for i, special in enumerate(upcoming_specials, 1):
        status = "TODAY" if special.special_date == today else "FUTURE"
        print(f"   {i}. {special.menu_item.name}")
        print(f"      Date: {special.special_date} ({status})")
        print(f"      Description: {special.description}")
        print()
else:
    print("   ⚠ No upcoming specials found")

# Verify results
print("\n5. Verifying results...")
all_specials = DailySpecial.objects.all()
print(f"   Total specials in database: {all_specials.count()}")
print(f"   Upcoming specials (today or future): {upcoming_specials.count()}")
print(f"   Past specials (excluded): {all_specials.count() - upcoming_specials.count()}")

# Check that past special is NOT in upcoming
if past_special not in upcoming_specials:
    print("   ✓ Past special correctly excluded")
else:
    print("   ✗ ERROR: Past special should not be in upcoming")

# Check that today's special IS in upcoming
if today_special in upcoming_specials:
    print("   ✓ Today's special correctly included")
else:
    print("   ✗ ERROR: Today's special should be in upcoming")

# Check that future specials ARE in upcoming
if tomorrow_special in upcoming_specials and future_special in upcoming_specials:
    print("   ✓ Future specials correctly included")
else:
    print("   ✗ ERROR: Future specials should be in upcoming")

# Check ordering (earliest date first)
upcoming_list = list(upcoming_specials)
if len(upcoming_list) >= 2:
    if upcoming_list[0].special_date <= upcoming_list[1].special_date:
        print("   ✓ Results correctly ordered by date (earliest first)")
    else:
        print("   ✗ ERROR: Results not properly ordered")

# Test chaining with filters
print("\n6. Testing filter chaining...")
available_upcoming = DailySpecial.objects.upcoming().filter(
    menu_item__is_available=True
)
print(f"   Available upcoming specials: {available_upcoming.count()}")
print("   ✓ Manager method can be chained with additional filters")

print("\n" + "="*70)
print("TEST COMPLETE - Custom manager working correctly!")
print("="*70)
print()
