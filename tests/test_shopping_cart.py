"""
Comprehensive tests for shopping cart functionality.
Tests both session-based and database-based cart operations, API endpoints, and model behavior.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
import json

from home.models import Restaurant, MenuItem, MenuCategory, Cart, CartItem
from home.cart_utils import (
    get_or_create_cart, add_to_cart, remove_from_cart, 
    update_cart_item_quantity, clear_cart, get_cart_summary, 
    migrate_session_cart_to_user
)


class CartModelTests(TestCase):
    """Test Cart and CartItem model functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test restaurant
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner_name='Test Owner',
            email='owner@test.com',
            phone_number='555-1234'
        )
        
        # Create test category
        self.category = MenuCategory.objects.create(name='Main Course')
        
        # Create test menu items
        self.menu_item1 = MenuItem.objects.create(
            name='Burger',
            description='Delicious burger',
            price=Decimal('12.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_available=True
        )
        
        self.menu_item2 = MenuItem.objects.create(
            name='Pizza',
            description='Cheese pizza',
            price=Decimal('15.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_available=True
        )
        
        self.unavailable_item = MenuItem.objects.create(
            name='Unavailable Item',
            description='Not available',
            price=Decimal('10.00'),
            restaurant=self.restaurant,
            is_available=False
        )

    def test_cart_creation_for_user(self):
        """Test creating a cart for an authenticated user."""
        cart = Cart.objects.create(user=self.user)
        self.assertEqual(cart.user, self.user)
        self.assertIsNone(cart.session_key)
        self.assertEqual(str(cart), f"Cart for {self.user.username}")

    def test_cart_creation_for_session(self):
        """Test creating a cart for a session."""
        session_key = 'test_session_123'
        cart = Cart.objects.create(session_key=session_key)
        self.assertIsNone(cart.user)
        self.assertEqual(cart.session_key, session_key)
        self.assertTrue(str(cart).startswith('Cart for session test_sessi'))

    def test_cart_total_items_empty(self):
        """Test total_items property with empty cart."""
        cart = Cart.objects.create(user=self.user)
        self.assertEqual(cart.total_items, 0)

    def test_cart_total_items_with_items(self):
        """Test total_items property with items."""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, menu_item=self.menu_item1, quantity=2)
        CartItem.objects.create(cart=cart, menu_item=self.menu_item2, quantity=3)
        self.assertEqual(cart.total_items, 5)

    def test_cart_total_price_empty(self):
        """Test total_price property with empty cart."""
        cart = Cart.objects.create(user=self.user)
        self.assertEqual(cart.total_price, 0)

    def test_cart_total_price_with_items(self):
        """Test total_price property with items."""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, menu_item=self.menu_item1, quantity=2)  # 2 * 12.99 = 25.98
        CartItem.objects.create(cart=cart, menu_item=self.menu_item2, quantity=1)  # 1 * 15.99 = 15.99
        expected_total = Decimal('25.98') + Decimal('15.99')
        self.assertEqual(cart.total_price, expected_total)

    def test_cart_clear(self):
        """Test clearing all items from cart."""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, menu_item=self.menu_item1, quantity=2)
        CartItem.objects.create(cart=cart, menu_item=self.menu_item2, quantity=1)
        
        self.assertEqual(cart.total_items, 3)
        cart.clear()
        self.assertEqual(cart.total_items, 0)

    def test_cart_item_subtotal(self):
        """Test CartItem subtotal calculation."""
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(cart=cart, menu_item=self.menu_item1, quantity=3)
        expected_subtotal = self.menu_item1.price * 3
        self.assertEqual(cart_item.subtotal, expected_subtotal)

    def test_cart_item_unique_constraint(self):
        """Test that same menu item cannot be added twice to same cart."""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, menu_item=self.menu_item1, quantity=1)
        
        # This should raise an integrity error due to unique_together constraint
        with self.assertRaises(Exception):  # IntegrityError in real DB
            CartItem.objects.create(cart=cart, menu_item=self.menu_item1, quantity=2)

    def test_cart_item_clean_unavailable_item(self):
        """Test CartItem.clean() method with unavailable item."""
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem(cart=cart, menu_item=self.unavailable_item, quantity=1)
        
        with self.assertRaises(ValidationError):
            cart_item.clean()


