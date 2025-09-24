"""
Shopping cart utility functions for managing cart operations.
Supports both session-based carts (anonymous users) and database carts (authenticated users).
"""

from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from .models import Cart, CartItem, MenuItem
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


def get_or_create_cart(request):
    """
    Get or create a cart for the current request.
    Uses database cart for authenticated users, session cart for anonymous users.
    
    Args:
        request: Django request object
    
    Returns:
        Cart: The cart instance for the current user/session
    """
    if request.user.is_authenticated:
        # Database cart for authenticated users
        cart, created = Cart.objects.get_or_create(user=request.user)
        if created:
            logger.info(f"Created new database cart for user {request.user.username}")
        return cart
    else:
        # Session-based cart for anonymous users
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        cart, created = Cart.objects.get_or_create(session_key=session_key)
        if created:
            logger.info(f"Created new session cart for session {session_key}")
        return cart


def add_to_cart(request, menu_item_id, quantity=1):
    """
    Add a menu item to the cart or update its quantity if it already exists.
    
    Args:
        request: Django request object
        menu_item_id: ID of the menu item to add
        quantity: Quantity to add (default: 1)
    
    Returns:
        dict: Success/error message and cart info
    """
    try:
        # Validate inputs
        if quantity <= 0:
            return {'success': False, 'error': 'Quantity must be greater than 0'}
        
        menu_item = get_object_or_404(MenuItem, id=menu_item_id)
        
        # Check if menu item is available
        if not menu_item.is_available:
            return {'success': False, 'error': f'{menu_item.name} is currently unavailable'}
        
        cart = get_or_create_cart(request)
        
        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            menu_item=menu_item,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Item already exists, update quantity
            cart_item.quantity += quantity
            cart_item.save()
            action = 'updated'
        else:
            action = 'added'
        
        logger.info(f"Menu item '{menu_item.name}' {action} to cart (quantity: {cart_item.quantity})")
        
        return {
            'success': True,
            'message': f'{menu_item.name} {action} to cart',
            'cart_total_items': cart.total_items,
            'cart_total_price': str(cart.total_price),
            'item_quantity': cart_item.quantity,
            'item_subtotal': str(cart_item.subtotal)
        }
        
    except MenuItem.DoesNotExist:
        return {'success': False, 'error': 'Menu item not found'}
    except ValidationError as e:
        return {'success': False, 'error': str(e)}
    except Exception as e:
        logger.error(f"Error adding item to cart: {str(e)}")
        return {'success': False, 'error': 'An error occurred while adding item to cart'}


def remove_from_cart(request, menu_item_id):
    """
    Remove a menu item completely from the cart.
    
    Args:
        request: Django request object
        menu_item_id: ID of the menu item to remove
    
    Returns:
        dict: Success/error message and cart info
    """
    try:
        cart = get_or_create_cart(request)
        
        try:
            cart_item = CartItem.objects.get(cart=cart, menu_item_id=menu_item_id)
        except CartItem.DoesNotExist:
            return {'success': False, 'error': 'Item not found in cart'}
        
        item_name = cart_item.menu_item.name
        cart_item.delete()
        
        logger.info(f"Menu item '{item_name}' removed from cart")
        
        return {
            'success': True,
            'message': f'{item_name} removed from cart',
            'cart_total_items': cart.total_items,
            'cart_total_price': str(cart.total_price)
        }
        
    except Exception as e:
        logger.error(f"Error removing item from cart: {str(e)}")
        return {'success': False, 'error': 'An error occurred while removing item from cart'}


def update_cart_item_quantity(request, menu_item_id, quantity):
    """
    Update the quantity of a specific item in the cart.
    
    Args:
        request: Django request object
        menu_item_id: ID of the menu item to update
        quantity: New quantity (if 0, item will be removed)
    
    Returns:
        dict: Success/error message and cart info
    """
    try:
        if quantity < 0:
            return {'success': False, 'error': 'Quantity cannot be negative'}
        
        cart = get_or_create_cart(request)
        
        try:
            cart_item = CartItem.objects.get(cart=cart, menu_item_id=menu_item_id)
        except CartItem.DoesNotExist:
            return {'success': False, 'error': 'Item not found in cart'}
        
        if quantity == 0:
            # Remove item if quantity is 0
            return remove_from_cart(request, menu_item_id)
        
        cart_item.quantity = quantity
        cart_item.save()
        
        logger.info(f"Cart item '{cart_item.menu_item.name}' quantity updated to {quantity}")
        
        return {
            'success': True,
            'message': f'{cart_item.menu_item.name} quantity updated',
            'cart_total_items': cart.total_items,
            'cart_total_price': str(cart.total_price),
            'item_quantity': cart_item.quantity,
            'item_subtotal': str(cart_item.subtotal)
        }
        
    except CartItem.DoesNotExist:
        return {'success': False, 'error': 'Item not found in cart'}
    except ValidationError as e:
        return {'success': False, 'error': str(e)}
    except Exception as e:
        logger.error(f"Error updating cart item quantity: {str(e)}")
        return {'success': False, 'error': 'An error occurred while updating item quantity'}


