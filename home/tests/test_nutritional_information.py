"""
Django TestCase for NutritionalInformation model.

This test suite validates the NutritionalInformation model functionality including:
1. Model creation and field validation
2. ForeignKey relationship with MenuItem
3. DecimalField precision for macronutrients
4. __str__ method representation
5. CRUD operations and data persistence

Run with: python manage.py test home.tests.test_nutritional_information
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal

from home.models import MenuItem, Restaurant, MenuCategory, NutritionalInformation


class NutritionalInformationModelTests(TestCase):
    """Test cases for the NutritionalInformation model."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all test methods."""
        # Create test restaurant
        cls.restaurant = Restaurant.objects.create(
            name='Healthy Eats',
            owner_name='Health Owner',
            email='healthy@restaurant.com',
            phone_number='555-1111'
        )
        
        # Create test category
        cls.category = MenuCategory.objects.create(
            name='Salads',
            description='Healthy salad options'
        )
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.menu_item = MenuItem.objects.create(
            name='Caesar Salad',
            description='Classic caesar salad',
            price=Decimal('12.99'),
            restaurant=self.restaurant,
            category=self.category
        )
    
    def test_nutritional_information_creation(self):
        """Test that NutritionalInformation can be created successfully."""
        nutrition = NutritionalInformation.objects.create(
            menu_item=self.menu_item,
            calories=350,
            protein_grams=Decimal('15.50'),
            fat_grams=Decimal('20.00'),
            carbohydrate_grams=Decimal('25.30')
        )
        
        self.assertEqual(nutrition.menu_item, self.menu_item)
        self.assertEqual(nutrition.calories, 350)
        self.assertEqual(nutrition.protein_grams, Decimal('15.50'))
        self.assertEqual(nutrition.fat_grams, Decimal('20.00'))
        self.assertEqual(nutrition.carbohydrate_grams, Decimal('25.30'))
    
    def test_nutritional_information_str_method(self):
        """Test the __str__ method returns correct format."""
        nutrition = NutritionalInformation.objects.create(
            menu_item=self.menu_item,
            calories=350,
            protein_grams=Decimal('15.50'),
            fat_grams=Decimal('20.00'),
            carbohydrate_grams=Decimal('25.30')
        )
        
        expected = f"{self.menu_item.name} - 350 calories"
        self.assertEqual(str(nutrition), expected)
    
    def test_foreign_key_relationship(self):
        """Test that ForeignKey relationship with MenuItem works correctly."""
        nutrition = NutritionalInformation.objects.create(
            menu_item=self.menu_item,
            calories=350,
            protein_grams=Decimal('15.50'),
            fat_grams=Decimal('20.00'),
            carbohydrate_grams=Decimal('25.30')
        )
        
        # Access from nutrition to menu_item
        self.assertEqual(nutrition.menu_item.name, 'Caesar Salad')
        
        # Access from menu_item to nutrition (reverse relationship)
        self.assertEqual(self.menu_item.nutritional_info.first(), nutrition)
    
    def test_cascade_delete(self):
        """Test that deleting menu item cascades to nutritional info."""
        nutrition = NutritionalInformation.objects.create(
            menu_item=self.menu_item,
            calories=350,
            protein_grams=Decimal('15.50'),
            fat_grams=Decimal('20.00'),
            carbohydrate_grams=Decimal('25.30')
        )
        
        nutrition_id = nutrition.id
        
        # Delete the menu item
        self.menu_item.delete()
        
        # Verify nutritional info was also deleted
        with self.assertRaises(NutritionalInformation.DoesNotExist):
            NutritionalInformation.objects.get(id=nutrition_id)
    
    def test_decimal_field_precision(self):
        """Test that DecimalFields maintain correct precision."""
        nutrition = NutritionalInformation.objects.create(
            menu_item=self.menu_item,
            calories=350,
            protein_grams=Decimal('15.55'),
            fat_grams=Decimal('20.99'),
            carbohydrate_grams=Decimal('25.01')
        )
        
        # Retrieve from database
        retrieved = NutritionalInformation.objects.get(id=nutrition.id)
        
        self.assertEqual(retrieved.protein_grams, Decimal('15.55'))
        self.assertEqual(retrieved.fat_grams, Decimal('20.99'))
        self.assertEqual(retrieved.carbohydrate_grams, Decimal('25.01'))
    
    def test_calories_is_integer(self):
        """Test that calories field accepts integer values."""
        nutrition = NutritionalInformation.objects.create(
            menu_item=self.menu_item,
            calories=500,
            protein_grams=Decimal('20.00'),
            fat_grams=Decimal('15.00'),
            carbohydrate_grams=Decimal('30.00')
        )
        
        self.assertIsInstance(nutrition.calories, int)
        self.assertEqual(nutrition.calories, 500)
    
    def test_multiple_nutritional_infos_for_different_items(self):
        """Test that multiple menu items can have their own nutritional info."""
        item2 = MenuItem.objects.create(
            name='Greek Salad',
            price=Decimal('11.99'),
            restaurant=self.restaurant,
            category=self.category
        )
        
        nutrition1 = NutritionalInformation.objects.create(
            menu_item=self.menu_item,
            calories=350,
            protein_grams=Decimal('15.50'),
            fat_grams=Decimal('20.00'),
            carbohydrate_grams=Decimal('25.30')
        )
        
        nutrition2 = NutritionalInformation.objects.create(
            menu_item=item2,
            calories=280,
            protein_grams=Decimal('12.00'),
            fat_grams=Decimal('18.00'),
            carbohydrate_grams=Decimal('20.00')
        )
        
        self.assertEqual(NutritionalInformation.objects.count(), 2)
        self.assertNotEqual(nutrition1.menu_item, nutrition2.menu_item)
    
    def test_update_nutritional_information(self):
        """Test that nutritional information can be updated."""
        nutrition = NutritionalInformation.objects.create(
            menu_item=self.menu_item,
            calories=350,
            protein_grams=Decimal('15.50'),
            fat_grams=Decimal('20.00'),
            carbohydrate_grams=Decimal('25.30')
        )
        
        # Update values
        nutrition.calories = 400
        nutrition.protein_grams = Decimal('18.00')
        nutrition.save()
        
        # Retrieve and verify
        retrieved = NutritionalInformation.objects.get(id=nutrition.id)
        self.assertEqual(retrieved.calories, 400)
        self.assertEqual(retrieved.protein_grams, Decimal('18.00'))
    
    def test_zero_values_allowed(self):
        """Test that zero values are allowed for nutritional fields."""
        nutrition = NutritionalInformation.objects.create(
            menu_item=self.menu_item,
            calories=0,
            protein_grams=Decimal('0.00'),
            fat_grams=Decimal('0.00'),
            carbohydrate_grams=Decimal('0.00')
        )
        
        self.assertEqual(nutrition.calories, 0)
        self.assertEqual(nutrition.protein_grams, Decimal('0.00'))
    
    def test_high_calorie_values(self):
        """Test that high calorie values are accepted."""
        nutrition = NutritionalInformation.objects.create(
            menu_item=self.menu_item,
            calories=2000,
            protein_grams=Decimal('50.00'),
            fat_grams=Decimal('80.00'),
            carbohydrate_grams=Decimal('150.00')
        )
        
        self.assertEqual(nutrition.calories, 2000)
        self.assertEqual(nutrition.protein_grams, Decimal('50.00'))


