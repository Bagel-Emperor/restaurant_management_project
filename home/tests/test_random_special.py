"""
Django TestCase for MenuItem.objects.get_random_special() method.

This test suite validates the random daily special functionality including:
1. Method existence and availability
2. Returns MenuItem instance or None
3. Only returns items with is_daily_special=True
4. Only returns available items (is_available=True)
5. Handles empty database and no specials gracefully
6. Randomness behavior (statistical validation)

Run with: python manage.py test home.tests.test_random_special
"""

from django.test import TestCase
from decimal import Decimal

from home.models import MenuItem, MenuCategory, Restaurant


class RandomSpecialMethodTests(TestCase):
    """Test cases for the get_random_special() manager method."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all test methods."""
        # Create test restaurant
        cls.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner_name='Test Owner',
            email='restaurant@test.com',
            phone_number='555-0100',
            opening_hours={'Monday': '9am-10pm'}
        )
        
        # Create test category
        cls.category = MenuCategory.objects.create(
            name='Specials',
            description='Daily special items'
        )
    
    def test_method_exists(self):
        """Test that get_random_special method exists on MenuItem manager."""
        self.assertTrue(hasattr(MenuItem.objects, 'get_random_special'))
        self.assertTrue(callable(MenuItem.objects.get_random_special))
    
    def test_returns_none_when_no_items(self):
        """Test that method returns None when no menu items exist."""
        result = MenuItem.objects.get_random_special()
        self.assertIsNone(result)
    
    def test_returns_none_when_no_daily_specials(self):
        """Test that method returns None when no daily specials exist."""
        # Create regular items (not daily specials)
        MenuItem.objects.create(
            name='Regular Burger',
            price=Decimal('10.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_daily_special=False,
            is_available=True
        )
        
        MenuItem.objects.create(
            name='Regular Pizza',
            price=Decimal('12.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_daily_special=False,
            is_available=True
        )
        
        result = MenuItem.objects.get_random_special()
        self.assertIsNone(result)
    
    def test_returns_menuitem_instance(self):
        """Test that method returns a MenuItem instance when specials exist."""
        MenuItem.objects.create(
            name='Daily Special Pasta',
            price=Decimal('15.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_daily_special=True,
            is_available=True
        )
        
        result = MenuItem.objects.get_random_special()
        self.assertIsNotNone(result)
        self.assertIsInstance(result, MenuItem)
    
    def test_returns_only_daily_specials(self):
        """Test that method only returns items with is_daily_special=True."""
        # Create mix of items
        special = MenuItem.objects.create(
            name='Daily Special Steak',
            price=Decimal('25.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_daily_special=True,
            is_available=True
        )
        
        regular = MenuItem.objects.create(
            name='Regular Salad',
            price=Decimal('8.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_daily_special=False,
            is_available=True
        )
        
        # Call method multiple times to ensure it never returns regular item
        for _ in range(10):
            result = MenuItem.objects.get_random_special()
            self.assertIsNotNone(result)
            self.assertEqual(result.id, special.id)
            self.assertNotEqual(result.id, regular.id)
    
    def test_returns_only_available_items(self):
        """Test that method only returns items with is_available=True."""
        # Create available special
        available_special = MenuItem.objects.create(
            name='Available Special',
            price=Decimal('18.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_daily_special=True,
            is_available=True
        )
        
        # Create unavailable special
        unavailable_special = MenuItem.objects.create(
            name='Unavailable Special',
            price=Decimal('22.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_daily_special=True,
            is_available=False
        )
        
        # Call method multiple times to ensure it never returns unavailable item
        for _ in range(10):
            result = MenuItem.objects.get_random_special()
            self.assertIsNotNone(result)
            self.assertEqual(result.id, available_special.id)
            self.assertNotEqual(result.id, unavailable_special.id)
    
    def test_returns_none_when_all_specials_unavailable(self):
        """Test that method returns None when all daily specials are unavailable."""
        # Create only unavailable specials
        MenuItem.objects.create(
            name='Unavailable Special 1',
            price=Decimal('15.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_daily_special=True,
            is_available=False
        )
        
        MenuItem.objects.create(
            name='Unavailable Special 2',
            price=Decimal('18.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_daily_special=True,
            is_available=False
        )
        
        result = MenuItem.objects.get_random_special()
        self.assertIsNone(result)
    
    def test_returns_single_item_not_queryset(self):
        """Test that method returns a single MenuItem, not a QuerySet."""
        MenuItem.objects.create(
            name='Daily Special',
            price=Decimal('16.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_daily_special=True,
            is_available=True
        )
        
        result = MenuItem.objects.get_random_special()
        self.assertIsNotNone(result)
        # Should be a MenuItem instance, not QuerySet
        self.assertIsInstance(result, MenuItem)
        self.assertFalse(hasattr(result, 'count'))  # QuerySets have count()
    
    def test_randomness_with_multiple_specials(self):
        """Test that method returns different items when multiple specials exist."""
        # Create 3 daily specials
        special1 = MenuItem.objects.create(
            name='Special 1',
            price=Decimal('15.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_daily_special=True,
            is_available=True
        )
        
        special2 = MenuItem.objects.create(
            name='Special 2',
            price=Decimal('17.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_daily_special=True,
            is_available=True
        )
        
        special3 = MenuItem.objects.create(
            name='Special 3',
            price=Decimal('19.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_daily_special=True,
            is_available=True
        )
        
        # Call method 30 times and collect results
        results = []
        for _ in range(30):
            result = MenuItem.objects.get_random_special()
            self.assertIsNotNone(result)
            results.append(result.id)
        
        # Check that we got at least 2 different items (statistical test)
        # With 3 items and 30 calls, probability of getting only 1 item is extremely low
        unique_items = set(results)
        self.assertGreaterEqual(len(unique_items), 2,
                                "Random selection should return different items over multiple calls")
    
    def test_all_returned_items_are_valid(self):
        """Test that all returned items meet the criteria over multiple calls."""
        # Create mix of items
        MenuItem.objects.create(
            name='Valid Special 1',
            price=Decimal('15.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_daily_special=True,
            is_available=True
        )
        
        MenuItem.objects.create(
            name='Valid Special 2',
            price=Decimal('17.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_daily_special=True,
            is_available=True
        )
        
        MenuItem.objects.create(
            name='Invalid - Not Special',
            price=Decimal('10.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_daily_special=False,
            is_available=True
        )
        
        MenuItem.objects.create(
            name='Invalid - Unavailable',
            price=Decimal('20.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_daily_special=True,
            is_available=False
        )
        
        # Call method 20 times
        for _ in range(20):
            result = MenuItem.objects.get_random_special()
            self.assertIsNotNone(result)
            # Verify it's a valid daily special
            self.assertTrue(result.is_daily_special)
            self.assertTrue(result.is_available)
            # Verify it's one of the valid specials
            self.assertIn(result.name, ['Valid Special 1', 'Valid Special 2'])
    
    def test_works_with_single_special(self):
        """Test that method works correctly when only one special exists."""
        special = MenuItem.objects.create(
            name='Only Special',
            price=Decimal('14.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_daily_special=True,
            is_available=True
        )
        
        # Call multiple times - should always return the same item
        for _ in range(5):
            result = MenuItem.objects.get_random_special()
            self.assertIsNotNone(result)
            self.assertEqual(result.id, special.id)
            self.assertEqual(result.name, 'Only Special')


if __name__ == '__main__':
    print("=" * 80)
    print("RANDOM DAILY SPECIAL TEST SUITE")
    print("=" * 80)
    print("\nRun with: python manage.py test home.tests.test_random_special")
    print("\nThis test suite covers:")
    print("  ✓ Method existence and availability")
    print("  ✓ Return type validation (MenuItem or None)")
    print("  ✓ Filtering by is_daily_special=True")
    print("  ✓ Filtering by is_available=True")
    print("  ✓ Edge cases (empty DB, no specials, all unavailable)")
    print("  ✓ Randomness validation with multiple specials")
    print("  ✓ Single special handling")
    print("=" * 80)
