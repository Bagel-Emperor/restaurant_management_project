#!/usr/bin/env python3
"""
Daily Sales Total Utility - Usage Examples

This script demonstrates how to use the get_daily_sales_total utility function
to calculate restaurant revenue for specific dates.
"""

import os
import sys
from datetime import date, timedelta
from decimal import Decimal

import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant_management.settings')
django.setup()

from orders.utils import get_daily_sales_total


def demo_daily_sales_utility():
    """Demonstrate the get_daily_sales_total utility function."""
    
    print("📊 Daily Sales Total Utility - Usage Examples")
    print("=" * 55)
    
    # Example 1: Get today's sales
    print("\n1️⃣ Today's Sales Total")
    print("-" * 25)
    
    today = date.today()
    today_sales = get_daily_sales_total(today)
    
    print(f"Date: {today}")
    print(f"Sales Total: ${today_sales}")
    print(f"Data Type: {type(today_sales).__name__}")
    
    # Example 2: Get yesterday's sales
    print("\n2️⃣ Yesterday's Sales Total")
    print("-" * 27)
    
    yesterday = today - timedelta(days=1)
    yesterday_sales = get_daily_sales_total(yesterday)
    
    print(f"Date: {yesterday}")
    print(f"Sales Total: ${yesterday_sales}")
    
    # Example 3: Get sales for a specific date
    print("\n3️⃣ Specific Date Sales")
    print("-" * 23)
    
    specific_date = date(2025, 10, 1)  # October 1, 2025
    specific_sales = get_daily_sales_total(specific_date)
    
    print(f"Date: {specific_date}")
    print(f"Sales Total: ${specific_sales}")
    
    # Example 4: Weekly sales comparison
    print("\n4️⃣ Weekly Sales Comparison")
    print("-" * 27)
    
    weekly_total = Decimal('0.00')
    
    for i in range(7):
        check_date = today - timedelta(days=i)
        daily_sales = get_daily_sales_total(check_date)
        weekly_total += daily_sales
        
        day_name = check_date.strftime("%A")
        print(f"{day_name:>9} ({check_date}): ${daily_sales:>8}")
    
    print("-" * 35)
    print(f"{'Weekly Total':>23}: ${weekly_total:>8}")
    
    # Example 5: Usage in business logic
    print("\n5️⃣ Business Logic Example")
    print("-" * 26)
    
    # Calculate if today's sales meet the daily target
    daily_target = Decimal('500.00')  # $500 daily target
    
    if today_sales >= daily_target:
        percentage = (today_sales / daily_target) * 100
        print(f"🎉 Target EXCEEDED! ({percentage:.1f}% of target)")
    else:
        remaining = daily_target - today_sales
        percentage = (today_sales / daily_target) * 100
        print(f"📈 Target Progress: {percentage:.1f}% (${remaining} remaining)")
    
    print(f"Daily Target: ${daily_target}")
    print(f"Actual Sales: ${today_sales}")
    
    # Example 6: Integration with existing order system
    print("\n6️⃣ Integration Notes")
    print("-" * 19)
    
    print("✅ Works with existing Order model")
    print("✅ Includes all order statuses (pending, completed, cancelled)")
    print("✅ Supports both user and guest orders") 
    print("✅ Uses efficient database aggregation")
    print("✅ Returns Decimal for financial precision")
    print("✅ Handles timezone-aware date filtering")
    
    print(f"\n📝 Usage in your code:")
    print("   from orders.utils import get_daily_sales_total")
    print("   from datetime import date")
    print("   ")
    print("   today_revenue = get_daily_sales_total(date.today())")
    print("   print(f'Today\\'s revenue: ${today_revenue}')")


if __name__ == '__main__':
    demo_daily_sales_utility()