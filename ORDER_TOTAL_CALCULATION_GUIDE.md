# Order Total Calculation with Discounts - Complete Guide

## Overview
This guide documents the `Order.calculate_total()` method which calculates order totals with optional coupon discount support. The method automatically validates coupons and applies appropriate discounts when available.

## Implementation

### Method: `Order.calculate_total()`

```python
def calculate_total(self):
    """
    Calculate the total cost of the order based on associated order items.
    
    This method calculates the order total in two steps:
    1. Calculate the subtotal (sum of all item prices × quantities)
    2. Apply any discount from an associated coupon
    
    The discount is calculated using the calculate_discount utility function,
    which validates the coupon and applies the appropriate discount percentage.
    
    Returns:
        Decimal: The final total cost after applying any discount.
                Returns 0 if no items are associated with the order.
    """
    from .utils import calculate_discount
    
    # Calculate subtotal from all order items
    subtotal = Decimal('0.00')
    
    for item in self.order_items.select_related('menu_item'):
        item_total = item.price * item.quantity
        subtotal += item_total
    
    # Apply discount if coupon is present
    discount_amount = calculate_discount(subtotal, self.coupon)
    
    # Calculate final total
    final_total = subtotal - discount_amount
    
    # Ensure total is never negative
    final_total = max(final_total, Decimal('0.00'))
    
    return final_total
```

### Utility: `calculate_discount(subtotal, coupon)`

```python
def calculate_discount(subtotal, coupon):
    """
    Calculate the discount amount for an order based on a coupon.
    
    Args:
        subtotal (Decimal): The order subtotal before discount
        coupon (Coupon or None): Coupon instance to apply, or None
    
    Returns:
        Decimal: The discount amount (always non-negative)
    """
    # No coupon means no discount
    if coupon is None:
        return Decimal('0.00')
    
    # Check if coupon can be used (valid date + usage available + is_active)
    if not coupon.can_be_used():
        return Decimal('0.00')
    
    # Calculate discount: subtotal × (percentage / 100)
    discount_amount = subtotal * (coupon.discount_percentage / Decimal('100'))
    
    # Ensure discount doesn't exceed subtotal
    discount_amount = min(discount_amount, subtotal)
    
    # Quantize to 2 decimal places for currency precision
    return discount_amount.quantize(Decimal('0.01'))
```

## How It Works

### Step 1: Calculate Subtotal
1. Iterate through all `OrderItem` instances associated with the order
2. For each item, calculate: `price × quantity`
3. Sum all item totals to get the subtotal
4. Uses `select_related('menu_item')` to prevent N+1 queries

### Step 2: Apply Discount
1. Check if order has an associated coupon
2. Validate coupon using `coupon.can_be_used()`:
   - ✓ Is active (`is_active=True`)
   - ✓ Current date within valid range (`valid_from` to `valid_until`)
   - ✓ Usage limit not exceeded (`usage_count < max_usage`)
3. If valid, calculate discount: `subtotal × (discount_percentage / 100)`
4. Round to 2 decimal places (cent precision)

### Step 3: Calculate Final Total
1. Subtract discount from subtotal
2. Ensure total is never negative (minimum `$0.00`)
3. Return final total as Decimal

## Usage Examples

### Example 1: Order Without Coupon

```python
from decimal import Decimal
from orders.models import Order, OrderItem, MenuItem

# Create order
order = Order.objects.create(
    status=pending_status,
    total_amount=Decimal('25.00')
)

# Add items
OrderItem.objects.create(
    order=order,
    menu_item=burger,  # $10.00
    quantity=2,
    price=burger.price
)
OrderItem.objects.create(
    order=order,
    menu_item=fries,  # $5.00
    quantity=1,
    price=fries.price
)

# Calculate total
total = order.calculate_total()
# Result: $25.00 (no discount applied)
# Breakdown:
# - 2 × $10.00 = $20.00
# - 1 × $5.00 = $5.00
# - Subtotal: $25.00
# - Discount: $0.00
# - Total: $25.00
```

### Example 2: Order With Valid 10% Coupon

```python
from orders.models import Coupon

# Get coupon
coupon = Coupon.objects.get(code='SAVE10')  # 10% discount

# Create order with coupon
order = Order.objects.create(
    status=pending_status,
    total_amount=Decimal('22.50'),
    coupon=coupon
)

# Add items (same as Example 1)
OrderItem.objects.create(order=order, menu_item=burger, quantity=2, price=burger.price)
OrderItem.objects.create(order=order, menu_item=fries, quantity=1, price=fries.price)

# Calculate total
total = order.calculate_total()
# Result: $22.50
# Breakdown:
# - Subtotal: $25.00
# - Discount: $2.50 (10% of $25.00)
# - Total: $22.50
```

### Example 3: Order With Expired Coupon (No Discount)

```python
# Coupon is expired (valid_until < today)
expired_coupon = Coupon.objects.get(code='EXPIRED20')

# Create order
order = Order.objects.create(
    status=pending_status,
    total_amount=Decimal('25.00')
)

# Manually assign expired coupon (bypassing validation for testing)
Order.objects.filter(pk=order.pk).update(coupon=expired_coupon)
order.refresh_from_db()

# Add items
OrderItem.objects.create(order=order, menu_item=burger, quantity=2, price=burger.price)
OrderItem.objects.create(order=order, menu_item=fries, quantity=1, price=fries.price)

# Calculate total
total = order.calculate_total()
# Result: $25.00 (expired coupon ignored)
# Breakdown:
# - Subtotal: $25.00
# - Discount: $0.00 (coupon is invalid)
# - Total: $25.00
```