class CartUtilsTests(TestCase):
    """Test cart utility functions."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner_name='Test Owner',
            email='owner@test.com',
            phone_number='555-1234'
        )
        
        self.category = MenuCategory.objects.create(name='Main Course')
        
        self.menu_item = MenuItem.objects.create(
            name='Test Item',
            description='Test description',
            price=Decimal('10.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_available=True
        )
        
        self.unavailable_item = MenuItem.objects.create(
            name='Unavailable Item',
            description='Not available',
            price=Decimal('5.99'),
            restaurant=self.restaurant,
            is_available=False
        )
        
        self.client = Client()

    def test_get_or_create_cart_authenticated_user(self):
        """Test getting/creating cart for authenticated user."""
        # Simulate authenticated user
        self.client.force_login(self.user)
        request = self.client.get('/').wsgi_request
        request.user = self.user
        
        cart = get_or_create_cart(request)
        self.assertEqual(cart.user, self.user)
        self.assertIsNone(cart.session_key)
        
        # Should return same cart on second call
        cart2 = get_or_create_cart(request)
        self.assertEqual(cart.id, cart2.id)

    def test_get_or_create_cart_anonymous_user(self):
        """Test getting/creating cart for anonymous user."""
        # Create a session
        session = self.client.session
        session.create()
        request = self.client.get('/').wsgi_request
        request.session = session
        
        cart = get_or_create_cart(request)
        self.assertIsNone(cart.user)
        self.assertEqual(cart.session_key, session.session_key)

    def test_add_to_cart_success(self):
        """Test successfully adding item to cart."""
        self.client.force_login(self.user)
        request = self.client.get('/').wsgi_request
        request.user = self.user
        
        result = add_to_cart(request, self.menu_item.id, 2)
        
        self.assertTrue(result['success'])
        self.assertIn('added to cart', result['message'])
        self.assertEqual(result['cart_total_items'], 2)
        self.assertEqual(result['item_quantity'], 2)

    def test_add_to_cart_update_existing(self):
        """Test adding item that already exists in cart (should update quantity)."""
        self.client.force_login(self.user)
        request = self.client.get('/').wsgi_request
        request.user = self.user
        
        # Add item first time
        add_to_cart(request, self.menu_item.id, 1)
        
        # Add same item again
        result = add_to_cart(request, self.menu_item.id, 2)
        
        self.assertTrue(result['success'])
        self.assertIn('updated', result['message'])
        self.assertEqual(result['item_quantity'], 3)  # 1 + 2 = 3

    def test_add_to_cart_unavailable_item(self):
        """Test adding unavailable item to cart."""
        self.client.force_login(self.user)
        request = self.client.get('/').wsgi_request
        request.user = self.user
        
        result = add_to_cart(request, self.unavailable_item.id, 1)
        
        self.assertFalse(result['success'])
        self.assertIn('unavailable', result['error'])

    def test_add_to_cart_invalid_quantity(self):
        """Test adding item with invalid quantity."""
        self.client.force_login(self.user)
        request = self.client.get('/').wsgi_request
        request.user = self.user
        
        result = add_to_cart(request, self.menu_item.id, 0)
        
        self.assertFalse(result['success'])
        self.assertIn('greater than 0', result['error'])

    def test_remove_from_cart_success(self):
        """Test successfully removing item from cart."""
        self.client.force_login(self.user)
        request = self.client.get('/').wsgi_request
        request.user = self.user
        
        # Add item first
        add_to_cart(request, self.menu_item.id, 2)
        
        # Remove item
        result = remove_from_cart(request, self.menu_item.id)
        
        self.assertTrue(result['success'])
        self.assertIn('removed from cart', result['message'])
        self.assertEqual(result['cart_total_items'], 0)

    def test_remove_from_cart_item_not_found(self):
        """Test removing item that's not in cart."""
        self.client.force_login(self.user)
        request = self.client.get('/').wsgi_request
        request.user = self.user
        
        result = remove_from_cart(request, self.menu_item.id)
        
        self.assertFalse(result['success'])
        self.assertIn('not found in cart', result['error'])

    def test_update_cart_item_quantity_success(self):
        """Test successfully updating cart item quantity."""
        self.client.force_login(self.user)
        request = self.client.get('/').wsgi_request
        request.user = self.user
        
        # Add item first
        add_to_cart(request, self.menu_item.id, 2)
        
        # Update quantity
        result = update_cart_item_quantity(request, self.menu_item.id, 5)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['item_quantity'], 5)
        self.assertEqual(result['cart_total_items'], 5)

    def test_update_cart_item_quantity_zero_removes_item(self):
        """Test updating quantity to 0 removes item."""
        self.client.force_login(self.user)
        request = self.client.get('/').wsgi_request
        request.user = self.user
        
        # Add item first
        add_to_cart(request, self.menu_item.id, 2)
        
        # Update quantity to 0
        result = update_cart_item_quantity(request, self.menu_item.id, 0)
        
        self.assertTrue(result['success'])
        self.assertIn('removed from cart', result['message'])
        self.assertEqual(result['cart_total_items'], 0)

    def test_clear_cart_success(self):
        """Test successfully clearing cart."""
        self.client.force_login(self.user)
        request = self.client.get('/').wsgi_request
        request.user = self.user
        
        # Add items first
        add_to_cart(request, self.menu_item.id, 3)
        
        # Clear cart
        result = clear_cart(request)
        
        self.assertTrue(result['success'])
        self.assertIn('Cart cleared', result['message'])
        self.assertEqual(result['cart_total_items'], 0)

    def test_get_cart_summary_empty(self):
        """Test getting summary of empty cart."""
        self.client.force_login(self.user)
        request = self.client.get('/').wsgi_request
        request.user = self.user
        
        result = get_cart_summary(request)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['total_items'], 0)
        self.assertEqual(result['total_price'], '0')
        self.assertEqual(len(result['items']), 0)

    def test_get_cart_summary_with_items(self):
        """Test getting summary of cart with items."""
        self.client.force_login(self.user)
        request = self.client.get('/').wsgi_request
        request.user = self.user
        
        # Add items
        add_to_cart(request, self.menu_item.id, 2)
        
        result = get_cart_summary(request)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['total_items'], 2)
        self.assertEqual(len(result['items']), 1)
        self.assertEqual(result['items'][0]['name'], self.menu_item.name)
        self.assertEqual(result['items'][0]['quantity'], 2)