def clear_cart(request):
    """
    Remove all items from the cart.
    
    Args:
        request: Django request object
    
    Returns:
        dict: Success/error message
    """
    try:
        cart = get_or_create_cart(request)
        items_count = cart.total_items
        cart.clear()
        
        logger.info(f"Cart cleared ({items_count} items removed)")
        
        return {
            'success': True,
            'message': f'Cart cleared ({items_count} items removed)',
            'cart_total_items': 0,
            'cart_total_price': '0.00'
        }
        
    except Exception as e:
        logger.error(f"Error clearing cart: {str(e)}")
        return {'success': False, 'error': 'An error occurred while clearing cart'}


def get_cart_summary(request):
    """
    Get a summary of the current cart contents.
    
    Args:
        request: Django request object
    
    Returns:
        dict: Cart summary with items, totals, and metadata
    """
    try:
        cart = get_or_create_cart(request)
        cart_items = cart.cart_items.select_related('menu_item', 'menu_item__category').all()
        
        items = []
        for item in cart_items:
            items.append({
                'id': item.id,
                'menu_item_id': item.menu_item.id,
                'name': item.menu_item.name,
                'description': item.menu_item.description,
                'price': str(item.menu_item.price),
                'quantity': item.quantity,
                'subtotal': str(item.subtotal),
                'category': item.menu_item.category.name if item.menu_item.category else None,
                'is_available': item.menu_item.is_available
            })
        
        return {
            'success': True,
            'cart_id': cart.id,
            'total_items': cart.total_items,
            'total_price': str(cart.total_price),
            'items': items,
            'created_at': cart.created_at.isoformat(),
            'updated_at': cart.updated_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting cart summary: {str(e)}")
        return {'success': False, 'error': 'An error occurred while retrieving cart information'}


def migrate_session_cart_to_user(request):
    """
    Migrate session-based cart to user cart when user logs in.
    Merges items if user already has a cart.
    
    Args:
        request: Django request object (user must be authenticated)
    
    Returns:
        dict: Migration result
    """
    if not request.user.is_authenticated:
        return {'success': False, 'error': 'User must be authenticated'}
    
    try:
        session_key = request.session.session_key
        if not session_key:
            return {'success': True, 'message': 'No session cart to migrate'}
        
        # Get session cart if it exists
        try:
            session_cart = Cart.objects.get(session_key=session_key)
        except Cart.DoesNotExist:
            return {'success': True, 'message': 'No session cart found'}
        
        # Get or create user cart
        user_cart, created = Cart.objects.get_or_create(user=request.user)
        
        if session_cart.id == user_cart.id:
            # Same cart, just update to remove session_key and set user
            session_cart.user = request.user
            session_cart.session_key = None
            session_cart.save()
            return {'success': True, 'message': 'Cart updated for user'}
        
        # Merge session cart items into user cart
        migrated_items = 0
        for session_item in session_cart.cart_items.all():
            user_cart_item, created = CartItem.objects.get_or_create(
                cart=user_cart,
                menu_item=session_item.menu_item,
                defaults={'quantity': session_item.quantity}
            )
            
            if not created:
                # Item exists in user cart, merge quantities
                user_cart_item.quantity += session_item.quantity
                user_cart_item.save()
            
            migrated_items += 1
        
        # Delete the session cart
        session_cart.delete()
        
        logger.info(f"Migrated {migrated_items} items from session cart to user cart for {request.user.username}")
        
        return {
            'success': True,
            'message': f'Cart migration completed ({migrated_items} items)',
            'migrated_items': migrated_items,
            'cart_total_items': user_cart.total_items,
            'cart_total_price': str(user_cart.total_price)
        }
        
    except Exception as e:
        logger.error(f"Error migrating session cart to user: {str(e)}")
        return {'success': False, 'error': 'An error occurred during cart migration'}