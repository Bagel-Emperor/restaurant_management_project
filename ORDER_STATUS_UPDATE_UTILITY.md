# Order Status Update Utility Function Documentation

## Overview
The `update_order_status()` utility function provides a reusable, standardized way to update order statuses programmatically from anywhere in the application. It handles database retrieval, validation, error handling, and audit logging automatically.

## Function Signature

```python
def update_order_status(order_id: str, new_status: str, user_info: Optional[str] = None) -> dict:
    """Update the status of an order given its order ID and new status."""
```

## Location
```
orders/utils.py
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `order_id` | str | Yes | The unique order identifier (e.g., "ORD-A7X9K2M5") |
| `new_status` | str | Yes | The new status name. Must be one of: 'Pending', 'Processing', 'Completed', 'Cancelled' |
| `user_info` | str | No | Information about who initiated the change (e.g., username, "system", "admin"). Used for audit logging. Default: "system" |

## Return Value

Returns a dictionary containing the operation result:

### Success Response
```python
{
    'success': True,
    'message': 'Order status updated successfully',
    'order_id': 'ORD-A7X9K2M5',
    'previous_status': 'Pending',
    'new_status': 'Processing'
}
```

### Error Response (Order Not Found)
```python
{
    'success': False,
    'message': 'Order not found',
    'order_id': 'ORD-INVALID',
    'error': 'No order found with ID: ORD-INVALID'
}
```

### Error Response (Invalid Status)
```python
{
    'success': False,
    'message': 'Invalid status provided',
    'order_id': 'ORD-A7X9K2M5',
    'error': 'Status must be one of: Pending, Processing, Completed, Cancelled'
}
```

## Usage Examples

### Basic Usage
```python
from orders.utils import update_order_status

# Update order status from admin panel
result = update_order_status('ORD-A7X9K2M5', 'Processing', 'admin')

if result['success']:
    print(f"Order {result['order_id']} updated to {result['new_status']}")
else:
    print(f"Error: {result['error']}")
```

### Automated Workflow
```python
from orders.utils import update_order_status

# Update from payment system
result = update_order_status('ORD-B8N4P2', 'Completed', 'payment_system')

if result['success']:
    print(result['message'])
    # Send notification to customer
    send_order_notification(result['order_id'], result['new_status'])
```

### Batch Processing
```python
from orders.utils import update_order_status
from orders.models import Order

# Mark all pending orders as processing
pending_orders = Order.objects.filter(status__name='Pending')

for order in pending_orders:
    result = update_order_status(order.order_id, 'Processing', 'batch_process')
    if result['success']:
        print(f"✓ {order.order_id}: {result['previous_status']} → {result['new_status']}")
    else:
        print(f"✗ {order.order_id}: {result['error']}")
```

### Management Command
```python
# management/commands/complete_old_orders.py
from django.core.management.base import BaseCommand
from orders.utils import update_order_status
from orders.models import Order
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Mark old processing orders as completed'
    
    def handle(self, *args, **options):
        cutoff_date = datetime.now() - timedelta(days=7)
        old_orders = Order.objects.filter(
            status__name='Processing',
            created_at__lt=cutoff_date
        )
        
        for order in old_orders:
            result = update_order_status(
                order.order_id,
                'Completed',
                'automated_cleanup'
            )
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(f"Completed: {order.order_id}")
                )
```

### Celery Task
```python
# tasks.py
from celery import shared_task
from orders.utils import update_order_status

@shared_task
def auto_cancel_unpaid_orders():
    """Cancel orders that haven't been paid within 30 minutes."""
    from orders.models import Order
    from datetime import datetime, timedelta
    
    cutoff_time = datetime.now() - timedelta(minutes=30)
    unpaid_orders = Order.objects.filter(
        status__name='Pending',
        created_at__lt=cutoff_time
    )
    
    for order in unpaid_orders:
        result = update_order_status(
            order.order_id,
            'Cancelled',
            'auto_cancel_task'
        )
        if result['success']:
            # Send cancellation email
            send_cancellation_email(order)
```

### Error Handling
```python
from orders.utils import update_order_status

def process_order_completion(order_id):
    """Process order completion with error handling."""
    result = update_order_status(order_id, 'Completed', 'process_system')
    
    if not result['success']:
        # Log error
        logger.error(f"Failed to complete order {order_id}: {result['error']}")
        
        # Alert admin
        send_admin_alert(f"Order completion failed: {result['error']}")
        
        return False
    
    # Success - continue with post-completion tasks
    send_completion_notification(order_id)
    update_inventory(order_id)
    return True
