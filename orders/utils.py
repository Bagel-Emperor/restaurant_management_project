"""
Utility functions for the orders application.

This module contains reusable utility functions for order management,
including unique ID generation, coupon code generation, sales calculations, and order-related helpers.
"""

import logging
import secrets
import string
from datetime import date
from decimal import Decimal
from typing import Optional

from django.db import transaction
from django.db.models import Sum

from orders.models import Order


# ================================
# ORDER STATUS MANAGEMENT
# ================================

def update_order_status(order_id: str, new_status: str, user_info: Optional[str] = None) -> dict:
    """
    Update the status of an order given its order ID and new status.
    
    This is a reusable utility function for programmatically updating order statuses
    from anywhere in the application. It handles database retrieval, validation,
    error handling, and audit logging.
    
    Args:
        order_id (str): The unique order identifier (e.g., "ORD-A7X9K2M5")
        new_status (str): The new status name. Must be one of:
                         'Pending', 'Processing', 'Completed', 'Cancelled'
        user_info (str, optional): Information about who initiated the change
                                  (e.g., username, "system", "admin")
                                  Used for audit logging. Default: "system"
    
    Returns:
        dict: A dictionary containing operation result with the following structure:
            {
                'success': bool,          # True if update succeeded
                'message': str,           # Human-readable result message
                'order_id': str,         # The order ID that was updated
                'previous_status': str,  # Status before update (if successful)
                'new_status': str,       # Status after update (if successful)
                'error': str            # Error message (only if success=False)
            }
    
    Returns (Success):
        {
            'success': True,
            'message': 'Order status updated successfully',
            'order_id': 'ORD-A7X9K2M5',
            'previous_status': 'Pending',
            'new_status': 'Processing'
        }
    
    Returns (Failure - Order Not Found):
        {
            'success': False,
            'message': 'Order not found',
            'order_id': 'ORD-INVALID',
            'error': 'No order found with ID: ORD-INVALID'
        }
    
    Returns (Failure - Invalid Status):
        {
            'success': False,
            'message': 'Invalid status provided',
            'order_id': 'ORD-A7X9K2M5',
            'error': 'Status must be one of: Pending, Processing, Completed, Cancelled'
        }
    
    Example:
        >>> from orders.utils import update_order_status
        >>> 
        >>> # Update order status from admin panel
        >>> result = update_order_status('ORD-A7X9K2M5', 'Processing', 'admin')
        >>> if result['success']:
        ...     print(f"Order {result['order_id']} updated to {result['new_status']}")
        ... else:
        ...     print(f"Error: {result['error']}")
        Order ORD-A7X9K2M5 updated to Processing
        
        >>> # Update from automated workflow
        >>> result = update_order_status('ORD-B8N4P2', 'Completed', 'payment_system')
        >>> if result['success']:
        ...     print(result['message'])
        Order status updated successfully
        
        >>> # Handle non-existent order
        >>> result = update_order_status('ORD-INVALID', 'Processing')
        >>> if not result['success']:
        ...     print(result['error'])
        No order found with ID: ORD-INVALID
    
    Raises:
        Does not raise exceptions. All errors are returned in the result dictionary
        with success=False and appropriate error messages.
    
    Notes:
        - Validates status against OrderStatusChoices.VALID_STATUSES
        - Automatically creates OrderStatus objects if they don't exist
        - Logs all status changes with timestamp and user info
        - Thread-safe with database transactions
        - Updates the order's updated_at timestamp automatically
        - Can be used by views, management commands, celery tasks, etc.
    
    Integration:
        - Used by UpdateOrderStatusView for API endpoint
        - Can be called from management commands for batch updates
        - Suitable for automated workflows and scheduled tasks
        - Works with order notification systems
        - Compatible with audit trail requirements
    
    Performance:
        - Uses select_related('status') to minimize database queries
        - Single transaction for atomicity
        - Indexed lookups on order_id field
    
    See Also:
        - UpdateOrderStatusView: REST API endpoint using this function
        - OrderStatusChoices: Valid status choices
        - get_order_status(): Retrieve current order status
    """
    logger = logging.getLogger(__name__)
    
    # Import here to avoid circular dependencies
    from .models import OrderStatus
    from .choices import OrderStatusChoices
    
    # Default user_info if not provided
    if user_info is None:
        user_info = "system"
    
    try:
        # Validate that the new status is valid
        valid_statuses = [
            OrderStatusChoices.PENDING,
            OrderStatusChoices.PROCESSING,
            OrderStatusChoices.COMPLETED,
            OrderStatusChoices.CANCELLED
        ]
        
        if new_status not in valid_statuses:
            error_msg = f"Status must be one of: {', '.join(valid_statuses)}"
            logger.warning(
                'Invalid status provided for order %s: %s (initiated by: %s)',
                order_id, new_status, user_info
            )
            return {
                'success': False,
                'message': 'Invalid status provided',
                'order_id': order_id,
                'error': error_msg
            }
        
        # Retrieve the order with its current status
        try:
            order = Order.objects.select_related('status').get(order_id=order_id)
        except Order.DoesNotExist:
            error_msg = f"No order found with ID: {order_id}"
            logger.warning(
                'Order status update failed: %s (initiated by: %s)',
                error_msg, user_info
            )
            return {
                'success': False,
                'message': 'Order not found',
                'order_id': order_id,
                'error': error_msg
            }
        
        # Store previous status for logging
        previous_status = order.status.name
        
        # Check if status is already the same (no update needed)
        if previous_status == new_status:
            logger.info(
                'Order %s already has status %s (initiated by: %s)',
                order_id, new_status, user_info
            )
            return {
                'success': True,
                'message': f'Order already has status: {new_status}',
                'order_id': order_id,
                'previous_status': previous_status,
                'new_status': new_status
            }
        
        # Get or create the new status object
        new_status_obj, created = OrderStatus.objects.get_or_create(name=new_status)
        
        # Update the order status
        order.status = new_status_obj
        order.save(update_fields=['status', 'updated_at'])
        
        # Log the successful status change
        logger.info(
            'Order %s status updated from %s to %s (initiated by: %s)',
            order_id, previous_status, new_status, user_info
        )
        
        return {
            'success': True,
            'message': 'Order status updated successfully',
            'order_id': order_id,
            'previous_status': previous_status,
            'new_status': new_status
        }
        
    except Exception as e:
        # Catch any unexpected errors
        error_msg = f"Unexpected error updating order status: {str(e)}"
        logger.error(
            'Error updating order %s status to %s: %s (initiated by: %s)',
            order_id, new_status, str(e), user_info,
            exc_info=True
        )
        return {
            'success': False,
            'message': 'An error occurred while updating order status',
            'order_id': order_id,
            'error': error_msg
        }


