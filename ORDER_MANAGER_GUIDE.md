# Custom Order Manager - Implementation Guide

## Overview

A custom Django model manager has been implemented for the Order model to provide convenient methods for retrieving orders based on their status. The primary feature is the `get_active_orders()` method that returns only orders with 'pending' or 'processing' status.

## Implementation

### Custom Manager Class

```python
class OrderManager(models.Manager):
    """
    Custom model manager for the Order model.
    Provides convenience methods for retrieving orders based on their status.
    """
    
    def get_active_orders(self):
        """
        Returns a queryset containing only active orders.
        Active orders are defined as having a status of 'pending' or 'processing'.
        
        Returns:
            QuerySet: Orders with status 'pending' or 'processing'
        """
        return self.filter(
            status__name__in=[OrderStatusChoices.PENDING, OrderStatusChoices.PROCESSING]
        )
```

### Order Model Integration

The custom manager is assigned to the Order model:

```python
class Order(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='orders')
    customer = models.ForeignKey('Customer', null=True, blank=True, on_delete=models.SET_NULL, related_name='orders')
    status = models.ForeignKey('OrderStatus', null=False, on_delete=models.PROTECT, related_name='orders')
    total_amount = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Custom model manager
    objects = OrderManager()
```

## Usage Examples

### Basic Usage

```python
# Get all active orders (pending + processing)
active_orders = Order.objects.get_active_orders()

# Print active orders
for order in active_orders:
    print(f"Order {order.id}: {order.status.name} - ${order.total_amount}")
```

### In Django Shell

```bash
python manage.py shell
```

```python
from orders.models import Order

# Get active orders
active_orders = Order.objects.get_active_orders()
print(f"Active orders count: {active_orders.count()}")

# Chain with other QuerySet methods
recent_active = Order.objects.get_active_orders().order_by('-created_at')[:5]
high_value_active = Order.objects.get_active_orders().filter(total_amount__gt=50.00)
```

### In Views

```python
from django.shortcuts import render
from orders.models import Order

def dashboard_view(request):
    """Dashboard showing active orders."""
    active_orders = Order.objects.get_active_orders().select_related('user', 'customer', 'status')
    
    context = {
        'active_orders': active_orders,
        'active_count': active_orders.count()
    }
    return render(request, 'dashboard.html', context)

def kitchen_view(request):
    """Kitchen view showing orders to prepare."""
    orders_to_prepare = Order.objects.get_active_orders().order_by('created_at')
    
    return render(request, 'kitchen.html', {
        'orders': orders_to_prepare
    })
```

### Performance Optimizations

```python
# Use select_related for better performance when accessing related objects
active_orders = Order.objects.get_active_orders().select_related(
    'user', 'customer', 'status'
)

# Prefetch related order items
active_orders_with_items = Order.objects.get_active_orders().prefetch_related(
    'order_items__menu_item'
)

# Filter active orders further
urgent_orders = Order.objects.get_active_orders().filter(
    created_at__lt=timezone.now() - timedelta(hours=1)
)
```

## Status Definitions

Active orders are defined as orders with the following statuses:

| Status | Description | Active |
|--------|-------------|---------|
| Pending | Order received, awaiting processing | ✅ Yes |
| Processing | Order being prepared/fulfilled | ✅ Yes |
| Completed | Order finished and delivered | ❌ No |
| Cancelled | Order cancelled by customer/staff | ❌ No |

## Features

### ✅ **Implemented Features**
- Custom `OrderManager` inheriting from `models.Manager`
- `get_active_orders()` method returning pending and processing orders
- Full Django QuerySet functionality (filtering, ordering, etc.)
- Integration with existing Order model
- Comprehensive unit testing (10 test cases)
- Performance optimizations with select_related/prefetch_related

### 🔧 **Technical Details**
- Uses `status__name__in` filter for efficient database queries
- Returns proper Django QuerySet for chaining operations
- Preserves all Django model manager functionality
- No breaking changes to existing code

### 🧪 **Testing Coverage**
- Basic functionality testing
- Edge cases (empty results, single status types)
- QuerySet properties and behavior
- Integration with related models
- Performance testing with select_related
- Method signature and naming verification

## Database Considerations

### Query Performance
The `get_active_orders()` method generates the following SQL:

```sql
SELECT * FROM orders_order 
INNER JOIN orders_orderstatus ON orders_order.status_id = orders_orderstatus.id 
WHERE orders_orderstatus.name IN ('Pending', 'Processing')
```

### Indexing Recommendations
For optimal performance, consider adding database indexes:

```python
# In OrderStatus model
class OrderStatus(models.Model):
    name = models.CharField(max_length=50, unique=True, db_index=True)  # Add db_index
```

## Future Enhancements

### Possible Extensions
1. **Additional Status Filters**:
   ```python
   def get_completed_orders(self):
       return self.filter(status__name=OrderStatusChoices.COMPLETED)
   
   def get_recent_orders(self, days=7):
       return self.filter(created_at__gte=timezone.now() - timedelta(days=days))
   ```

2. **Customer-Specific Methods**:
   ```python
   def get_customer_active_orders(self, customer):
       return self.get_active_orders().filter(customer=customer)
   ```

3. **Time-Based Filtering**:
   ```python
   def get_overdue_orders(self, hours=2):
       cutoff = timezone.now() - timedelta(hours=hours)
       return self.get_active_orders().filter(created_at__lt=cutoff)
   ```

## Testing

### Run Tests
```bash
# Run all order manager tests
python manage.py test tests.test_order_manager

# Run with verbose output
python manage.py test tests.test_order_manager -v 2

# Run specific test
python manage.py test tests.test_order_manager.OrderManagerTests.test_get_active_orders_returns_pending_and_processing
```

### Test Script
A comprehensive test script is available:
```bash
python test_order_manager.py
```

## Best Practices

### 1. **Use with select_related**
```python
# Good - reduces database queries
active_orders = Order.objects.get_active_orders().select_related('status', 'customer')

# Avoid - causes N+1 query problem
active_orders = Order.objects.get_active_orders()
for order in active_orders:
    print(order.status.name)  # Each access hits database
```

### 2. **Chain with other methods**
```python
# Take advantage of QuerySet chaining
recent_active = Order.objects.get_active_orders().order_by('-created_at')[:10]
high_value = Order.objects.get_active_orders().filter(total_amount__gt=100)
```

### 3. **Handle empty results**
```python
active_orders = Order.objects.get_active_orders()
if active_orders.exists():
    # Process orders
    pass
else:
    # Handle no active orders
    pass
```

## Conclusion

The custom OrderManager successfully provides the requested functionality:

✅ **All Requirements Met:**
- ✅ Custom manager class inheriting from `models.Manager`
- ✅ `get_active_orders()` method returning pending/processing orders
- ✅ Assigned to Order model via `objects = OrderManager()`
- ✅ Tested in Django shell with `Order.objects.get_active_orders()`

The implementation is production-ready with comprehensive testing, performance considerations, and extensive documentation.