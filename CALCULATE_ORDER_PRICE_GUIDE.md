# Calculate Order Price Utility Function Guide

## Overview

The `calculate_order_price()` utility function provides a robust, reusable way to calculate the total price of order items. This function handles various input formats, validates data integrity, and ensures precise decimal calculations for financial accuracy.

## Location

**File:** `orders/utils.py`

## Function Signature

```python
def calculate_order_price(order_items: list) -> Decimal
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `order_items` | `list` | Yes | A list of items, where each item can be either a dictionary with `quantity` and `price` keys, or an object with `quantity` and `price` attributes |

## Return Value

Returns a `Decimal` object representing the total price, quantized to 2 decimal places (cents).

- Returns `Decimal('0.00')` for an empty list
- Returns the sum of (quantity × price) for all items

## Features

### ✅ Flexible Input Format

Accepts both dictionaries and objects:

```python
# Dictionary items
items = [
    {'quantity': 2, 'price': 10.50},
    {'quantity': 1, 'price': 5.99}
]

# Object items
class OrderItem:
    def __init__(self, quantity, price):
        self.quantity = quantity
        self.price = price

items = [
    OrderItem(quantity=2, price=10.50),
    OrderItem(quantity=1, price=5.99)
]
```

### ✅ Type Conversion

Automatically converts various numeric types to `Decimal`:
- Integers: `2` → `Decimal('2')`
- Floats: `10.50` → `Decimal('10.50')`
- Strings: `"5.99"` → `Decimal('5.99')`
- Decimal: `Decimal('7.25')` → `Decimal('7.25')`

### ✅ Precision Guarantee

Uses Python's `Decimal` type throughout to avoid floating-point arithmetic errors:

```python
# NO floating-point errors
items = [{'quantity': 3, 'price': 0.1}]
result = calculate_order_price(items)  # Decimal('0.30'), NOT 0.30000000000000004
```

### ✅ Validation

Comprehensive validation prevents invalid data:
- **Negative quantity:** Raises `ValueError`
- **Negative price:** Raises `ValueError`
- **Missing fields:** Raises `TypeError`
- **Invalid types:** Raises `TypeError`

### ✅ Error Handling

Detailed error messages with logging for debugging:

```python
# Negative quantity
items = [{'quantity': -1, 'price': 10.00}]
# Raises: ValueError("Item at index 0 has negative quantity: -1...")

# Missing field
items = [{'quantity': 2}]  # missing 'price'
# Raises: TypeError("Item at index 0 missing required 'quantity' or 'price' field...")
```

## Usage Examples

### Basic Usage

```python
from decimal import Decimal
from orders.utils import calculate_order_price

# Simple order
items = [
    {'quantity': 2, 'price': Decimal('12.99')},
    {'quantity': 1, 'price': Decimal('8.50')}
]

total = calculate_order_price(items)
print(total)  # Decimal('34.48')
```

### Real-World Restaurant Order

```python
from orders.utils import calculate_order_price

# Customer orders: 2 burgers, 1 salad, 3 drinks
order = [
    {'quantity': 2, 'price': 12.99},  # Burgers
    {'quantity': 1, 'price': 8.50},   # Salad
    {'quantity': 3, 'price': 2.50}    # Drinks
]

total = calculate_order_price(order)
print(f"Order total: ${total}")  # Order total: $42.48
```

### Shopping Cart Integration

```python
from home.models import CartItem
from orders.utils import calculate_order_price

def get_cart_total(cart):
    """Calculate the total price for a shopping cart."""
    cart_items = CartItem.objects.filter(cart=cart).select_related('menu_item')
    
    items = [
        {
            'quantity': item.quantity,
            'price': item.menu_item.price
        }
        for item in cart_items
    ]
    
    return calculate_order_price(items)
```

### Order Summary

```python
from orders.models import OrderItem
from orders.utils import calculate_order_price

def recalculate_order_total(order):
    """Recalculate the total for an existing order."""
    order_items = OrderItem.objects.filter(order=order)
    
    # Use the actual OrderItem objects directly
    # (calculate_order_price works with objects that have quantity/price attributes)
    total = calculate_order_price(list(order_items))
    
    order.total_amount = total
    order.save()
    
    return total
```

### Quote Generation

```python
from orders.utils import calculate_order_price