class NutritionalInformationQueryTests(TestCase):
    """Test cases for querying NutritionalInformation."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all test methods."""
        # Create test restaurant and category
        cls.restaurant = Restaurant.objects.create(
            name='Query Test Restaurant',
            owner_name='Query Owner',
            email='query@restaurant.com',
            phone_number='555-2222'
        )
        
        cls.category = MenuCategory.objects.create(
            name='Main Dishes',
            description='Main course options'
        )
        
        # Create menu items with nutritional info
        for i in range(3):
            item = MenuItem.objects.create(
                name=f'Dish {i}',
                price=Decimal('10.99'),
                restaurant=cls.restaurant,
                category=cls.category
            )
            
            NutritionalInformation.objects.create(
                menu_item=item,
                calories=300 + (i * 100),
                protein_grams=Decimal(f'{10 + i}.00'),
                fat_grams=Decimal(f'{15 + i}.00'),
                carbohydrate_grams=Decimal(f'{20 + i}.00')
            )
    
    def test_filter_by_calorie_range(self):
        """Test filtering nutritional info by calorie range."""
        low_cal = NutritionalInformation.objects.filter(calories__lt=400)
        self.assertEqual(low_cal.count(), 1)  # Only 300 calories
        
        high_cal = NutritionalInformation.objects.filter(calories__gte=400)
        self.assertEqual(high_cal.count(), 2)  # 400 and 500 calories
    
    def test_filter_by_protein(self):
        """Test filtering by protein content."""
        high_protein = NutritionalInformation.objects.filter(
            protein_grams__gte=Decimal('11.00')
        )
        self.assertEqual(high_protein.count(), 2)
    
    def test_get_nutritional_info_through_menu_item(self):
        """Test accessing nutritional info through menu item."""
        item = MenuItem.objects.filter(name='Dish 0').first()
        nutrition = item.nutritional_info.first()
        
        self.assertIsNotNone(nutrition)
        self.assertEqual(nutrition.calories, 300)
    
    def test_count_items_with_nutritional_info(self):
        """Test counting menu items that have nutritional information."""
        count = NutritionalInformation.objects.count()
        self.assertEqual(count, 3)
    
    def test_order_by_calories(self):
        """Test ordering nutritional info by calories."""
        nutrition_list = NutritionalInformation.objects.order_by('calories')
        
        calories = [n.calories for n in nutrition_list]
        self.assertEqual(calories, [300, 400, 500])