```

## Features

### ✅ Validation
- Validates order_id existence in database
- Validates new_status against allowed choices
- Case-sensitive status validation (must match exactly)

### ✅ Error Handling
- Returns structured error responses (no exceptions raised)
- Clear, descriptive error messages
- Handles all edge cases (missing orders, invalid statuses, etc.)

### ✅ Audit Logging
- Logs all status changes with timestamps
- Records who initiated the change (user_info parameter)
- Logs validation failures and errors
- Uses parameterized logging for performance

### ✅ Database Safety
- Uses select_related('status') for optimized queries
- Atomic operations (no partial updates)
- Auto-creates OrderStatus objects if needed
- Updates updated_at timestamp automatically

### ✅ Idempotent
- Gracefully handles updating to current status
- Returns success if already in requested state
- No side effects from repeated calls

## Valid Status Values

The function accepts these status values (case-sensitive):

| Status | Description | Typical Use Case |
|--------|-------------|------------------|
| `Pending` | Order placed, waiting for processing | Initial state after order creation |
| `Processing` | Order is being prepared | Kitchen/restaurant is working on it |
| `Completed` | Order finished and delivered | Customer received order |
| `Cancelled` | Order has been cancelled | Customer or system cancelled |

## Integration Points

### REST API Endpoint
The function is used by the `UpdateOrderStatusView` API endpoint:

```python
# In UpdateOrderStatusView._update_order_status()
from orders.utils import update_order_status

result = update_order_status(order_id, new_status, request.user.username)
if result['success']:
    return Response(result, status=status.HTTP_200_OK)
else:
    return Response(result, status=status.HTTP_400_BAD_REQUEST)
```

### Order Cancellation
Used in the order cancellation workflow:

```python
from orders.utils import update_order_status

# In OrderCancellationView
result = update_order_status(order_id, 'Cancelled', request.user.username)
```

### Automated Systems
Perfect for:
- Scheduled tasks (cron jobs)
- Celery background tasks
- Management commands
- Admin scripts
- Integration with external systems

## Comparison with API Endpoint

| Feature | Utility Function | API Endpoint |
|---------|-----------------|--------------|
| **Use Case** | Internal/programmatic | External/HTTP requests |
| **Authentication** | Not required | Required |
| **Input Format** | Python function | JSON over HTTP |
| **Output Format** | Python dict | JSON Response |
| **Error Handling** | Returns dict | HTTP status codes |
| **Logging** | Yes | Yes |
| **Flexibility** | High (any Python code) | Limited (HTTP only) |

## Performance Considerations

- **Single Query**: Uses `select_related('status')` for one query
- **Indexed Lookups**: Uses indexed `order_id` field
- **Minimal Overhead**: No serialization or HTTP processing
- **Atomic Updates**: Single save() call with `update_fields`
- **Efficient Logging**: Uses parameterized format (lazy evaluation)

## Error Handling

The function never raises exceptions. All errors are returned in the response dictionary:

```python
result = update_order_status(order_id, new_status, user_info)

if not result['success']:
    # Handle error
    if result['message'] == 'Order not found':
        # Order doesn't exist
        handle_missing_order(order_id)
    elif result['message'] == 'Invalid status provided':
        # Status value is invalid
        handle_invalid_status(new_status)
    else:
        # Unexpected error
        handle_unexpected_error(result['error'])
```

## Testing

Comprehensive test suite with 14 tests:

```bash
python manage.py test tests.test_update_order_status_utility
```

**Test Coverage**:
- ✅ Valid status transitions (all combinations)
- ✅ Error handling (missing orders, invalid statuses)
- ✅ Idempotent behavior (updating to same status)
- ✅ OrderStatus object creation
- ✅ Multiple order independence
- ✅ Response structure validation
- ✅ Case sensitivity
- ✅ Default parameters

**Results**: All 14 tests passing (100%)

## Logging Examples

The function provides detailed audit logging:

```
INFO: Order ORD-A7X9K2M5 status updated from Pending to Processing (initiated by: admin)
INFO: Order ORD-B8N4P2 already has status Completed (initiated by: system)
WARNING: Invalid status provided for order ORD-C9M5T3: InvalidStatus (initiated by: testuser)
WARNING: Order status update failed: No order found with ID: ORD-NONEXISTENT (initiated by: auto_process)
ERROR: Error updating order ORD-D2K8R4 status to Cancelled: Database connection error (initiated by: batch_script)
```

## Best Practices

### DO ✅
- Always check `result['success']` before proceeding
- Provide meaningful `user_info` for audit trails
- Use for batch processing and automation
- Handle errors gracefully
- Use in management commands and tasks

### DON'T ❌
- Don't assume success without checking `result['success']`
- Don't raise your own exceptions (function handles errors)
- Don't bypass validation by accessing database directly
- Don't use lowercase status values (case-sensitive)
- Don't forget to log the results of batch operations

## Troubleshooting

### Order Not Found
**Problem**: `result['success'] = False`, message = "Order not found"

**Solutions**:
- Verify order_id format and existence
- Check if order was deleted
- Ensure you're using order_id, not pk/id

### Invalid Status
**Problem**: `result['success'] = False`, message = "Invalid status provided"

**Solutions**:
- Use exact case: 'Pending', not 'pending'
- Check OrderStatusChoices for valid values
- Verify status name spelling

### Already Same Status
**Problem**: `result['success'] = True`, but no change

**Solutions**:
- This is normal behavior (idempotent)
- Check `previous_status` and `new_status` in result
- Update logic if you need to detect this case

## Related Documentation
- [Update Order Status API](ORDER_API_GUIDE.md#update-order-status) - REST API endpoint
- [Order Status Retrieval](ORDER_STATUS_RETRIEVAL_API.md) - Get current order status
- [OrderStatusChoices](../orders/choices.py) - Valid status values
- [Order Model](../orders/models.py) - Order data model

## Changelog
- **2025-10-14**: Initial implementation of reusable utility function