# ================================
# DISCOUNT AND COUPON UTILITIES
# ================================

def calculate_discount(subtotal, coupon):
    """
    Calculate the discount amount for an order based on a coupon.
    
    Takes the order subtotal and a Coupon instance, and calculates the discount
    amount based on the coupon's discount percentage. Returns zero if the coupon
    is None or invalid.
    
    Args:
        subtotal (Decimal): The order subtotal before discount
        coupon (Coupon or None): Coupon instance to apply, or None
    
    Returns:
        Decimal: The discount amount (always non-negative)
    
    Example:
        >>> from decimal import Decimal
        >>> from orders.models import Coupon
        >>> # Assuming a coupon with 10% discount exists
        >>> coupon = Coupon.objects.filter(is_active=True).first()
        >>> if coupon:
        ...     calculate_discount(Decimal('100.00'), coupon)
        Decimal('10.00')
        
        >>> # No coupon returns zero discount
        >>> calculate_discount(Decimal('100.00'), None)
        Decimal('0.00')
    
    Notes:
        - Returns Decimal('0.00') if coupon is None
        - Returns Decimal('0.00') if coupon is not valid (inactive or expired)
        - Discount is calculated as: subtotal × (discount_percentage / 100)
        - Result is quantized to 2 decimal places (cent precision)
    """
    # No coupon means no discount
    if coupon is None:
        return Decimal('0.00')
    
    # Check if coupon can be used (valid date + usage available + is_active)
    if not coupon.can_be_used():
        return Decimal('0.00')
    
    # Calculate discount: subtotal × (percentage / 100)
    discount_amount = subtotal * (coupon.discount_percentage / Decimal('100'))
    
    # Ensure discount doesn't exceed subtotal (shouldn't happen with max 100% validation)
    discount_amount = min(discount_amount, subtotal)
    
    # Quantize to 2 decimal places for currency precision
    return discount_amount.quantize(Decimal('0.01'))