def generate_quote(customer_selections):
    """Generate a price quote before creating an order."""
    items = []
    
    for selection in customer_selections:
        items.append({
            'quantity': selection['qty'],
            'price': selection['unit_price']
        })
    
    subtotal = calculate_order_price(items)
    tax = subtotal * Decimal('0.08')  # 8% tax
    total = subtotal + tax
    
    return {
        'subtotal': subtotal,
        'tax': tax,
        'total': total
    }
```

### Invoice/Receipt Generation

```python
from orders.utils import calculate_order_price

def create_invoice(order_items):
    """Create an invoice with itemized pricing."""
    items_list = []
    
    for item in order_items:
        items_list.append({
            'quantity': item.quantity,
            'price': item.price
        })
    
    subtotal = calculate_order_price(items_list)
    
    invoice = {
        'items': order_items,
        'subtotal': subtotal,
        'tax': subtotal * Decimal('0.08'),
        'total': subtotal * Decimal('1.08')
    }
    
    return invoice
```

## Edge Cases Handled

| Case | Behavior | Example |
|------|----------|---------|
| Empty list | Returns `Decimal('0.00')` | `calculate_order_price([])` → `Decimal('0.00')` |
| Zero quantity | Contributes `0.00` to total | `{'quantity': 0, 'price': 10.00}` → `Decimal('0.00')` |
| Zero price | Contributes `0.00` to total (free item) | `{'quantity': 5, 'price': 0.00}` → `Decimal('0.00')` |
| Large numbers | Handles up to 8 digits + 2 decimals | `{'quantity': 999, 'price': 99999.99}` |
| Mixed types | Converts all to Decimal | `{'quantity': 2, 'price': '10.50'}` |

## Error Scenarios

### Negative Quantity

```python
items = [{'quantity': -1, 'price': 10.00}]
calculate_order_price(items)
# Raises: ValueError("Item at index 0 has negative quantity: -1. Quantity must be non-negative.")
```

### Negative Price

```python
items = [{'quantity': 2, 'price': -5.00}]
calculate_order_price(items)
# Raises: ValueError("Item at index 0 has negative price: -5.00. Price must be non-negative.")
```

### Missing Fields

```python
items = [{'quantity': 2}]  # Missing 'price'
calculate_order_price(items)
# Raises: TypeError("Item at index 0 missing required 'quantity' or 'price' field...")
```

### Invalid Types

```python
items = [{'quantity': 'invalid', 'price': 10.00}]
calculate_order_price(items)
# Raises: TypeError("Item at index 0 has invalid quantity or price type...")
```

## Best Practices

### ✅ DO

- Use `Decimal` for all price values in your application
- Pass lists of dictionaries or objects with `quantity` and `price`
- Handle the exceptions appropriately in your calling code
- Use this function for any order-related price calculations

### ❌ DON'T

- Don't use floats for prices (causes rounding errors)
- Don't pass negative quantities or prices
- Don't modify the returned Decimal object without re-quantizing
- Don't use this for calculations that need more than 2 decimal places

## Testing

A comprehensive test suite with 22 tests validates all functionality:

```bash
# Run tests
python manage.py test tests.test_calculate_order_price --keepdb -v 2
```

Test coverage includes:
- ✅ Dictionary items
- ✅ Object attributes
- ✅ Empty lists
- ✅ Zero values
- ✅ Negative value validation
- ✅ Missing field detection
- ✅ Type conversion
- ✅ Precision maintenance
- ✅ Large numbers
- ✅ Real-world scenarios

## Performance Considerations

- **Time Complexity:** O(n) where n is the number of items
- **Space Complexity:** O(1) (constant space, excluding input)
- **Suitable for:** Up to thousands of items per call

## Related Functions

- `Order.calculate_total()` - Instance method on Order model (uses order items)
- This function is standalone and more flexible for various use cases

## Logging

All errors are logged with detailed context:

```python
logger.error(
    "Item at index %d has negative quantity: %s. Quantity must be non-negative.",
    index,
    quantity
)
```

Check application logs for debugging validation issues.

## Version History

- **v1.0** (Current): Initial implementation with comprehensive validation, type conversion, and error handling

## Support

For issues or questions about this utility function, please:
1. Check the test suite for usage examples: `tests/test_calculate_order_price.py`
2. Review the source code with full documentation: `orders/utils.py`
3. Check application logs for detailed error messages

---

**Last Updated:** December 2024  
**Maintainer:** Restaurant Management System Team
