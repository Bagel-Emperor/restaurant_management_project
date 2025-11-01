"""
Test cases for DailySpecialManager custom manager.

This test module provides comprehensive coverage for the DailySpecial model's
custom manager, specifically testing the upcoming() method that filters specials
to show only today's and future dates.
"""

from django.test import TestCase
from datetime import date, timedelta
from home.models import DailySpecial, MenuItem, Restaurant, MenuCategory
from decimal import Decimal


class DailySpecialManagerUpcomingTests(TestCase):
	"""Test cases for the DailySpecialManager.upcoming() method."""
	
	def setUp(self):
		"""Set up test data with restaurant, category, and menu items."""
		# Create a restaurant
		self.restaurant = Restaurant.objects.create(
			name='Test Restaurant',
			owner_name='Test Owner',
			email='test@restaurant.com',
			phone_number='555-0100'
		)
		
		# Create a menu category
		self.category = MenuCategory.objects.create(
			name='Specials',
			description='Daily special items'
		)
		
		# Create menu items for testing
		self.menu_item_1 = MenuItem.objects.create(
			name='Special Pasta',
			description='Delicious pasta special',
			price=Decimal('12.99'),
			restaurant=self.restaurant,
			category=self.category,
			is_available=True
		)
		
		self.menu_item_2 = MenuItem.objects.create(
			name='Special Steak',
			description='Premium steak special',
			price=Decimal('24.99'),
			restaurant=self.restaurant,
			category=self.category,
			is_available=True
		)
		
		self.menu_item_3 = MenuItem.objects.create(
			name='Special Salad',
			description='Fresh salad special',
			price=Decimal('8.99'),
			restaurant=self.restaurant,
			category=self.category,
			is_available=False  # Unavailable item
		)
	
	def test_upcoming_returns_today_special(self):
		"""Test that upcoming() returns a special scheduled for today."""
		today = date.today()
		
		special = DailySpecial.objects.create(
			menu_item=self.menu_item_1,
			special_date=today,
			description='Today\'s special!'
		)
		
		upcoming_specials = DailySpecial.objects.upcoming()
		
		self.assertEqual(upcoming_specials.count(), 1)
		self.assertEqual(upcoming_specials.first(), special)
	
	def test_upcoming_returns_future_specials(self):
		"""Test that upcoming() returns specials scheduled for future dates."""
		tomorrow = date.today() + timedelta(days=1)
		next_week = date.today() + timedelta(days=7)
		
		special_tomorrow = DailySpecial.objects.create(
			menu_item=self.menu_item_1,
			special_date=tomorrow,
			description='Tomorrow\'s special'
		)
		
		special_next_week = DailySpecial.objects.create(
			menu_item=self.menu_item_2,
			special_date=next_week,
			description='Next week\'s special'
		)
		
		upcoming_specials = DailySpecial.objects.upcoming()
		
		self.assertEqual(upcoming_specials.count(), 2)
		self.assertIn(special_tomorrow, upcoming_specials)
		self.assertIn(special_next_week, upcoming_specials)
	
	def test_upcoming_excludes_past_specials(self):
		"""Test that upcoming() does not return specials from past dates."""
		yesterday = date.today() - timedelta(days=1)
		last_week = date.today() - timedelta(days=7)
		
		# Create past specials
		DailySpecial.objects.create(
			menu_item=self.menu_item_1,
			special_date=yesterday,
			description='Yesterday\'s special'
		)
		
		DailySpecial.objects.create(
			menu_item=self.menu_item_2,
			special_date=last_week,
			description='Last week\'s special'
		)
		
		upcoming_specials = DailySpecial.objects.upcoming()
		
		self.assertEqual(upcoming_specials.count(), 0)
	
	def test_upcoming_mixed_dates(self):
		"""Test upcoming() with a mix of past, present, and future specials."""
		yesterday = date.today() - timedelta(days=1)
		today = date.today()
		tomorrow = date.today() + timedelta(days=1)
		
		# Past special (should be excluded)
		DailySpecial.objects.create(
			menu_item=self.menu_item_1,
			special_date=yesterday,
			description='Past special'
		)
		
		# Today's special (should be included)
		today_special = DailySpecial.objects.create(
			menu_item=self.menu_item_2,
			special_date=today,
			description='Today\'s special'
		)
		
		# Future special (should be included)
		future_special = DailySpecial.objects.create(
			menu_item=self.menu_item_3,
			special_date=tomorrow,
			description='Future special'
		)
		
		upcoming_specials = DailySpecial.objects.upcoming()
		
		self.assertEqual(upcoming_specials.count(), 2)
		self.assertIn(today_special, upcoming_specials)
		self.assertIn(future_special, upcoming_specials)
	
	def test_upcoming_ordering(self):
		"""Test that upcoming() returns specials ordered by date (earliest first)."""
		today = date.today()
		in_3_days = today + timedelta(days=3)
		in_1_day = today + timedelta(days=1)
		in_7_days = today + timedelta(days=7)
		
		# Create specials in non-chronological order
		special_3 = DailySpecial.objects.create(
			menu_item=self.menu_item_1,
			special_date=in_3_days,
			description='3 days from now'
		)
		
		special_1 = DailySpecial.objects.create(
			menu_item=self.menu_item_2,
			special_date=in_1_day,
			description='1 day from now'
		)
		
		special_7 = DailySpecial.objects.create(
			menu_item=self.menu_item_3,
			special_date=in_7_days,
			description='7 days from now'
		)
		
		upcoming_specials = list(DailySpecial.objects.upcoming())
		
		# Check ordering: should be 1 day, 3 days, 7 days
		self.assertEqual(upcoming_specials[0], special_1)
		self.assertEqual(upcoming_specials[1], special_3)
		self.assertEqual(upcoming_specials[2], special_7)
	
	def test_upcoming_empty_queryset(self):
		"""Test that upcoming() returns an empty queryset when no specials exist."""
		upcoming_specials = DailySpecial.objects.upcoming()
		
		self.assertEqual(upcoming_specials.count(), 0)
		self.assertFalse(upcoming_specials.exists())
	
	def test_upcoming_only_past_specials(self):
		"""Test upcoming() returns empty queryset when only past specials exist."""
		last_week = date.today() - timedelta(days=7)
		yesterday = date.today() - timedelta(days=1)
		
		DailySpecial.objects.create(
			menu_item=self.menu_item_1,
			special_date=last_week
		)
		
		DailySpecial.objects.create(
			menu_item=self.menu_item_2,
			special_date=yesterday
		)
		
		upcoming_specials = DailySpecial.objects.upcoming()
		
		self.assertEqual(upcoming_specials.count(), 0)
	
	def test_upcoming_can_be_chained_with_filters(self):
		"""Test that upcoming() returns a queryset that can be chained with other filters."""
		today = date.today()
		tomorrow = date.today() + timedelta(days=1)
		
		# Create specials with available and unavailable menu items
		available_special = DailySpecial.objects.create(
			menu_item=self.menu_item_1,  # is_available=True
			special_date=today,
			description='Available special'
		)
		
		DailySpecial.objects.create(
			menu_item=self.menu_item_3,  # is_available=False
			special_date=tomorrow,
			description='Unavailable special'
		)
		
		# Chain filter to get only available upcoming specials
		available_upcoming = DailySpecial.objects.upcoming().filter(
			menu_item__is_available=True
		)
		
		self.assertEqual(available_upcoming.count(), 1)
		self.assertEqual(available_upcoming.first(), available_special)
	
	def test_upcoming_with_same_date_multiple_items(self):
		"""Test upcoming() handles multiple specials on the same date."""
		tomorrow = date.today() + timedelta(days=1)
		
		special_1 = DailySpecial.objects.create(
			menu_item=self.menu_item_1,
			special_date=tomorrow,
			description='Special 1'
		)
		
		special_2 = DailySpecial.objects.create(
			menu_item=self.menu_item_2,
			special_date=tomorrow,
			description='Special 2'
		)
		
		upcoming_specials = DailySpecial.objects.upcoming()
		
		self.assertEqual(upcoming_specials.count(), 2)
		self.assertIn(special_1, upcoming_specials)
		self.assertIn(special_2, upcoming_specials)


