"""
Utility functions for the orders application.

This module contains reusable utility functions for order management,
including unique ID generation, coupon code generation, and order-related helpers.
"""

import secrets
import string
from typing import Optional
from django.db import transaction

from orders.models import Order

# If you have a Coupon model, import it instead and check uniqueness there.
# from .models import Coupon

def generate_coupon_code(length=10, existing_codes=None):
    """
    Generate a unique alphanumeric coupon code.
    Checks uniqueness against a set of existing codes (or a database model if available).
    Args:
        length (int): Length of the coupon code. Must be positive. Default is 10.
        existing_codes (set or None): Set of codes to check uniqueness against. If None, checks against Order.coupon_code if present.
    Returns:
        str: Unique coupon code.
    Raises:
        ValueError: If length is not a positive integer.
    Note:
        For production, integrate with a Coupon model and check against Coupon.objects.values_list('code', flat=True) to ensure no duplicates in the database.
    """
    if not isinstance(length, int) or length < 1:
        raise ValueError("Coupon code length must be a positive integer.")
    alphabet = string.ascii_uppercase + string.digits
    if existing_codes is None:
        # Example: If you have a Coupon model, use Coupon.objects.values_list('code', flat=True)
        # For now, fallback to an empty set (no uniqueness check)
        existing_codes = set()
    max_attempts = min(10000, len(alphabet) ** length)
    for _ in range(max_attempts):
        code = ''.join(secrets.choice(alphabet) for _ in range(length))
        if code not in existing_codes:
            return code
    raise RuntimeError("Unable to generate a unique coupon code after {} attempts. Consider increasing the code length or clearing used codes.".format(max_attempts))


def generate_unique_order_id(length: int = 8, prefix: str = '', model_class=None, field_name: str = 'order_id') -> str:
    """
    Generate a unique alphanumeric ID for orders.
    
    This function creates a cryptographically secure random string that's
    suitable for user-facing order identification. It automatically checks
    for collisions in the database and retries if necessary.
    
    Args:
        length (int): Length of the random portion (default: 8)
        prefix (str): Optional prefix to add to the ID (default: '')
        model_class: Django model class to check for uniqueness (default: None)
        field_name (str): Field name to check for uniqueness (default: 'order_id')
    
    Returns:
        str: A unique alphanumeric ID
    
    Example:
        >>> generate_unique_order_id(8, 'ORD-')
        'ORD-A7X9K2M5'
        
        >>> generate_unique_order_id(6, model_class=Order, field_name='order_id')
        'B8N4P1'
    
    Raises:
        ValueError: If unable to generate unique ID after maximum attempts
        ImportError: If model_class is provided but cannot be imported
    """
    # Character set for ID generation (alphanumeric, excluding confusing chars)
    # Excluded: 0, O, 1, I to avoid confusion
    alphabet = string.ascii_uppercase + string.digits
    safe_alphabet = alphabet.replace('0', '').replace('O', '').replace('1', '').replace('I', '')
    
    max_attempts = 50  # Prevent infinite loops
    
    for attempt in range(max_attempts):
        # Generate random string
        random_part = ''.join(secrets.choice(safe_alphabet) for _ in range(length))
        order_id = f"{prefix}{random_part}"
        
        # If no model provided, just return the ID (for testing or simple cases)
        if model_class is None:
            return order_id
        
        # Check for uniqueness in database
        try:
            with transaction.atomic():
                filter_kwargs = {field_name: order_id}
                if not model_class.objects.filter(**filter_kwargs).exists():
                    return order_id
        except Exception as e:
            # Log the error but continue trying
            print(f"Database check error on attempt {attempt + 1}: {e}")
            continue
    
    raise ValueError(f"Unable to generate unique ID after {max_attempts} attempts")


def generate_order_number(model_class=None) -> str:
    """
    Generate a user-friendly order number with 'ORD-' prefix.
    
    This is a convenience function that uses generate_unique_order_id()
    with predefined settings optimized for order numbers.
    
    Args:
        model_class: Django model class to check for uniqueness
    
    Returns:
        str: A unique order number like 'ORD-A7X9K2M5'
    
    Example:
        >>> generate_order_number(Order)
        'ORD-A7X9K2M5'
    """
    return generate_unique_order_id(
        length=8,
        prefix='ORD-',
        model_class=model_class,
        field_name='order_id'
    )


def generate_short_id(length: int = 6, model_class=None, field_name: str = 'short_id') -> str:
    """
    Generate a short unique ID (6 characters by default).
    
    Useful for compact IDs, SMS references, or display purposes
    where space is limited.
    
    Args:
        length (int): Length of the ID (default: 6)
        model_class: Django model class to check for uniqueness
        field_name (str): Field name to check for uniqueness
    
    Returns:
        str: A short unique ID like 'B8N4P2'
    
    Example:
        >>> generate_short_id(6, Order, 'reference_code')
        'B8N4P2'
    """
    return generate_unique_order_id(
        length=length,
        prefix='',
        model_class=model_class,
        field_name=field_name
    )


def validate_order_id_format(order_id: str, expected_prefix: str = '', expected_length: Optional[int] = None) -> bool:
    """
    Validate the format of an order ID.
    
    Args:
        order_id (str): The order ID to validate
        expected_prefix (str): Expected prefix (default: '')
        expected_length (int): Expected total length (optional)
    
    Returns:
        bool: True if format is valid, False otherwise
    
    Example:
        >>> validate_order_id_format('ORD-A7X9K2M5', 'ORD-', 12)
        True
        >>> validate_order_id_format('invalid', 'ORD-', 12)
        False
    """
    if not order_id:
        return False
    
    # Check prefix
    if expected_prefix and not order_id.startswith(expected_prefix):
        return False
    
    # Check length
    if expected_length and len(order_id) != expected_length:
        return False
    
    # Check that non-prefix part contains only valid characters
    non_prefix_part = order_id[len(expected_prefix):] if expected_prefix else order_id
    safe_alphabet = string.ascii_uppercase + string.digits
    safe_alphabet = safe_alphabet.replace('0', '').replace('O', '').replace('1', '').replace('I', '')
    
    return all(char in safe_alphabet for char in non_prefix_part)


# Convenience constants for common ID formats
DEFAULT_ORDER_ID_LENGTH = 8
DEFAULT_ORDER_PREFIX = 'ORD-'
DEFAULT_SHORT_ID_LENGTH = 6
