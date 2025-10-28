"""
Django TestCase for Menu Item Ingredients API endpoint.

This test suite validates the ingredients API functionality including:
1. Endpoint accessibility and permissions
2. Ingredient model and serialization
3. Response structure and data accuracy
4. Edge cases (no ingredients, invalid menu item)
5. ManyToMany relationship behavior

Run with: python manage.py test home.tests.test_ingredients_api
"""

from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
import json

from home.models import MenuItem, MenuCategory, Restaurant, Ingredient


class IngredientModelTests(TestCase):
    """Test cases for the Ingredient model."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all test methods."""
        pass
    
    def test_ingredient_creation(self):
        """Test that ingredients can be created successfully."""
        ingredient = Ingredient.objects.create(
            name='Tomato',
            description='Fresh roma tomatoes',
            is_allergen=False,
            is_vegetarian=True,
            is_vegan=True
        )
        
        self.assertEqual(ingredient.name, 'Tomato')
        self.assertEqual(ingredient.description, 'Fresh roma tomatoes')
        self.assertFalse(ingredient.is_allergen)
        self.assertTrue(ingredient.is_vegetarian)
        self.assertTrue(ingredient.is_vegan)
    
    def test_ingredient_str_method(self):
        """Test the __str__ method returns ingredient name."""
        ingredient = Ingredient.objects.create(name='Cheese')
        self.assertEqual(str(ingredient), 'Cheese')
    
    def test_ingredient_unique_name(self):
        """Test that ingredient names must be unique."""
        Ingredient.objects.create(name='Lettuce')
        
        with self.assertRaises(Exception):  # IntegrityError wrapped by Django
            Ingredient.objects.create(name='Lettuce')
    
    def test_ingredient_defaults(self):
        """Test default values for ingredient flags."""
        ingredient = Ingredient.objects.create(name='Garlic')
        
        # Check defaults
        self.assertFalse(ingredient.is_allergen)
        self.assertTrue(ingredient.is_vegetarian)  # default=True
        self.assertFalse(ingredient.is_vegan)  # default=False
    
    def test_ingredient_allergen_flag(self):
        """Test that allergen flag can be set."""
        allergen = Ingredient.objects.create(
            name='Peanuts',
            is_allergen=True,
            is_vegetarian=True,
            is_vegan=True
        )
        
        self.assertTrue(allergen.is_allergen)


class MenuItemIngredientRelationshipTests(TestCase):
    """Test cases for MenuItem-Ingredient ManyToMany relationship."""
    
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
            name='Main Courses',
            description='Main course dishes'
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
        
        # Create ingredients
        self.lettuce = Ingredient.objects.create(
            name='Romaine Lettuce',
            is_allergen=False,
            is_vegetarian=True,
            is_vegan=True
        )
        
        self.cheese = Ingredient.objects.create(
            name='Parmesan Cheese',
            is_allergen=True,  # Dairy allergen
            is_vegetarian=True,
            is_vegan=False
        )
    
    def test_add_ingredient_to_menu_item(self):
        """Test adding ingredients to a menu item."""
        self.menu_item.ingredients.add(self.lettuce)
        self.menu_item.ingredients.add(self.cheese)
        
        self.assertEqual(self.menu_item.ingredients.count(), 2)
        self.assertIn(self.lettuce, self.menu_item.ingredients.all())
        self.assertIn(self.cheese, self.menu_item.ingredients.all())
    
    def test_menu_item_starts_with_no_ingredients(self):
        """Test that newly created menu items have no ingredients by default."""
        self.assertEqual(self.menu_item.ingredients.count(), 0)
    
    def test_remove_ingredient_from_menu_item(self):
        """Test removing an ingredient from a menu item."""
        self.menu_item.ingredients.add(self.lettuce, self.cheese)
        self.assertEqual(self.menu_item.ingredients.count(), 2)
        
        self.menu_item.ingredients.remove(self.cheese)
        self.assertEqual(self.menu_item.ingredients.count(), 1)
        self.assertNotIn(self.cheese, self.menu_item.ingredients.all())
    
    def test_ingredient_can_be_used_in_multiple_items(self):
        """Test that an ingredient can be associated with multiple menu items."""
        item2 = MenuItem.objects.create(
            name='Greek Salad',
            price=Decimal('11.99'),
            restaurant=self.restaurant,
            category=self.category
        )
        
        # Add same ingredient to both items
        self.menu_item.ingredients.add(self.lettuce)
        item2.ingredients.add(self.lettuce)
        
        # Check reverse relationship
        self.assertEqual(self.lettuce.menu_items.count(), 2)
        self.assertIn(self.menu_item, self.lettuce.menu_items.all())
        self.assertIn(item2, self.lettuce.menu_items.all())