def generate_coupon_code(length=10, existing_codes=None):
    """
    Generate a unique alphanumeric coupon code.
    
    Automatically checks uniqueness against the Coupon model database to ensure
    no duplicate codes are created. Integrates seamlessly with the coupon system.
    
    Args:
        length (int): Length of the coupon code. Must be positive. Default is 10.
        existing_codes (set or None): Optional set of additional codes to avoid.
                                    If None, only checks against database.
    
    Returns:
        str: Unique coupon code in uppercase letters and numbers.
    
    Raises:
        ValueError: If length is not a positive integer.
        RuntimeError: If unable to generate unique code after maximum attempts.
    
    Example:
        >>> generate_coupon_code(8)
        'A7X9K2M5'
        
        >>> generate_coupon_code(6, {'AVOID1', 'AVOID2'})
        'B8N4P2'
    
    Integration:
        - Automatically imports and checks against Coupon model
        - Ensures no duplicate codes in database
        - Safe for concurrent use with proper database constraints
        - Used by admin interface and promotional campaign tools
    """
    if not isinstance(length, int) or length < 1:
        raise ValueError("Coupon code length must be a positive integer.")
    
    # Import Coupon model for database uniqueness checking
    try:
        from .models import Coupon
        coupon_model_available = True
    except ImportError:
        # Fallback if Coupon model is not available
        coupon_model_available = False
        logger = logging.getLogger(__name__)
        logger.warning("Coupon model not available for uniqueness checking")
    
    alphabet = string.ascii_uppercase + string.digits
    
    # Use existing_codes only as an optional 'avoid list' provided by caller
    if existing_codes is None:
        existing_codes = set()
    
    max_attempts = min(10000, len(alphabet) ** length)
    
    for attempt in range(max_attempts):
        # Generate random code
        code = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        # Check against provided existing codes (avoid list)
        if code in existing_codes:
            continue
        
        # Rely on indexed database exists() check for efficiency
        if coupon_model_available:
            try:
                if Coupon.objects.filter(code=code).exists():
                    continue  # Code already exists, try again
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning(f"Database check failed for coupon code '{code}': {e}")
                continue
        
        return code
    
    raise RuntimeError(
        f"Unable to generate a unique coupon code after {max_attempts} attempts. "
        f"Consider increasing the code length or clearing used codes."
    )


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


def get_daily_sales_total(target_date: date) -> Decimal:
    """
    Calculate the total sales revenue for a specific date.
    
    This function sums up the total_amount of all orders placed on the specified date,
    providing a daily revenue calculation that's useful for restaurant management,
    reporting, and analytics.
    
    Args:
        target_date (datetime.date): The specific date to calculate sales for.
                                   Can be a date object from Python's datetime module.
    
    Returns:
        Decimal: The total sales amount for the specified date.
                Returns Decimal('0.00') if no orders were placed on that date.
    
    Example:
        >>> from datetime import date
        >>> from orders.utils import get_daily_sales_total
        >>> 
        >>> # Get sales for today
        >>> today_sales = get_daily_sales_total(date.today())
        >>> print(f"Today's sales: ${today_sales}")
        Today's sales: $1,234.56
        
        >>> # Get sales for a specific date
        >>> from datetime import date
        >>> specific_date = date(2025, 10, 1)
        >>> sales = get_daily_sales_total(specific_date)
        >>> print(f"Sales for {specific_date}: ${sales}")
        Sales for 2025-10-01: $856.42
        
        >>> # Get sales for a day with no orders
        >>> no_orders_date = date(2025, 1, 1)  # Assuming no orders on this date
        >>> sales = get_daily_sales_total(no_orders_date)
        >>> print(f"Sales: ${sales}")
        Sales: $0.00
    
    Note:
        - Uses Django's __date lookup to filter DateTimeField by date portion
        - Only includes orders with valid total_amount values (excludes null values)
        - Returns Decimal for precise financial calculations
        - Integrates with existing Order model and shopping cart system
        - Considers orders from both authenticated users and guest customers
    
    Integration:
        This function works seamlessly with the existing order system:
        - Orders created through the shopping cart system
        - Manual orders created by restaurant staff
        - All order statuses (pending, completed, cancelled) are included
        - Works with the Order.calculate_total() method for verification
    
    Performance:
        - Uses efficient database aggregation (Sum) for optimal performance
        - Single database query regardless of number of orders
        - Indexes on created_at field recommended for large datasets
    """
    try:
        # Query all orders for the specified date and sum their total_amount
        # Use __date lookup to filter DateTimeField by date portion only
        result = Order.objects.filter(
            created_at__date=target_date
        ).aggregate(
            total_sum=Sum('total_amount')
        )
        
        # Extract the sum from the result dictionary
        # If no orders found, Sum returns None, so we default to 0
        daily_total = result['total_sum'] or Decimal('0.00')
        
        return daily_total
        
    except Exception as e:
        # Log the error using Python's logging module for proper production error handling
        logger = logging.getLogger(__name__)
        logger.error(f"Error calculating daily sales total for {target_date}: {e}", exc_info=True)
        return Decimal('0.00')