### Example 4: Large Order With 50% Discount

```python
# Get 50% off coupon
half_off = Coupon.objects.get(code='HALF OFF')

# Create order
order = Order.objects.create(
    status=pending_status,
    total_amount=Decimal('50.00'),
    coupon=half_off
)

# Add items
OrderItem.objects.create(order=order, menu_item=burger, quantity=10, price=burger.price)

# Calculate total
total = order.calculate_total()
# Result: $50.00
# Breakdown:
# - 10 × $10.00 = $100.00
# - Subtotal: $100.00
# - Discount: $50.00 (50% of $100.00)
# - Total: $50.00
```

### Example 5: Decimal Rounding

```python
# Order with rounding
order = Order.objects.create(
    status=pending_status,
    total_amount=Decimal('8.99'),
    coupon=save10_coupon  # 10% off
)

# Add items
OrderItem.objects.create(order=order, menu_item=item, quantity=3, price=Decimal('3.33'))

# Calculate total
total = order.calculate_total()
# Result: $8.99
# Breakdown:
# - 3 × $3.33 = $9.99
# - Subtotal: $9.99
# - Discount: $1.00 (10% of $9.99 = $0.999, rounded to $1.00)
# - Total: $8.99
```

## Coupon Validation

The `calculate_total()` method automatically validates coupons before applying discounts:

### Valid Coupon Requirements:
1. ✅ **Active**: `coupon.is_active = True`
2. ✅ **Valid Date Range**: `valid_from ≤ today ≤ valid_until`
3. ✅ **Usage Available**: `usage_count < max_usage` (or `max_usage is None`)

### Invalid Coupons (No Discount Applied):
- ❌ Coupon is `None`
- ❌ Coupon is inactive (`is_active=False`)
- ❌ Coupon is expired (`today > valid_until`)
- ❌ Coupon not yet valid (`today < valid_from`)
- ❌ Coupon usage limit reached (`usage_count ≥ max_usage`)

## Test Results

All 8 comprehensive tests passed:

| Test | Scenario | Expected | Actual | Result |
|------|----------|----------|--------|--------|
| 1 | Order with no items | $0.00 | $0.00 | ✅ PASS |
| 2 | Order with items (no coupon) | $25.00 | $25.00 | ✅ PASS |
| 3 | Order with 10% coupon | $22.50 | $22.50 | ✅ PASS |
| 4 | Order with expired coupon | $25.00 | $25.00 | ✅ PASS |
| 5 | Order with inactive coupon | $25.00 | $25.00 | ✅ PASS |
| 6 | Order with maxed out coupon | $25.00 | $25.00 | ✅ PASS |
| 7 | Large order with 50% discount | $50.00 | $50.00 | ✅ PASS |
| 8 | Decimal rounding | $8.99 | $8.99 | ✅ PASS |

## Performance Considerations

### Optimizations:
1. **select_related('menu_item')**: Prevents N+1 query problem when accessing menu item details
2. **Decimal Precision**: Uses `quantize(Decimal('0.01'))` for exact cent precision
3. **Early Return**: Returns `Decimal('0.00')` immediately if no coupon is present
4. **Single Query**: Coupon validation happens in memory (no additional database queries)

### Query Count:
- **Without optimization**: `1 + N` queries (1 for order + N for each order item)
- **With select_related**: `1` query (single JOIN query for all items)

## API Integration Example

```python
from rest_framework.response import Response
from rest_framework.decorators import api_view

@api_view(['GET'])
def order_total(request, order_id):
    """API endpoint to get order total with discount."""
    try:
        order = Order.objects.get(pk=order_id)
        
        # Get breakdown
        subtotal = sum(
            item.price * item.quantity 
            for item in order.order_items.all()
        )
        
        total = order.calculate_total()
        discount = subtotal - total
        
        return Response({
            'order_id': order.order_id,
            'subtotal': str(subtotal),
            'discount': str(discount),
            'total': str(total),
            'coupon_applied': order.coupon.code if order.coupon else None
        })
    except Order.DoesNotExist:
        return Response(
            {'error': 'Order not found'},
            status=404
        )
```

## Error Handling

### Edge Cases Handled:
1. **No Items**: Returns `$0.00`
2. **No Coupon**: Returns subtotal (no discount)
3. **Invalid Coupon**: Returns subtotal (discount = $0.00)
4. **Negative Total**: Ensures minimum of `$0.00` (shouldn't happen with validation)
5. **Rounding**: Always rounds to 2 decimal places for currency

### Not Handled (By Design):
- **Usage Increment**: `Coupon.increment_usage()` exists but is NOT called automatically
  - **Why**: Usage should be incremented when order is paid/confirmed, not during calculation
  - **Where**: Implement in payment processing flow

## Related Documentation

- **COUPON_VALIDATION_GUIDE.md**: Comprehensive coupon validation rules
- **ORDER_MANAGER_GUIDE.md**: Custom OrderManager query methods
- **ORDER_API_GUIDE.md**: Complete REST API documentation

## Files Modified

- `orders/models.py`: Added `coupon` field, `clean()` validation, updated `calculate_total()`
- `orders/utils.py`: Added `calculate_discount()` utility function
- `orders/migrations/0019_order_coupon.py`: Database migration for coupon field

## Testing

Run tests with:
```bash
python test_calculate_total.py
python test_coupon_validation.py
```

All tests pass successfully! ✅