class MenuItemIngredientsAPITests(TestCase):
    """Test cases for the Menu Item Ingredients API endpoint."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all test methods."""
        # Create test restaurant
        cls.restaurant = Restaurant.objects.create(
            name='La Bistro',
            owner_name='Bistro Owner',
            email='bistro@restaurant.com',
            phone_number='555-9876',
            opening_hours={'Monday': '11am-11pm'}
        )
        
        # Create test category
        cls.category = MenuCategory.objects.create(
            name='Salads',
            description='Fresh salads'
        )
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.client = Client()
        
        # Create menu item
        self.menu_item = MenuItem.objects.create(
            name='House Salad',
            description='Fresh garden salad',
            price=Decimal('9.99'),
            restaurant=self.restaurant,
            category=self.category
        )
        
        # Create ingredients
        self.ingredient1 = Ingredient.objects.create(
            name='Lettuce',
            description='Fresh lettuce',
            is_allergen=False,
            is_vegetarian=True,
            is_vegan=True
        )
        
        self.ingredient2 = Ingredient.objects.create(
            name='Tomato',
            description='Ripe tomatoes',
            is_allergen=False,
            is_vegetarian=True,
            is_vegan=True
        )
        
        self.ingredient3 = Ingredient.objects.create(
            name='Feta Cheese',
            description='Crumbled feta',
            is_allergen=True,
            is_vegetarian=True,
            is_vegan=False
        )
        
        # Add ingredients to menu item
        self.menu_item.ingredients.add(self.ingredient1, self.ingredient2, self.ingredient3)
    
    def test_endpoint_accessible_without_authentication(self):
        """Test that the endpoint is publicly accessible."""
        url = reverse('menuitem-ingredients', kwargs={'pk': self.menu_item.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_endpoint_returns_json(self):
        """Test that endpoint returns JSON response."""
        url = reverse('menuitem-ingredients', kwargs={'pk': self.menu_item.pk})
        response = self.client.get(url)
        self.assertEqual(response['Content-Type'], 'application/json')
    
    def test_response_structure(self):
        """Test that response has correct structure."""
        url = reverse('menuitem-ingredients', kwargs={'pk': self.menu_item.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        
        # Check top-level keys
        self.assertIn('id', data)
        self.assertIn('name', data)
        self.assertIn('ingredients', data)
        
        # Check that ingredients is a list
        self.assertIsInstance(data['ingredients'], list)
    
    def test_returns_correct_menu_item_info(self):
        """Test that response includes correct menu item details."""
        url = reverse('menuitem-ingredients', kwargs={'pk': self.menu_item.pk})
        response = self.client.get(url)
        data = json.loads(response.content)
        
        self.assertEqual(data['id'], self.menu_item.id)
        self.assertEqual(data['name'], 'House Salad')
    
    def test_returns_all_ingredients(self):
        """Test that all ingredients for menu item are returned."""
        url = reverse('menuitem-ingredients', kwargs={'pk': self.menu_item.pk})
        response = self.client.get(url)
        data = json.loads(response.content)
        
        self.assertEqual(len(data['ingredients']), 3)
        
        # Check ingredient names
        ingredient_names = [ing['name'] for ing in data['ingredients']]
        self.assertIn('Lettuce', ingredient_names)
        self.assertIn('Tomato', ingredient_names)
        self.assertIn('Feta Cheese', ingredient_names)
    
    def test_ingredient_fields_in_response(self):
        """Test that each ingredient has all expected fields."""
        url = reverse('menuitem-ingredients', kwargs={'pk': self.menu_item.pk})
        response = self.client.get(url)
        data = json.loads(response.content)
        
        for ingredient in data['ingredients']:
            self.assertIn('id', ingredient)
            self.assertIn('name', ingredient)
            self.assertIn('description', ingredient)
            self.assertIn('is_allergen', ingredient)
            self.assertIn('is_vegetarian', ingredient)
            self.assertIn('is_vegan', ingredient)
    
    def test_ingredient_data_accuracy(self):
        """Test that ingredient data matches database values."""
        url = reverse('menuitem-ingredients', kwargs={'pk': self.menu_item.pk})
        response = self.client.get(url)
        data = json.loads(response.content)
        
        # Find feta cheese in response
        feta = next((ing for ing in data['ingredients'] if ing['name'] == 'Feta Cheese'), None)
        self.assertIsNotNone(feta)
        
        # Verify field values
        self.assertEqual(feta['description'], 'Crumbled feta')
        self.assertTrue(feta['is_allergen'])
        self.assertTrue(feta['is_vegetarian'])
        self.assertFalse(feta['is_vegan'])
    
    def test_empty_ingredients_list(self):
        """Test endpoint returns empty list when menu item has no ingredients."""
        # Create item with no ingredients
        empty_item = MenuItem.objects.create(
            name='Plain Rice',
            price=Decimal('3.99'),
            restaurant=self.restaurant,
            category=self.category
        )
        
        url = reverse('menuitem-ingredients', kwargs={'pk': empty_item.pk})
        response = self.client.get(url)
        data = json.loads(response.content)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['ingredients']), 0)
        self.assertEqual(data['ingredients'], [])
    
    def test_invalid_menu_item_id_returns_404(self):
        """Test that invalid menu item ID returns 404."""
        url = reverse('menuitem-ingredients', kwargs={'pk': 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
    
    def test_post_method_not_allowed(self):
        """Test that POST method is not allowed (read-only endpoint)."""
        url = reverse('menuitem-ingredients', kwargs={'pk': self.menu_item.pk})
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 405)  # Method Not Allowed
    
    def test_put_method_not_allowed(self):
        """Test that PUT method is not allowed."""
        url = reverse('menuitem-ingredients', kwargs={'pk': self.menu_item.pk})
        response = self.client.put(url, {})
        self.assertEqual(response.status_code, 405)
    
    def test_delete_method_not_allowed(self):
        """Test that DELETE method is not allowed."""
        url = reverse('menuitem-ingredients', kwargs={'pk': self.menu_item.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 405)


if __name__ == '__main__':
    print("=" * 80)
    print("MENU ITEM INGREDIENTS API TEST SUITE")
    print("=" * 80)
    print("\nRun with: python manage.py test home.tests.test_ingredients_api")
    print("\nThis test suite covers:")
    print("  ✓ Ingredient model creation and validation")
    print("  ✓ ManyToMany relationship between MenuItem and Ingredient")
    print("  ✓ API endpoint permissions and accessibility")
    print("  ✓ Response structure and data accuracy")
    print("  ✓ Edge cases (empty ingredients, invalid IDs)")
    print("  ✓ HTTP method restrictions")
    print("=" * 80)