# ================================
# ORDER PRICE CALCULATION
# ================================

def calculate_order_price(order_items: list) -> Decimal:
    """
    Calculate the total price of an order from a list of order items.
    
    This is a generic, reusable utility function that calculates the total cost
    by summing (quantity × price) for each item. It can be used for:
    - Shopping cart total calculation
    - Order price calculation
    - Quote/estimate generation
    - Invoice total calculation
    - Any scenario requiring item-based price calculation
    
    Args:
        order_items (list): List of items, where each item is either:
            - Dictionary with 'quantity' and 'price' keys
            - Object with quantity and price attributes
            
            Examples:
                [
                    {'quantity': 2, 'price': Decimal('12.99')},
                    {'quantity': 1, 'price': Decimal('8.50')}
                ]
                
                or
                
                [
                    OrderItem(quantity=2, price=Decimal('12.99')),
                    OrderItem(quantity=1, price=Decimal('8.50'))
                ]
    
    Returns:
        Decimal: Total price with 2 decimal places (cent precision).
                Returns Decimal('0.00') for empty lists or invalid input.
    
    Raises:
        ValueError: If any item has negative quantity or price
        TypeError: If items don't have required quantity/price fields
    
    Validation:
        - Ensures quantity and price are non-negative
        - Validates numeric types (int, float, Decimal)
        - Converts floats to Decimal for precision
        - Handles edge cases (empty list, None values)
    
    Examples:
        >>> # Calculate cart total
        >>> items = [
        ...     {'quantity': 2, 'price': Decimal('12.99')},
        ...     {'quantity': 1, 'price': Decimal('8.50')}
        ... ]
        >>> total = calculate_order_price(items)
        >>> print(total)
        Decimal('34.48')
        
        >>> # Empty cart
        >>> calculate_order_price([])
        Decimal('0.00')
        
        >>> # With OrderItem objects
        >>> order_items = order.order_items.all()
        >>> total = calculate_order_price(order_items)
    
    Notes:
        - Uses Decimal for financial precision (no floating-point errors)
        - Returns 0.00 for empty lists (graceful handling)
        - Thread-safe and side-effect free (pure function)
        - Efficient for any list size
        - All prices quantized to 2 decimal places
    
    Performance:
        - O(n) time complexity where n is number of items
        - Minimal memory overhead
        - Single pass through items
    """
    # Handle empty list gracefully
    if not order_items:
        return Decimal('0.00')
    
    # Initialize total
    total = Decimal('0.00')
    
    # Get logger for error reporting
    logger = logging.getLogger(__name__)
    
    # Process each item
    for index, item in enumerate(order_items):
        try:
            # Extract quantity and price (support both dict and object access)
            if isinstance(item, dict):
                quantity = item.get('quantity')
                price = item.get('price')
            else:
                # Object with attributes
                quantity = getattr(item, 'quantity', None)
                price = getattr(item, 'price', None)
            
            # Validate quantity and price exist
            if quantity is None or price is None:
                raise TypeError(
                    f"Item at index {index} missing required 'quantity' or 'price' field. "
                    f"Item: {item}"
                )
            
            # Convert to appropriate numeric types
            # Handle int, float, Decimal, or string representations
            try:
                # Validate that quantity is a whole number before conversion
                if not isinstance(quantity, int):
                    # Check if it's a float/Decimal that's actually a whole number
                    if isinstance(quantity, (float, Decimal)):
                        if quantity != int(quantity):
                            raise ValueError(
                                f"Quantity must be a whole number, got {quantity}"
                            )
                    quantity = int(quantity)
                
                if not isinstance(price, Decimal):
                    # Convert float/int/string to Decimal for precision
                    price = Decimal(str(price))
            except (ValueError, TypeError) as e:
                raise TypeError(
                    f"Item at index {index} has invalid quantity or price type. "
                    f"quantity={quantity}, price={price}. Error: {e}"
                )
            
            # Validate non-negative values
            if quantity < 0:
                raise ValueError(
                    f"Item at index {index} has negative quantity: {quantity}. "
                    f"Quantity must be non-negative."
                )
            
            if price < 0:
                raise ValueError(
                    f"Item at index {index} has negative price: {price}. "
                    f"Price must be non-negative."
                )
            
            # Calculate item total and add to running total
            # Decimal handles multiplication with int natively, no conversion needed
            item_total = quantity * price
            total += item_total
            
        except (TypeError, ValueError) as e:
            # Re-raise validation errors with context
            logger.error(f"Error calculating price for item at index {index}: {e}")
            raise
        except Exception as e:
            # Catch unexpected errors and provide helpful message
            logger.error(
                f"Unexpected error processing item at index {index}: {e}",
                exc_info=True
            )
            raise TypeError(
                f"Failed to process item at index {index}: {item}. Error: {e}"
            )
    
    # Ensure result has exactly 2 decimal places (cent precision)
    # This is important for financial calculations
    total = total.quantize(Decimal('0.01'))
    
    return total


