# Order Status Retrieval API Documentation

## Overview
This API endpoint provides a lightweight way to retrieve the current status of an order using its unique order ID. Unlike the full order detail endpoint, this returns only the essential status information, making it ideal for status polling and order tracking features.

## Endpoint

### Get Order Status
```
GET /PerpexBistro/orders/<order_id>/status/
```

**Description**: Retrieve the current status of a specific order by its order ID.

**Authentication**: Not required (public access)

**URL Parameters**:
- `order_id` (string, required): The unique order identifier (e.g., "ORD-A7X9K2M5")

**Response (Success - 200 OK)**:
```json
{
    "order_id": "ORD-A7X9K2M5",
    "status": "Processing",
    "updated_at": "2025-10-14T21:45:30.123456Z"
}
```

**Response (Not Found - 404)**:
```json
{
    "error": "Order not found",
    "order_id": "ORD-INVALID123"
}
```

## Status Values

The `status` field can have one of the following values:
- `Pending` - Order has been placed and is waiting to be processed
- `Processing` - Order is being prepared
- `Completed` - Order has been completed and delivered
- `Cancelled` - Order has been cancelled

## Usage Examples

### Python/Requests
```python
import requests

order_id = "ORD-A7X9K2M5"
response = requests.get(f'http://localhost:8000/PerpexBistro/orders/{order_id}/status/')

if response.status_code == 200:
    data = response.json()
    print(f"Order {data['order_id']} is currently: {data['status']}")
    print(f"Last updated: {data['updated_at']}")
elif response.status_code == 404:
    print("Order not found")
```

### JavaScript/Fetch
```javascript
const orderId = 'ORD-A7X9K2M5';

fetch(`/PerpexBistro/orders/${orderId}/status/`)
    .then(response => {
        if (!response.ok) {
            throw new Error('Order not found');
        }
        return response.json();
    })
    .then(data => {
        console.log(`Order ${data.order_id} is currently: ${data.status}`);
        console.log(`Last updated: ${data.updated_at}`);
    })
    .catch(error => {
        console.error('Error:', error);
    });
```

### cURL
```bash
# Get order status
curl http://localhost:8000/PerpexBistro/orders/ORD-A7X9K2M5/status/

# Example response
# {
#     "order_id": "ORD-A7X9K2M5",
#     "status": "Processing",
#     "updated_at": "2025-10-14T21:45:30.123456Z"
# }
```

## Use Cases

### 1. Order Tracking Page
Display real-time order status to customers:
```javascript
function trackOrder(orderId) {
    // Poll every 30 seconds
    setInterval(async () => {
        const response = await fetch(`/PerpexBistro/orders/${orderId}/status/`);
        const data = await response.json();
        updateStatusDisplay(data.status);
    }, 30000);
}
```

### 2. Status Notification System
Check for status changes and notify users:
```python
def check_order_status_change(order_id, previous_status):
    response = requests.get(f'/PerpexBistro/orders/{order_id}/status/')
    if response.status_code == 200:
        data = response.json()
        if data['status'] != previous_status:
            send_notification(order_id, data['status'])
            return data['status']
    return previous_status
```

### 3. Admin Dashboard
Monitor multiple orders:
```javascript
async function monitorOrders(orderIds) {
    const statuses = await Promise.all(
        orderIds.map(id => 
            fetch(`/PerpexBistro/orders/${id}/status/`)
                .then(r => r.json())
        )
    );
    
    return statuses.filter(s => s.status === 'Pending');
}
```

## Comparison with Related Endpoints

### Order Status Retrieval vs Order Detail
| Feature | `/orders/<order_id>/status/` | `/orders/<order_id>/` |
|---------|----------------------------|---------------------|
| **Purpose** | Quick status check | Full order information |
| **Authentication** | Not required | Required |
| **Data Returned** | Status only | All order details, items, customer info |
| **Response Size** | Small (~100 bytes) | Large (~2-5 KB) |
| **Use Case** | Status polling, tracking | Order review, receipt |
| **Performance** | Very fast | Slower (more data) |