class NutritionalInformationTimestampTests(TestCase):
    """Test cases for timestamp fields."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.restaurant = Restaurant.objects.create(
            name='Timestamp Test',
            owner_name='Timestamp Owner',
            email='timestamp@restaurant.com',
            phone_number='555-3333'
        )
        
        self.category = MenuCategory.objects.create(
            name='Desserts',
            description='Sweet treats'
        )
        
        self.menu_item = MenuItem.objects.create(
            name='Chocolate Cake',
            price=Decimal('8.99'),
            restaurant=self.restaurant,
            category=self.category
        )
    
    def test_created_at_auto_set(self):
        """Test that created_at is automatically set."""
        nutrition = NutritionalInformation.objects.create(
            menu_item=self.menu_item,
            calories=450,
            protein_grams=Decimal('5.00'),
            fat_grams=Decimal('25.00'),
            carbohydrate_grams=Decimal('50.00')
        )
        
        self.assertIsNotNone(nutrition.created_at)
    
    def test_updated_at_auto_set(self):
        """Test that updated_at is automatically set and updated."""
        nutrition = NutritionalInformation.objects.create(
            menu_item=self.menu_item,
            calories=450,
            protein_grams=Decimal('5.00'),
            fat_grams=Decimal('25.00'),
            carbohydrate_grams=Decimal('50.00')
        )
        
        original_updated = nutrition.updated_at
        
        # Update the record
        nutrition.calories = 500
        nutrition.save()
        
        # Reload from database
        nutrition.refresh_from_db()
        
        self.assertIsNotNone(nutrition.updated_at)
        self.assertGreaterEqual(nutrition.updated_at, original_updated)


if __name__ == '__main__':
    print("=" * 80)
    print("NUTRITIONAL INFORMATION MODEL TEST SUITE")
    print("=" * 80)
    print("\nRun with: python manage.py test home.tests.test_nutritional_information")
    print("\nThis test suite covers:")
    print("  ✓ Model creation and field validation")
    print("  ✓ ForeignKey relationship with MenuItem")
    print("  ✓ Cascade deletion behavior")
    print("  ✓ DecimalField precision for macronutrients")
    print("  ✓ Integer field for calories")
    print("  ✓ __str__ method representation")
    print("  ✓ CRUD operations")
    print("  ✓ Query filtering and ordering")
    print("  ✓ Timestamp field behavior")
    print("=" * 80)
