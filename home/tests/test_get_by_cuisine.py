"""
Comprehensive tests for MenuItem.get_by_cuisine() model method.

Tests the classmethod that filters menu items by cuisine type (category name).
"""
from django.test import TestCase
from decimal import Decimal
from home.models import MenuItem, MenuCategory, Restaurant


class MenuItemGetByCuisineTests(TestCase):
    """Test suite for MenuItem.get_by_cuisine() classmethod."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all test methods."""
        # Create a restaurant
        cls.restaurant = Restaurant.objects.create(
            name="Test Restaurant",
            owner_name="Test Owner",
            email="test@restaurant.com",
            phone_number="555-1234"
        )
        
        # Create multiple categories/cuisines
        cls.italian = MenuCategory.objects.create(
            name="Italian",
            description="Italian cuisine"
        )
        cls.chinese = MenuCategory.objects.create(
            name="Chinese",
            description="Chinese cuisine"
        )
        cls.desserts = MenuCategory.objects.create(
            name="Desserts",
            description="Dessert items"
        )
        cls.appetizers = MenuCategory.objects.create(
            name="Appetizers",
            description="Starter items"
        )
        
        # Create Italian items
        cls.pasta = MenuItem.objects.create(
            name="Spaghetti Carbonara",
            description="Classic Italian pasta",
            price=Decimal('15.99'),
            restaurant=cls.restaurant,
            category=cls.italian,
            is_available=True
        )
        cls.pizza = MenuItem.objects.create(
            name="Margherita Pizza",
            description="Traditional Italian pizza",
            price=Decimal('12.99'),
            restaurant=cls.restaurant,
            category=cls.italian,
            is_available=True
        )
        cls.risotto = MenuItem.objects.create(
            name="Mushroom Risotto",
            description="Creamy Italian risotto",
            price=Decimal('14.50'),
            restaurant=cls.restaurant,
            category=cls.italian,
            is_available=False  # Not available
        )
        
        # Create Chinese items
        cls.fried_rice = MenuItem.objects.create(
            name="Yangzhou Fried Rice",
            description="Traditional Chinese fried rice",
            price=Decimal('10.99'),
            restaurant=cls.restaurant,
            category=cls.chinese,
            is_available=True
        )
        cls.kung_pao = MenuItem.objects.create(
            name="Kung Pao Chicken",
            description="Spicy Sichuan dish",
            price=Decimal('13.99'),
            restaurant=cls.restaurant,
            category=cls.chinese,
            is_available=True
        )
        
        # Create Desserts
        cls.tiramisu = MenuItem.objects.create(
            name="Tiramisu",
            description="Italian coffee dessert",
            price=Decimal('7.99'),
            restaurant=cls.restaurant,
            category=cls.desserts,
            is_available=True
        )
        
        # Create Appetizers
        cls.spring_rolls = MenuItem.objects.create(
            name="Spring Rolls",
            description="Crispy vegetable rolls",
            price=Decimal('5.99'),
            restaurant=cls.restaurant,
            category=cls.appetizers,
            is_available=True
        )
        
        # Create item with no category
        cls.no_category_item = MenuItem.objects.create(
            name="Uncategorized Item",
            description="Item without category",
            price=Decimal('9.99'),
            restaurant=cls.restaurant,
            category=None,
            is_available=True
        )
    
    def test_get_italian_cuisine(self):
        """Test retrieving Italian cuisine items."""
        items = MenuItem.get_by_cuisine('Italian')
        
        self.assertEqual(items.count(), 3)
        self.assertIn(self.pasta, items)
        self.assertIn(self.pizza, items)
        self.assertIn(self.risotto, items)
    
    def test_get_chinese_cuisine(self):
        """Test retrieving Chinese cuisine items."""
        items = MenuItem.get_by_cuisine('Chinese')
        
        self.assertEqual(items.count(), 2)
        self.assertIn(self.fried_rice, items)
        self.assertIn(self.kung_pao, items)
    
    def test_get_desserts_cuisine(self):
        """Test retrieving Desserts category items."""
        items = MenuItem.get_by_cuisine('Desserts')
        
        self.assertEqual(items.count(), 1)
        self.assertIn(self.tiramisu, items)
    
    def test_get_appetizers_cuisine(self):
        """Test retrieving Appetizers category items."""
        items = MenuItem.get_by_cuisine('Appetizers')
        
        self.assertEqual(items.count(), 1)
        self.assertIn(self.spring_rolls, items)
    
    def test_case_insensitive_search(self):
        """Test that cuisine search is case-insensitive."""
        # Test lowercase
        items_lower = MenuItem.get_by_cuisine('italian')
        self.assertEqual(items_lower.count(), 3)
        
        # Test uppercase
        items_upper = MenuItem.get_by_cuisine('ITALIAN')
        self.assertEqual(items_upper.count(), 3)
        
        # Test mixed case
        items_mixed = MenuItem.get_by_cuisine('ItAlIaN')
        self.assertEqual(items_mixed.count(), 3)
        
        # All should return same items
        self.assertEqual(set(items_lower), set(items_upper))
        self.assertEqual(set(items_lower), set(items_mixed))
    
    def test_nonexistent_cuisine(self):
        """Test that nonexistent cuisine returns empty queryset."""
        items = MenuItem.get_by_cuisine('Mexican')
        
        self.assertEqual(items.count(), 0)
        self.assertFalse(items.exists())
        self.assertEqual(list(items), [])
    
    def test_none_cuisine_type(self):
        """Test that None cuisine_type returns empty queryset."""
        items = MenuItem.get_by_cuisine(None)
        
        self.assertEqual(items.count(), 0)
        self.assertFalse(items.exists())
        self.assertEqual(list(items), [])
    
    def test_empty_string_cuisine_type(self):
        """Test that empty string cuisine_type returns empty queryset."""
        items = MenuItem.get_by_cuisine('')
        
        self.assertEqual(items.count(), 0)
        self.assertFalse(items.exists())
        self.assertEqual(list(items), [])
    
    def test_whitespace_cuisine_type(self):
        """Test that whitespace-only cuisine_type returns empty queryset."""
        items = MenuItem.get_by_cuisine('   ')
        
        # Note: '   ' is truthy in Python, so it will search for category name '   '
        # which doesn't exist, so should return empty queryset
        self.assertEqual(items.count(), 0)
        self.assertFalse(items.exists())
    
    def test_returns_queryset(self):
        """Test that method returns a QuerySet, not a list."""
        from django.db.models import QuerySet
        
        items = MenuItem.get_by_cuisine('Italian')
        
        self.assertIsInstance(items, QuerySet)
        self.assertNotIsInstance(items, list)
    
    def test_queryset_chaining(self):
        """Test that returned QuerySet can be chained with other filters."""
        # Chain with is_available filter
        available_italian = MenuItem.get_by_cuisine('Italian').filter(is_available=True)
        
        self.assertEqual(available_italian.count(), 2)
        self.assertIn(self.pasta, available_italian)
        self.assertIn(self.pizza, available_italian)
        self.assertNotIn(self.risotto, available_italian)  # Not available
    
    def test_queryset_ordering(self):
        """Test that returned QuerySet can be ordered."""
        # Order by price ascending
        items_by_price = MenuItem.get_by_cuisine('Italian').order_by('price')
        
        prices = list(items_by_price.values_list('price', flat=True))
        self.assertEqual(prices, sorted(prices))
    
    def test_queryset_filtering_by_price(self):
        """Test filtering by price range after cuisine filter."""
        # Get Italian items under $15
        affordable_italian = MenuItem.get_by_cuisine('Italian').filter(price__lt=Decimal('15.00'))
        
        self.assertEqual(affordable_italian.count(), 2)
        self.assertIn(self.pizza, affordable_italian)  # $12.99
        self.assertIn(self.risotto, affordable_italian)  # $14.50
        self.assertNotIn(self.pasta, affordable_italian)  # $15.99
    
    def test_queryset_values(self):
        """Test using values() on returned QuerySet."""
        items = MenuItem.get_by_cuisine('Chinese').values('name', 'price')
        
        self.assertEqual(len(items), 2)
        names = [item['name'] for item in items]
        self.assertIn('Yangzhou Fried Rice', names)
        self.assertIn('Kung Pao Chicken', names)
    
    def test_queryset_exists(self):
        """Test using exists() on returned QuerySet."""
        # Cuisine with items
        self.assertTrue(MenuItem.get_by_cuisine('Italian').exists())
        
        # Cuisine without items
        self.assertFalse(MenuItem.get_by_cuisine('Mexican').exists())
    
    def test_queryset_count(self):
        """Test using count() on returned QuerySet."""
        self.assertEqual(MenuItem.get_by_cuisine('Italian').count(), 3)
        self.assertEqual(MenuItem.get_by_cuisine('Chinese').count(), 2)
        self.assertEqual(MenuItem.get_by_cuisine('Mexican').count(), 0)
    
    def test_excludes_items_without_category(self):
        """Test that items with category=None are not included."""
        # Get all items for a nonexistent cuisine
        items = MenuItem.get_by_cuisine('Uncategorized')
        
        # Should not include the no_category_item
        self.assertNotIn(self.no_category_item, items)
        self.assertEqual(items.count(), 0)
    
    def test_multiple_restaurants_same_cuisine(self):
        """Test filtering cuisine items across multiple restaurants."""
        # Create another restaurant
        restaurant2 = Restaurant.objects.create(
            name="Another Restaurant",
            owner_name="Another Owner",
            email="another@restaurant.com",
            phone_number="555-5678"
        )
        
        # Create Italian item in second restaurant
        pasta2 = MenuItem.objects.create(
            name="Penne Arrabbiata",
            description="Spicy Italian pasta",
            price=Decimal('13.99'),
            restaurant=restaurant2,
            category=self.italian,
            is_available=True
        )
        
        # Should get Italian items from both restaurants
        italian_items = MenuItem.get_by_cuisine('Italian')
        self.assertEqual(italian_items.count(), 4)
        self.assertIn(pasta2, italian_items)
        self.assertIn(self.pasta, italian_items)
    
    def test_featured_items_by_cuisine(self):
        """Test filtering for featured items within a cuisine."""
        # Mark one Italian item as featured
        self.pasta.is_featured = True
        self.pasta.save()
        
        # Get featured Italian items
        featured_italian = MenuItem.get_by_cuisine('Italian').filter(is_featured=True)
        
        self.assertEqual(featured_italian.count(), 1)
        self.assertIn(self.pasta, featured_italian)
    
    def test_daily_specials_by_cuisine(self):
        """Test filtering for daily specials within a cuisine."""
        # Mark Chinese items as daily specials
        self.fried_rice.is_daily_special = True
        self.fried_rice.save()
        
        # Get Chinese daily specials
        chinese_specials = MenuItem.get_by_cuisine('Chinese').filter(is_daily_special=True)
        
        self.assertEqual(chinese_specials.count(), 1)
        self.assertIn(self.fried_rice, chinese_specials)
        self.assertNotIn(self.kung_pao, chinese_specials)
    
    def test_empty_cuisine_with_category_exists(self):
        """Test cuisine with category that has no items."""
        # Create a category with no items
        MenuCategory.objects.create(
            name="Mexican",
            description="Mexican cuisine"
        )
        
        items = MenuItem.get_by_cuisine('Mexican')
        
        self.assertEqual(items.count(), 0)
        self.assertFalse(items.exists())
    
    def test_special_characters_in_cuisine_name(self):
        """Test cuisine names with special characters."""
        # Create category with special characters
        special_category = MenuCategory.objects.create(
            name="Café & Bakery",
            description="Coffee and baked goods"
        )
        
        coffee = MenuItem.objects.create(
            name="Espresso",
            description="Strong coffee",
            price=Decimal('3.99'),
            restaurant=self.restaurant,
            category=special_category,
            is_available=True
        )
        
        items = MenuItem.get_by_cuisine('Café & Bakery')
        
        self.assertEqual(items.count(), 1)
        self.assertIn(coffee, items)
    
    def test_numeric_cuisine_name(self):
        """Test cuisine name that looks like a number."""
        # Create category with numeric-looking name
        category_24_7 = MenuCategory.objects.create(
            name="24/7 Menu",
            description="Always available items"
        )
        
        burger = MenuItem.objects.create(
            name="Classic Burger",
            description="Available anytime",
            price=Decimal('8.99'),
            restaurant=self.restaurant,
            category=category_24_7,
            is_available=True
        )
        
        items = MenuItem.get_by_cuisine('24/7 Menu')
        
        self.assertEqual(items.count(), 1)
        self.assertIn(burger, items)
    
    def test_queryset_select_related(self):
        """Test using select_related on returned QuerySet."""
        # Should be able to optimize queries with select_related
        items = MenuItem.get_by_cuisine('Italian').select_related('category', 'restaurant')
        
        # This would cause additional queries if not properly select_related
        with self.assertNumQueries(1):
            for item in items:
                _ = item.category.name
                _ = item.restaurant.name
    
    def test_queryset_prefetch_related(self):
        """Test using prefetch_related on returned QuerySet."""
        # Add ingredients to test prefetch_related
        from home.models import Ingredient
        
        tomato = Ingredient.objects.create(name="Tomato")
        cheese = Ingredient.objects.create(name="Cheese")
        
        self.pizza.ingredients.add(tomato, cheese)
        
        # Prefetch ingredients
        items = MenuItem.get_by_cuisine('Italian').prefetch_related('ingredients')
        
        # Should efficiently fetch ingredients in 2 queries total (1 for items, 1 for ingredients)
        with self.assertNumQueries(2):
            for item in items:
                _ = list(item.ingredients.all())