class DailySpecialModelTests(TestCase):
	"""Test cases for DailySpecial model functionality."""
	
	def setUp(self):
		"""Set up test data."""
		self.restaurant = Restaurant.objects.create(
			name='Test Restaurant',
			owner_name='Test Owner',
			email='test@restaurant.com',
			phone_number='555-0100'
		)
		
		self.category = MenuCategory.objects.create(
			name='Specials',
			description='Special items'
		)
		
		self.menu_item = MenuItem.objects.create(
			name='Test Special',
			description='Test description',
			price=Decimal('15.99'),
			restaurant=self.restaurant,
			category=self.category
		)
	
	def test_create_daily_special(self):
		"""Test creating a DailySpecial instance."""
		today = date.today()
		
		special = DailySpecial.objects.create(
			menu_item=self.menu_item,
			special_date=today,
			description='Today\'s special offer'
		)
		
		self.assertEqual(special.menu_item, self.menu_item)
		self.assertEqual(special.special_date, today)
		self.assertEqual(special.description, 'Today\'s special offer')
		self.assertIsNotNone(special.created_at)
		self.assertIsNotNone(special.updated_at)
	
	def test_daily_special_str_representation(self):
		"""Test the string representation of DailySpecial."""
		today = date.today()
		
		special = DailySpecial.objects.create(
			menu_item=self.menu_item,
			special_date=today
		)
		
		expected_str = f"{self.menu_item.name} on {today}"
		self.assertEqual(str(special), expected_str)
	
	def test_daily_special_unique_together_constraint(self):
		"""Test that a menu item can only be special once per date."""
		today = date.today()
		
		# Create first special
		DailySpecial.objects.create(
			menu_item=self.menu_item,
			special_date=today,
			description='First special'
		)
		
		# Try to create duplicate - should raise IntegrityError
		from django.db import IntegrityError
		with self.assertRaises(IntegrityError):
			DailySpecial.objects.create(
				menu_item=self.menu_item,
				special_date=today,
				description='Duplicate special'
			)
	
	def test_daily_special_optional_description(self):
		"""Test that description field is optional."""
		today = date.today()
		
		special = DailySpecial.objects.create(
			menu_item=self.menu_item,
			special_date=today
			# No description provided
		)
		
		self.assertEqual(special.description, '')
	
	def test_is_upcoming_method_for_today(self):
		"""Test is_upcoming() returns True for today's special."""
		today = date.today()
		
		special = DailySpecial.objects.create(
			menu_item=self.menu_item,
			special_date=today
		)
		
		self.assertTrue(special.is_upcoming())
	
	def test_is_upcoming_method_for_future(self):
		"""Test is_upcoming() returns True for future special."""
		tomorrow = date.today() + timedelta(days=1)
		
		special = DailySpecial.objects.create(
			menu_item=self.menu_item,
			special_date=tomorrow
		)
		
		self.assertTrue(special.is_upcoming())
	
	def test_is_upcoming_method_for_past(self):
		"""Test is_upcoming() returns False for past special."""
		yesterday = date.today() - timedelta(days=1)
		
		special = DailySpecial.objects.create(
			menu_item=self.menu_item,
			special_date=yesterday
		)
		
		self.assertFalse(special.is_upcoming())
	
	def test_daily_special_cascade_delete(self):
		"""Test that DailySpecial is deleted when menu item is deleted."""
		today = date.today()
		
		special = DailySpecial.objects.create(
			menu_item=self.menu_item,
			special_date=today
		)
		
		special_id = special.id
		
		# Delete the menu item
		self.menu_item.delete()
		
		# Verify the special was also deleted
		with self.assertRaises(DailySpecial.DoesNotExist):
			DailySpecial.objects.get(id=special_id)
	
	def test_menu_item_can_have_multiple_specials_different_dates(self):
		"""Test that a menu item can be a special on different dates."""
		today = date.today()
		tomorrow = date.today() + timedelta(days=1)
		
		special_today = DailySpecial.objects.create(
			menu_item=self.menu_item,
			special_date=today,
			description='Today\'s special'
		)
		
		special_tomorrow = DailySpecial.objects.create(
			menu_item=self.menu_item,
			special_date=tomorrow,
			description='Tomorrow\'s special'
		)
		
		# Verify both specials exist
		specials = DailySpecial.objects.filter(menu_item=self.menu_item)
		self.assertEqual(specials.count(), 2)
		self.assertIn(special_today, specials)
		self.assertIn(special_tomorrow, specials)
	
	def test_daily_special_related_name(self):
		"""Test accessing daily specials through menu item's related name."""
		today = date.today()
		tomorrow = date.today() + timedelta(days=1)
		
		DailySpecial.objects.create(
			menu_item=self.menu_item,
			special_date=today
		)
		
		DailySpecial.objects.create(
			menu_item=self.menu_item,
			special_date=tomorrow
		)
		
		# Access through related name
		specials = self.menu_item.daily_specials.all()
		
		self.assertEqual(specials.count(), 2)
	
	def test_daily_special_ordering(self):
		"""Test that DailySpecial model has default ordering by special_date."""
		today = date.today()
		in_3_days = today + timedelta(days=3)
		tomorrow = today + timedelta(days=1)
		
		# Create in non-chronological order
		special_3 = DailySpecial.objects.create(
			menu_item=self.menu_item,
			special_date=in_3_days
		)
		
		special_1 = DailySpecial.objects.create(
			menu_item=self.menu_item,
			special_date=tomorrow
		)
		
		# Create another menu item for today
		menu_item_2 = MenuItem.objects.create(
			name='Another Special',
			price=Decimal('10.99'),
			restaurant=self.restaurant
		)
		
		special_today = DailySpecial.objects.create(
			menu_item=menu_item_2,
			special_date=today
		)
		
		# Get all specials - should be ordered by date
		all_specials = list(DailySpecial.objects.all())
		
		self.assertEqual(all_specials[0], special_today)  # Today first
		self.assertEqual(all_specials[1], special_1)      # Tomorrow second
		self.assertEqual(all_specials[2], special_3)      # 3 days last
	
	def test_updated_at_changes_on_save(self):
		"""Test that updated_at timestamp changes when special is modified."""
		import time
		today = date.today()
		
		special = DailySpecial.objects.create(
			menu_item=self.menu_item,
			special_date=today,
			description='Original description'
		)
		
		original_updated_at = special.updated_at
		
		# Wait a moment and update
		time.sleep(0.01)
		special.description = 'Updated description'
		special.save()
		
		# Refresh from database
		special.refresh_from_db()
		
		self.assertGreater(special.updated_at, original_updated_at)