### Order Status Retrieval vs Order Status Update
| Feature | `/orders/<order_id>/status/` | `/orders/update-status/` |
|---------|----------------------------|----------------------|
| **HTTP Method** | GET | POST/PUT |
| **Purpose** | Retrieve status | Update status |
| **Authentication** | Not required | Required |
| **Side Effects** | None (read-only) | Modifies order status |

## Features

✅ **Lightweight**: Returns only essential status information  
✅ **Public Access**: No authentication required (suitable for tracking pages)  
✅ **Fast**: Optimized with `select_related()` for minimal database queries  
✅ **Real-time**: Reflects current order status immediately  
✅ **Error Handling**: Clear error messages for non-existent orders  
✅ **REST Compliant**: Follows REST best practices

## Performance Considerations

- **Database Optimization**: Uses `select_related('status')` to prevent N+1 queries
- **Minimal Data**: Returns only 3 fields, reducing bandwidth
- **No Authorization Overhead**: Public access eliminates auth processing time
- **Ideal for Polling**: Lightweight enough for frequent status checks

## Error Handling

### Order Not Found (404)
Occurs when the provided order_id doesn't exist in the database.

**Example**:
```json
{
    "error": "Order not found",
    "order_id": "ORD-INVALID123"
}
```

**Common Causes**:
- Typo in order ID
- Order has been permanently deleted
- Invalid order ID format

### Method Not Allowed (405)
Occurs when using HTTP methods other than GET.

**Allowed Methods**: GET only

**Example Error**:
```
POST /PerpexBistro/orders/ORD-123/status/ → 405 Method Not Allowed
```

## Implementation Details

### View Function
```python
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_order_status(request, order_id):
    """Retrieve order status by order ID."""
    try:
        order = Order.objects.select_related('status').get(order_id=order_id)
        return Response({
            'order_id': order.order_id,
            'status': order.status.name,
            'updated_at': order.updated_at
        }, status=status.HTTP_200_OK)
    except Order.DoesNotExist:
        return Response({
            'error': 'Order not found',
            'order_id': order_id
        }, status=status.HTTP_404_NOT_FOUND)
```

### URL Pattern
```python
path('orders/<str:order_id>/status/', get_order_status, name='order-status')
```

## Testing

Comprehensive test suite included with 10 test cases:

```bash
python manage.py test tests.test_order_status_retrieval
```

**Test Coverage**:
- ✅ Retrieve status for all order states (Pending, Processing, Completed, Cancelled)
- ✅ Handle non-existent orders (404)
- ✅ Public access verification (no auth required)
- ✅ Response structure validation
- ✅ Real-time status updates
- ✅ HTTP method restrictions (GET only)
- ✅ Multiple order independence

**All 10 tests pass** ✅

## Security Considerations

### Public Access Justification
This endpoint is publicly accessible because:
1. **Order IDs are unique and unpredictable** (e.g., "ORD-A7X9K2M5")
2. **Minimal sensitive information** (only status, not payment or personal details)
3. **Common use case** (customer tracking pages, email links)
4. **Industry standard** (most order tracking is public with order ID)

### What's Protected
- Order IDs are hard to guess (10-character alphanumeric)
- No personal information exposed (use full detail endpoint for that)
- Status is read-only (cannot be modified via this endpoint)

### Alternative Security Approach
If you need to restrict access, change permissions:
```python
@permission_classes([permissions.IsAuthenticated])
```

## Related Documentation
- [Order Detail API](ORDER_API_GUIDE.md) - Full order information retrieval
- [Order Status Update API](ORDER_API_GUIDE.md#update-order-status) - Modify order status
- [Order Cancellation API](ORDER_CANCELLATION_API.md) - Cancel orders

## Changelog
- **2025-10-14**: Initial implementation of order status retrieval endpoint
