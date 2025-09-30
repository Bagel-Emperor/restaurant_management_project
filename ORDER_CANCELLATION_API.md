# Order Cancellation API Documentation

## Overview
The Order Cancellation API allows users to cancel their orders by updating the order status to 'Cancelled'. This endpoint provides secure order cancellation with proper authorization and validation.

## Endpoint Details

### Cancel Order
- **URL**: `/PerpexBistro/orders/orders/{order_id}/cancel/`
- **Method**: `DELETE`
- **Content-Type**: `application/json`

#### URL Parameters
- `order_id` (string): The order identifier - can be either:
  - User-friendly Order ID (e.g., `ORD-ABC123`)
  - Database ID (e.g., `15`)

#### Request Body (Optional)
```json
{
  "customer_id": "123"  // Required for guest orders
}
```

#### Authentication
- **Optional**: Endpoint accepts both authenticated and unauthenticated requests
- **Authorization**: Users can only cancel their own orders
- **Guest Orders**: Require `customer_id` parameter for validation

## Response Formats

### Success Response (200 OK)
```json
{
  "success": true,
  "message": "Order cancelled successfully",
  "order_id": "ORD-ABC123",
  "previous_status": "Pending",
  "current_status": "Cancelled",
  "cancelled_at": "2025-09-30T03:50:52.801120+00:00"
}
```

### Error Responses

#### Order Not Found (404 Not Found)
```json
{
  "success": false,
  "message": "Order not found",
  "order_id": "FAKE-ORDER-ID"
}
```

#### Unauthorized (403 Forbidden)
```json
{
  "success": false,
  "message": "You are not authorized to cancel this order",
  "error": "Permission denied"
}
```

#### Already Cancelled/Completed (400 Bad Request)
```json
{
  "success": false,
  "message": "Cannot cancel order that is already cancelled",
  "current_status": "Cancelled",
  "order_id": "ORD-ABC123"
}
```

#### Server Error (500 Internal Server Error)
```json
{
  "success": false,
  "message": "An unexpected error occurred while cancelling the order",
  "error": "Error details"
}
```

## Usage Examples

### 1. Cancel Order with Order ID (Authenticated User)
```bash
curl -X DELETE \
  "http://localhost:8000/PerpexBistro/orders/orders/ORD-ABC123/cancel/" \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json"
```

### 2. Cancel Order with Database ID (Guest)
```bash
curl -X DELETE \
  "http://localhost:8000/PerpexBistro/orders/orders/15/cancel/" \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "123"}'
```

### 3. Using JavaScript/Fetch
```javascript
// For authenticated users
fetch('/PerpexBistro/orders/orders/ORD-ABC123/cancel/', {
  method: 'DELETE',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + userToken
  }
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log('Order cancelled:', data.order_id);
  } else {
    console.error('Cancellation failed:', data.message);
  }
});

// For guest orders
fetch('/PerpexBistro/orders/orders/15/cancel/', {
  method: 'DELETE',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    customer_id: '123'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

## Business Rules

### Cancellation Eligibility
- ✅ **Pending Orders**: Can be cancelled
- ✅ **Processing Orders**: Can be cancelled  
- ❌ **Completed Orders**: Cannot be cancelled
- ❌ **Already Cancelled Orders**: Cannot be cancelled again

### Authorization Rules
1. **Authenticated Users**: Can cancel orders they placed (`order.user == request.user`)
2. **Guest Orders**: Require correct `customer_id` parameter
3. **Fallback**: Orders without user/customer tracking allow cancellation (legacy support)

### Status Updates
- Order status changes from current status to `'Cancelled'`
- Previous status is preserved in response for audit trail
- Database is updated immediately upon successful cancellation

## Error Handling
The API implements comprehensive error handling for all scenarios:

- **Invalid Order IDs**: Returns 404 Not Found
- **Authorization Failures**: Returns 403 Forbidden  
- **Business Rule Violations**: Returns 400 Bad Request
- **Server Errors**: Returns 500 Internal Server Error
- **All responses include descriptive error messages**

## Testing
The API has been thoroughly tested with the following scenarios:
1. ✅ Successfully cancel a pending order
2. ✅ Prevent double-cancellation of already cancelled orders
3. ✅ Return 404 for non-existent orders
4. ✅ Support cancellation by both order_id and database ID

## Integration Notes
- Compatible with existing Order and OrderStatus models
- Uses Django REST Framework's Response and status codes
- Integrates with existing authentication system
- Maintains audit trail with timestamp information
- Thread-safe database operations