class CartAPITests(TestCase):
    """Test shopping cart API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner_name='Test Owner',
            email='owner@test.com',
            phone_number='555-1234'
        )
        
        self.category = MenuCategory.objects.create(name='Main Course')
        
        self.menu_item = MenuItem.objects.create(
            name='Test Item',
            description='Test description',
            price=Decimal('10.99'),
            restaurant=self.restaurant,
            category=self.category,
            is_available=True
        )
        
        self.api_client = APIClient()

    def test_cart_summary_api_authenticated(self):
        """Test cart summary API for authenticated user."""
        self.api_client.force_authenticate(user=self.user)
        
        url = reverse('cart-summary')
        response = self.api_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['total_items'], 0)

    def test_cart_summary_api_anonymous(self):
        """Test cart summary API for anonymous user."""
        url = reverse('cart-summary')
        response = self.api_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['total_items'], 0)

    def test_add_to_cart_api_success(self):
        """Test adding item to cart via API."""
        self.api_client.force_authenticate(user=self.user)
        
        url = reverse('add-to-cart')
        data = {
            'menu_item_id': self.menu_item.id,
            'quantity': 2
        }
        response = self.api_client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['cart_total_items'], 2)

    def test_add_to_cart_api_missing_menu_item_id(self):
        """Test adding item without menu_item_id."""
        self.api_client.force_authenticate(user=self.user)
        
        url = reverse('add-to-cart')
        data = {'quantity': 2}
        response = self.api_client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('required', response.data['error'])

    def test_add_to_cart_api_invalid_quantity(self):
        """Test adding item with invalid quantity."""
        self.api_client.force_authenticate(user=self.user)
        
        url = reverse('add-to-cart')
        data = {
            'menu_item_id': self.menu_item.id,
            'quantity': 'invalid'
        }
        response = self.api_client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('Invalid quantity', response.data['error'])

    def test_remove_from_cart_api_success(self):
        """Test removing item from cart via API."""
        self.api_client.force_authenticate(user=self.user)
        
        # Add item first
        add_url = reverse('add-to-cart')
        add_data = {'menu_item_id': self.menu_item.id, 'quantity': 1}
        self.api_client.post(add_url, add_data, format='json')
        
        # Remove item
        remove_url = reverse('remove-from-cart', kwargs={'menu_item_id': self.menu_item.id})
        response = self.api_client.delete(remove_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['cart_total_items'], 0)

    def test_update_cart_item_api_success(self):
        """Test updating cart item quantity via API."""
        self.api_client.force_authenticate(user=self.user)
        
        # Add item first
        add_url = reverse('add-to-cart')
        add_data = {'menu_item_id': self.menu_item.id, 'quantity': 1}
        self.api_client.post(add_url, add_data, format='json')
        
        # Update quantity
        update_url = reverse('update-cart-item', kwargs={'menu_item_id': self.menu_item.id})
        update_data = {'quantity': 5}
        response = self.api_client.put(update_url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['cart_total_items'], 5)

    def test_clear_cart_api_success(self):
        """Test clearing cart via API."""
        self.api_client.force_authenticate(user=self.user)
        
        # Add item first
        add_url = reverse('add-to-cart')
        add_data = {'menu_item_id': self.menu_item.id, 'quantity': 3}
        self.api_client.post(add_url, add_data, format='json')
        
        # Clear cart
        clear_url = reverse('clear-cart')
        response = self.api_client.delete(clear_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['cart_total_items'], 0)


class HomeViewCartTests(TestCase):
    """Test cart integration in home view."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner_name='Test Owner',
            email='owner@test.com',
            phone_number='555-1234'
        )
        
        self.menu_item = MenuItem.objects.create(
            name='Test Item',
            description='Test description',
            price=Decimal('10.99'),
            restaurant=self.restaurant,
            is_available=True
        )
        
        self.client = Client()

    def test_home_view_cart_count_anonymous(self):
        """Test that home view includes cart count for anonymous users."""
        response = self.client.get(reverse('home'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('cart_total_items', response.context)
        self.assertEqual(response.context['cart_total_items'], 0)
        self.assertContains(response, 'Cart: 0 items')

    def test_home_view_cart_count_authenticated(self):
        """Test that home view includes cart count for authenticated users."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('home'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('cart_total_items', response.context)
        self.assertEqual(response.context['cart_total_items'], 0)
        self.assertContains(response, 'Cart: 0 items')

    def test_home_view_cart_count_with_items(self):
        """Test home view shows correct cart count when items are present."""
        self.client.force_login(self.user)
        
        # Add items to cart
        request = self.client.get('/').wsgi_request
        request.user = self.user
        add_to_cart(request, self.menu_item.id, 3)
        
        response = self.client.get(reverse('home'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cart: 3 items')