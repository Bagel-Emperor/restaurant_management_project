# Order Management API Guide

## Overview
This guide provides comprehensive documentation for all order management API endpoints in the Restaurant Management Platform. These endpoints handle the complete order lifecycle from creation to completion or cancellation.

## Table of Contents
- [Authentication](#authentication)
- [Endpoints Overview](#endpoints-overview)
- [Order Creation](#1-create-order)
- [List Orders](#2-list-orders)
- [Order Details](#3-order-details)
- [Order History](#4-order-history)
- [Update Order Status](#5-update-order-status)
- [Cancel Order](#6-cancel-order)
- [Status Transition Rules](#status-transition-rules)
- [Testing Guide](#testing-guide)
- [Error Handling](#error-handling)

---

## Authentication

Most order endpoints support multiple authentication methods:
- **Session Authentication**: Cookie-based (for web browsers)
- **Token Authentication**: DRF Token in header
- **JWT Authentication**: Bearer token in header
- **AllowAny**: Some endpoints allow unauthenticated access (guest orders)

**JWT Authentication Example:**
```bash
Authorization: Bearer <your_jwt_token>
```

---

## Endpoints Overview

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/PerpexBistro/orders/orders/create/` | Create new order | Optional |
| `GET` | `/PerpexBistro/orders/orders/` | List customer orders | Optional |
| `GET` | `/PerpexBistro/orders/orders/<id>/` | Get order details | Optional |
| `GET` | `/PerpexBistro/orders/orders/history/` | User order history | Required |
| `POST` | `/PerpexBistro/orders/orders/update-status/` | Update order status | **Required** |
| `DELETE` | `/PerpexBistro/orders/orders/<id>/cancel/` | Cancel order | Optional |

---

## 1. Create Order

Create a new order with menu items.

### Endpoint
```
POST /PerpexBistro/orders/orders/create/
```

### Request Body
```json
{
  "customer": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "1234567890"
  },
  "order_items": [
    {
      "menu_item_id": 1,
      "quantity": 2
    },
    {
      "menu_item_id": 3,
      "quantity": 1
    }
  ]
}
```

### Success Response (201 Created)
```json
{
  "id": 15,
  "order_id": "ORD-A7X9K2M5",
  "customer": {
    "id": 8,
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "1234567890"
  },
  "status": {
    "id": 1,
    "name": "Pending"
  },
  "total_amount": "45.99",
  "created_at": "2025-10-09T10:30:00Z",
  "order_items": [
    {
      "id": 20,
      "menu_item": {
        "id": 1,
        "name": "Margherita Pizza",
        "price": "12.99"
      },
      "quantity": 2,
      "price": "12.99"
    }
  ]
}
```

### Error Response (400 Bad Request)
```json
{
  "customer": {
    "email": ["Enter a valid email address."]
  }
}
```

---

## 2. List Orders

Retrieve orders for a customer or authenticated user.

### Endpoint
```
GET /PerpexBistro/orders/orders/?customer_id=<id>
GET /PerpexBistro/orders/orders/  # For authenticated users
```

### Query Parameters
- `customer_id` (optional): Filter by customer ID (for guest orders)

### Success Response (200 OK)
```json
[
  {
    "id": 15,
    "order_id": "ORD-A7X9K2M5",
    "status": {
      "id": 1,
      "name": "Pending"
    },
    "total_amount": "45.99",
    "created_at": "2025-10-09T10:30:00Z"
  }
]
```

---

## 3. Order Details

Get detailed information about a specific order.

### Endpoint
```
GET /PerpexBistro/orders/orders/<order_id>/
```

### URL Parameters
- `order_id`: Can be either:
  - User-friendly Order ID (e.g., `ORD-A7X9K2M5`)
  - Database ID (e.g., `15`)

### Success Response (200 OK)
```json
{
  "id": 15,
  "order_id": "ORD-A7X9K2M5",
  "customer": {
    "id": 8,
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "1234567890"
  },
  "status": {
    "id": 2,
    "name": "Processing"
  },
  "total_amount": "45.99",
  "created_at": "2025-10-09T10:30:00Z",
  "order_items": [
    {
      "id": 20,
      "menu_item": {
        "id": 1,
        "name": "Margherita Pizza",
        "description": "Classic pizza with tomato and mozzarella",
        "price": "12.99",
        "category": {
          "id": 1,
          "name": "Pizza"
        }
      },
      "quantity": 2,
      "price": "12.99",
      "total_price": "25.98"
    }
  ]
}
```

### Error Response (404 Not Found)
```json
{
  "detail": "Order not found"
}
```

---

## 4. Order History

Get order history for the authenticated user.

### Endpoint
```
GET /PerpexBistro/orders/orders/history/
```

### Authentication
**Required** - User must be authenticated

### Success Response (200 OK)
```json
{
  "count": 2,
  "orders": [
    {
      "id": 15,
      "order_id": "ORD-A7X9K2M5",
      "created_at": "2025-10-09T10:30:00Z",
      "total_amount": "45.99",
      "status": {
        "id": 3,
        "name": "Completed"
      },
      "items_count": 2,
      "order_items": [
        {
          "id": 20,
          "menu_item": {
            "id": 1,
            "name": "Margherita Pizza",
            "price": "12.99"
          },
          "quantity": 2,
          "price": "12.99",
          "total_price": "25.98"
        }
      ]
    }
  ]
}
```

---

## 5. Update Order Status

Update the status of an existing order with validation for state transitions.

### Endpoint
```
POST /PerpexBistro/orders/orders/update-status/
```

### Authentication
**Required** - User must be authenticated with valid JWT token or session

### Request Body
```json
{
  "order_id": "ORD-A7X9K2M5",
  "status": "Processing"
}
```

### Request Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `order_id` | string | Yes | Unique alphanumeric order identifier |
| `status` | string | Yes | New status: `Pending`, `Processing`, `Completed`, or `Cancelled` |

### Success Response (200 OK)
```json
{
  "success": true,
  "message": "Order status updated successfully",
  "order": {
    "order_id": "ORD-A7X9K2M5",
    "status": "Processing",
    "previous_status": "Pending",
    "updated_at": "2025-10-09T10:35:00Z"
  }
}
```

### Error Responses

#### Unauthenticated Request (401 Unauthorized)
```json
{
  "detail": "Authentication credentials were not provided."
}
```

#### Invalid Order ID (404 Not Found)
```json
{
  "success": false,
  "errors": {
    "order_id": ["Order with ID 'ORD-XYZ123' does not exist."]
  }
}
```

#### Invalid Status Value (400 Bad Request)
```json
{
  "success": false,
  "errors": {
    "status": ["\"InvalidStatus\" is not a valid choice."]
  }
}
```

#### Invalid Status Transition (400 Bad Request)
```json
{
  "success": false,
  "errors": {
    "non_field_errors": [
      "Invalid status transition from 'Completed' to 'Pending'. Allowed transitions: "
    ]
  }
}
```

#### Order Already in Status (400 Bad Request)
```json
{
  "success": false,
  "errors": {
    "non_field_errors": ["Order is already in 'Processing' status."]
  }
}
```

#### Finalized Order (400 Bad Request)
```json
{
  "success": false,
  "errors": {
    "non_field_errors": [
      "Cannot change status from 'Completed'. This order is finalized."
    ]
  }
}
```

### Testing Examples

#### Using cURL
```bash
# Update order to Processing
curl -X POST http://localhost:8000/PerpexBistro/orders/orders/update-status/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -d '{
    "order_id": "ORD-A7X9K2M5",
    "status": "Processing"
  }'

# Complete an order
curl -X POST http://localhost:8000/PerpexBistro/orders/orders/update-status/ \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ORD-A7X9K2M5",
    "status": "Completed"
  }'
```

#### Using Python requests
```python
import requests

url = "http://localhost:8000/PerpexBistro/orders/orders/update-status/"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer <your_jwt_token>"
}
data = {
    "order_id": "ORD-A7X9K2M5",
    "status": "Processing"
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

#### Using JavaScript fetch
```javascript
fetch('http://localhost:8000/PerpexBistro/orders/orders/update-status/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer <your_jwt_token>'
  },
  body: JSON.stringify({
    order_id: 'ORD-A7X9K2M5',
    status: 'Processing'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

---

## 6. Cancel Order

Cancel an existing order by setting status to 'Cancelled'.

### Endpoint
```
DELETE /PerpexBistro/orders/orders/<order_id>/cancel/
```

### URL Parameters
- `order_id`: Can be either:
  - User-friendly Order ID (e.g., `ORD-A7X9K2M5`)
  - Database ID (e.g., `15`)

### Request Body (Optional)
```json
{
  "customer_id": "8"  // Required for guest orders
}
```

### Success Response (200 OK)
```json
{
  "success": true,
  "message": "Order cancelled successfully",
  "order_id": "ORD-A7X9K2M5",
  "previous_status": "Pending",
  "current_status": "Cancelled",
  "cancelled_at": "2025-10-09T10:40:00Z"
}
```

### Error Response (404 Not Found)
```json
{
  "success": false,
  "message": "Order not found"
}
```

### Error Response (403 Forbidden)
```json
{
  "success": false,
  "message": "You do not have permission to cancel this order"
}
```

---

## Status Transition Rules

The Order Status Update API enforces the following state machine rules:

### Valid Status Transitions

```
┌──────────┐
│ Pending  │──────────┐
└────┬─────┘          │
     │                │
     ▼                ▼
┌────────────┐   ┌───────────┐
│ Processing │──►│ Cancelled │ (Final State)
└────┬───────┘   └───────────┘
     │
     ▼
┌───────────┐
│ Completed │ (Final State)
└───────────┘
```

### Allowed Transitions

| Current Status | Allowed Next Status |
|----------------|---------------------|
| **Pending** | Processing, Cancelled |
| **Processing** | Completed, Cancelled |
| **Completed** | ❌ None (finalized) |
| **Cancelled** | ❌ None (finalized) |

### Validation Rules

1. **Order Must Exist**: Order ID must correspond to an existing order
2. **Valid Status Value**: Status must be one of: `Pending`, `Processing`, `Completed`, `Cancelled`
3. **Valid Transition**: Status change must follow the allowed transition rules
4. **No Duplicate Status**: Cannot set order to its current status
5. **Finalized Orders**: Cannot change status of `Completed` or `Cancelled` orders

### Business Logic

- **Pending → Processing**: Order accepted and being prepared
- **Pending → Cancelled**: Order cancelled before processing starts
- **Processing → Completed**: Order successfully fulfilled
- **Processing → Cancelled**: Order cancelled during preparation
- **Completed**: Final state - order delivered/picked up
- **Cancelled**: Final state - order was cancelled

---

## Testing Guide

### Manual Testing Steps

#### Test 1: Create and Update Order Flow
```bash
# 1. Create a new order
POST /PerpexBistro/orders/orders/create/
# Note the order_id from response (e.g., ORD-A7X9K2M5)

# 2. Update to Processing
POST /PerpexBistro/orders/orders/update-status/
{
  "order_id": "ORD-A7X9K2M5",
  "status": "Processing"
}
# Expected: Success with previous_status="Pending"

# 3. Complete the order
POST /PerpexBistro/orders/orders/update-status/
{
  "order_id": "ORD-A7X9K2M5",
  "status": "Completed"
}
# Expected: Success with previous_status="Processing"

# 4. Try to change completed order (should fail)
POST /PerpexBistro/orders/orders/update-status/
{
  "order_id": "ORD-A7X9K2M5",
  "status": "Pending"
}
# Expected: 400 Error - Cannot change from finalized state
```

#### Test 2: Invalid Transitions
```bash
# 1. Create order (starts as Pending)
POST /PerpexBistro/orders/orders/create/

# 2. Try to complete without processing (should fail)
POST /PerpexBistro/orders/orders/update-status/
{
  "order_id": "ORD-A7X9K2M5",
  "status": "Completed"
}
# Expected: 400 Error - Invalid transition from Pending to Completed
```

#### Test 3: Error Handling
```bash
# Test invalid order ID
POST /PerpexBistro/orders/orders/update-status/
{
  "order_id": "ORD-INVALID",
  "status": "Processing"
}
# Expected: 404 Error

# Test invalid status value
POST /PerpexBistro/orders/orders/update-status/
{
  "order_id": "ORD-A7X9K2M5",
  "status": "InvalidStatus"
}
# Expected: 400 Error

# Test missing fields
POST /PerpexBistro/orders/orders/update-status/
{
  "order_id": "ORD-A7X9K2M5"
}
# Expected: 400 Error - status field required
```

### Automated Testing

Example test case for Django tests:

```python
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from orders.models import Order, OrderStatus

class OrderStatusUpdateTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create test order
        self.order = Order.objects.create(...)
    
    def test_update_order_status_success(self):
        """Test successful order status update."""
        response = self.client.post(
            '/PerpexBistro/orders/orders/update-status/',
            {
                'order_id': self.order.order_id,
                'status': 'Processing'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['order']['status'], 'Processing')
    
    def test_invalid_transition(self):
        """Test invalid status transition is rejected."""
        # Set order to Completed
        completed_status = OrderStatus.objects.get(name='Completed')
        self.order.status = completed_status
        self.order.save()
        
        # Try to change to Pending (should fail)
        response = self.client.post(
            '/PerpexBistro/orders/orders/update-status/',
            {
                'order_id': self.order.order_id,
                'status': 'Pending'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
```

---

## Error Handling

### Standard Error Format

All endpoints return errors in a consistent format:

```json
{
  "success": false,
  "errors": {
    "field_name": ["Error message"]
  }
}
```

### Common Error Codes

| Status Code | Meaning | Common Causes |
|-------------|---------|---------------|
| 400 | Bad Request | Invalid data, validation errors, invalid transitions |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | User lacks permission for this action |
| 404 | Not Found | Order ID doesn't exist |
| 500 | Internal Server Error | Unexpected server error |

### Error Messages Reference

| Error Type | Message | Resolution |
|------------|---------|------------|
| Invalid Order | "Order with ID 'XXX' does not exist." | Verify order_id is correct |
| Invalid Status | "\"XXX\" is not a valid choice." | Use: Pending, Processing, Completed, or Cancelled |
| Invalid Transition | "Invalid status transition from 'X' to 'Y'..." | Follow allowed transition rules |
| Already in Status | "Order is already in 'X' status." | Check current order status first |
| Finalized Order | "Cannot change status from 'X'. This order is finalized." | Completed/Cancelled orders can't be changed |
| Missing Fields | "This field is required." | Include all required fields in request |

---

## Best Practices

### 1. Status Update Flow
```python
# Always check current status before updating
GET /PerpexBistro/orders/orders/<order_id>/

# Update status following transition rules
POST /PerpexBistro/orders/orders/update-status/

# Verify the update
GET /PerpexBistro/orders/orders/<order_id>/
```

### 2. Error Handling
```javascript
try {
  const response = await fetch('/api/orders/update-status/', {
    method: 'POST',
    body: JSON.stringify(data)
  });
  
  const result = await response.json();
  
  if (!result.success) {
    // Handle validation errors
    console.error('Validation errors:', result.errors);
  }
} catch (error) {
  // Handle network errors
  console.error('Network error:', error);
}
```

### 3. Logging & Monitoring
- All status updates are logged with timestamps
- Monitor for unusual status transition patterns
- Track completion rates and cancellation reasons
- Alert on high error rates

### 4. Security Considerations
- Consider restricting status updates to admin users only
- Implement rate limiting to prevent abuse
- Validate user permissions before status changes
- Audit trail for all status changes

---

## Related Documentation

- **[Order Cancellation API](ORDER_CANCELLATION_API.md)** - Detailed cancellation endpoint documentation
- **[Order Manager Guide](ORDER_MANAGER_GUIDE.md)** - Custom order manager implementation
- **[JWT Authentication](JWT_AUTHENTICATION.md)** - Authentication setup and usage
- **[Main README](README.md)** - Platform overview and setup

---

## Support

For issues or questions about the Order Management API:
1. Check this documentation first
2. Review related documentation files
3. Check Django system logs for detailed error information
4. Verify database migrations are up to date

---

**Last Updated**: October 9, 2025  
**API Version**: 1.0  
**Django Version**: 5.2.5  
**DRF Version**: 3.16.1
