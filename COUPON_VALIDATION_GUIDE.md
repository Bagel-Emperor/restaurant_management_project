# Order Coupon Validation - Implementation Summary

## Overview
This document describes the coupon validation system implemented for the Order model to prevent misuse and ensure data integrity.

## Protections Implemented

### 1. **Only One Coupon Per Order** ✅
- **Implementation**: ForeignKey relationship (not ManyToMany)
- **Effect**: An order can only have ONE coupon assigned at a time
- **Database**: Enforced at the schema level with a single `coupon_id` foreign key column

### 2. **Cannot Change Coupon on Finalized Orders** ✅
- **Implementation**: Validation in `Order.clean()` method
- **Prevents**: Changing or removing coupons on orders with status:
  - `Completed`
  - `Cancelled`
- **Error Message**: "Cannot change coupon on completed/cancelled orders."
- **Use Case**: Prevents fraudulent discount changes after order is finalized

### 3. **Coupon Must Be Valid When Assigned** ✅
- **Implementation**: Validation in `Order.clean()` method
- **Checks Performed**:
  - ✓ Coupon is active (`is_active=True`)
  - ✓ Current date is within valid date range (`valid_from` to `valid_until`)
  - ✓ Coupon has not reached usage limit (`usage_count < max_usage`)
- **Validation Flow**: Calls `coupon.can_be_used()` which checks all three conditions

### 4. **Cannot Use Same Coupon Code Multiple Times on Same Order** ✅
- **Implementation**: Single ForeignKey prevents multiple coupon assignments
- **Effect**: Replacing a coupon removes the previous one
- **Example**:
  ```python
  order.coupon = coupon1  # Sets coupon1
  order.coupon = coupon2  # Replaces coupon1 with coupon2 (only one at a time)
  ```

## Code Implementation

### Order Model Changes

#### Added Field
```python
class Order(models.Model):
    # ... existing fields ...
    
    coupon = models.ForeignKey(
        'Coupon',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='orders',
        help_text="Optional coupon for discount on this order"
    )
```

#### Added Validation
```python
def clean(self):
    """
    Custom validation for Order model.
    
    Validates:
    - Coupon cannot be changed on finalized orders (Completed/Cancelled)
    - Coupon must be valid and usable when assigned
    - Only one coupon per order (enforced by ForeignKey)
    """
    super().clean()
    
    # Prevent coupon changes on finalized orders
    if self.pk:
        old_order = Order.objects.get(pk=self.pk)
        if old_order.status.name in [OrderStatusChoices.COMPLETED, OrderStatusChoices.CANCELLED]:
            if old_order.coupon != self.coupon:
                raise ValidationError({'coupon': 'Cannot change coupon...'})
    
    # Validate coupon if assigned
    if self.coupon and not self.coupon.can_be_used():
        # Detailed error messages for inactive/expired/maxed out coupons
        raise ValidationError({'coupon': '...'})
```

#### Updated save() Method
```python
def save(self, *args, **kwargs):
    # ... existing logic ...
    
    # Run validation before saving
    self.full_clean()
    
    super().save(*args, **kwargs)
```

### Utility Function
```python
def calculate_discount(subtotal, coupon):
    """
    Calculate discount amount based on coupon.
    
    - Returns Decimal('0.00') if coupon is None
    - Returns Decimal('0.00') if coupon is invalid
    - Calculates: subtotal × (discount_percentage / 100)
    """
    if coupon is None:
        return Decimal('0.00')
    
    if not coupon.can_be_used():
        return Decimal('0.00')
    
    discount_amount = subtotal * (coupon.discount_percentage / Decimal('100'))
    return discount_amount.quantize(Decimal('0.01'))
```

### Updated calculate_total() Method
```python
def calculate_total(self):
    """Calculate order total with discount applied."""
    from .utils import calculate_discount
    
    # Step 1: Calculate subtotal
    subtotal = sum(item.price * item.quantity 
                   for item in self.order_items.select_related('menu_item'))
    
    # Step 2: Apply discount
    discount_amount = calculate_discount(subtotal, self.coupon)
    
    # Step 3: Return final total
    return max(subtotal - discount_amount, Decimal('0.00'))
```

## Test Results

All validation tests passed successfully:

✅ **Test 1**: One coupon per order (ForeignKey enforcement)
✅ **Test 2**: Cannot change coupon on completed orders  
✅ **Test 3**: Cannot use expired coupon  
✅ **Test 4**: Cannot use inactive coupon  
✅ **Test 5**: Cannot use maxed out coupon  
✅ **Test 6**: Valid coupon works correctly

## Migration
- **Migration**: `0019_order_coupon.py`
- **Operation**: Add `coupon` ForeignKey field to Order model
- **Status**: Applied successfully

## Edge Cases Handled

1. **Coupon is None**: Order total = subtotal (no discount)
2. **Coupon is invalid**: Order total = subtotal (no discount)
3. **Expired coupon**: Validation error prevents order creation
4. **Inactive coupon**: Validation error prevents order creation
5. **Maxed usage coupon**: Validation error prevents order creation
6. **Changing coupon on completed order**: Validation error prevents change
7. **Multiple coupons**: Not possible (single ForeignKey)

## What's NOT Implemented Yet

### ⚠️ Usage Increment
The `Coupon.increment_usage()` method exists but is **not called automatically**.

**Why**: This should be called when an order is **paid/confirmed**, not during calculation.

**Where to implement**: In the payment processing flow (when order moves to "Completed" status).

**Example implementation location**:
```python
# In payment processing view/signal
order.status = OrderStatus.objects.get(name=OrderStatusChoices.COMPLETED)
if order.coupon:
    order.coupon.increment_usage()  # Increment usage count
order.save()
```

## API Usage Example

```python
from orders.models import Order, Coupon
from decimal import Decimal

# Create order with coupon
coupon = Coupon.objects.get(code='SAVE10')
order = Order(
    total_amount=Decimal('100.00'),
    coupon=coupon
)
order.save()  # Validation runs automatically

# Calculate total with discount
total = order.calculate_total()  # Returns Decimal('90.00')

# Try to change coupon on completed order (will fail)
order.status = OrderStatus.objects.get(name='Completed')
order.save()

order.coupon = None
order.save()  # ValidationError: Cannot change coupon on completed orders
```

## Benefits

1. **Data Integrity**: Prevents invalid coupons from being applied
2. **Audit Trail**: Completed orders cannot have coupons changed
3. **Business Logic**: Enforces one-coupon-per-order policy
4. **User Experience**: Clear error messages for invalid coupons
5. **Security**: Prevents coupon manipulation after order finalization

## Related Files

- `orders/models.py` - Order and Coupon models with validation
- `orders/utils.py` - `calculate_discount` utility function
- `orders/migrations/0019_order_coupon.py` - Database migration
- `test_coupon_validation.py` - Comprehensive validation tests