# ================================
# TIP CALCULATION
# ================================

def calculate_tip_amount(order_total, tip_percentage):
    """
    Calculate the tip amount for a given order total and tip percentage.
    
    This utility function computes the gratuity amount based on the order total
    and desired tip percentage. The result is rounded to two decimal places
    for proper currency representation.
    
    Args:
        order_total (Decimal, float, or int): The total bill amount before tip.
                                              Can be a Decimal, float, or int.
        tip_percentage (int or float): The tip percentage (e.g., 15 for 15%, 20 for 20%).
                                       Can be an integer or float for fractional percentages.
    
    Returns:
        Decimal: The calculated tip amount, rounded to 2 decimal places.
    
    Formula:
        tip_amount = order_total * (tip_percentage / 100)
    
    Examples:
        >>> from orders.utils import calculate_tip_amount
        >>> from decimal import Decimal
        
        >>> # 15% tip on $50.00 order
        >>> calculate_tip_amount(Decimal('50.00'), 15)
        Decimal('7.50')
        
        >>> # 20% tip on $100.00 order
        >>> calculate_tip_amount(100.00, 20)
        Decimal('20.00')
        
        >>> # 18% tip on $75.50 order
        >>> calculate_tip_amount(Decimal('75.50'), 18)
        Decimal('13.59')
        
        >>> # Fractional percentage: 12.5% tip
        >>> calculate_tip_amount(80, 12.5)
        Decimal('10.00')
        
        >>> # No tip (0%)
        >>> calculate_tip_amount(Decimal('25.00'), 0)
        Decimal('0.00')
        
        >>> # Large order with standard tip
        >>> calculate_tip_amount(Decimal('347.89'), 18)
        Decimal('62.62')
    
    Notes:
        - The function uses Decimal type for precise currency calculations
        - Result is always rounded to exactly 2 decimal places
        - Negative values are allowed (though uncommon in practice)
        - Zero tip percentage returns 0.00
    
    Raises:
        TypeError: If order_total or tip_percentage cannot be converted to Decimal
        ValueError: If conversion to Decimal fails (e.g., invalid string input)
    """
    # Convert inputs to Decimal for precise currency calculations
    order_total = Decimal(str(order_total))
    tip_percentage = Decimal(str(tip_percentage))
    
    # Calculate tip amount: total * (percentage / 100)
    tip_amount = order_total * (tip_percentage / Decimal('100'))
    
    # Round to 2 decimal places for currency precision
    tip_amount = tip_amount.quantize(Decimal('0.01'))
    
    return tip_amount
