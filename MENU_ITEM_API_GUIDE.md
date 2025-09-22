# Menu Item API Documentation

## Overview
The Menu Item API provides full CRUD (Create, Read, Update, Delete) operations for managing restaurant menu items. It includes proper authentication, validation, and error handling.

## Base URL
```
/PerpexBistro/api/menu-items/
```

## Authentication
- **Read operations** (GET): Public access
- **Write operations** (POST, PUT, PATCH, DELETE): Admin/Staff authentication required

## Endpoints

### 1. List Menu Items
**GET** `/api/menu-items/`

Returns a list of all menu items.

**Query Parameters:**
- `restaurant` (optional): Filter by restaurant ID
- `available` (optional): Filter by availability (`true`/`false`)

**Example:**
```bash
GET /PerpexBistro/api/menu-items/?restaurant=1&available=true
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Margherita Pizza",
    "description": "Classic pizza with tomato and mozzarella",
    "price": "12.99",
    "restaurant": 1,
    "is_available": true,
    "image": null,
    "created_at": "2025-09-21T15:30:00Z"
  }
]
```

### 2. Create Menu Item
**POST** `/api/menu-items/`

Creates a new menu item. Requires admin authentication.

**Request Body:**
```json
{
  "name": "New Pizza",
  "description": "Delicious new pizza",
  "price": 15.99,
  "restaurant": 1,
  "is_available": true
}
```

**Validation Rules:**
- `price`: Must be positive number
- `name`: Cannot be empty, max 100 characters
- `restaurant`: Must be valid restaurant ID

**Response (201 Created):**
```json
{
  "id": 2,
  "name": "New Pizza",
  "description": "Delicious new pizza",
  "price": "15.99",
  "restaurant": 1,
  "is_available": true,
  "image": null,
  "created_at": "2025-09-21T15:35:00Z"
}
```

### 3. Retrieve Menu Item
**GET** `/api/menu-items/{id}/`

Returns a specific menu item by ID.

**Response:**
```json
{
  "id": 1,
  "name": "Margherita Pizza",
  "description": "Classic pizza with tomato and mozzarella",
  "price": "12.99",
  "restaurant": 1,
  "is_available": true,
  "image": null,
  "created_at": "2025-09-21T15:30:00Z"
}
```

### 4. Update Menu Item
**PUT** `/api/menu-items/{id}/`

Updates a complete menu item. Requires admin authentication.

**Request Body:**
```json
{
  "name": "Updated Pizza",
  "description": "Updated description",
  "price": 18.99,
  "restaurant": 1,
  "is_available": true
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Updated Pizza",
  "description": "Updated description",
  "price": "18.99",
  "restaurant": 1,
  "is_available": true,
  "image": null,
  "created_at": "2025-09-21T15:30:00Z"
}
```

### 5. Partial Update Menu Item
**PATCH** `/api/menu-items/{id}/`

Partially updates a menu item. Requires admin authentication.

**Request Body (only fields to update):**
```json
{
  "price": 16.99,
  "is_available": false
}
```

### 6. Delete Menu Item
**DELETE** `/api/menu-items/{id}/`

Deletes a menu item. Requires admin authentication.

**Response:** 204 No Content

### 7. Toggle Availability (Custom Action)
**PATCH** `/api/menu-items/{id}/toggle_availability/`

Toggles the availability status of a menu item. Requires admin authentication.

**Response:**
```json
{
  "message": "Menu item is now unavailable",
  "menu_item": {
    "id": 1,
    "name": "Margherita Pizza",
    "description": "Classic pizza with tomato and mozzarella",
    "price": "12.99",
    "restaurant": 1,
    "is_available": false,
    "image": null,
    "created_at": "2025-09-21T15:30:00Z"
  }
}
```

## Error Responses

### 400 Bad Request
Validation errors:
```json
{
  "price": ["Price must be a positive number."],
  "name": ["Name cannot be empty."]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
  "error": "Unable to process request"
}
```

## Features

### ✅ Implemented Requirements
1. **Menu Item Model and Serializer** - Complete with validation
2. **ViewSet with PUT method** - Full CRUD using ModelViewSet
3. **Validation** - Price positivity, name requirements
4. **Error Handling** - Comprehensive HTTP status codes and logging
5. **URL Routing** - RESTful endpoints with router configuration

### ✅ Additional Features
- **Authentication & Authorization** - Admin-only write access
- **Filtering** - By restaurant and availability
- **Custom Actions** - Toggle availability endpoint
- **Transaction Safety** - Database transactions for consistency
- **Logging** - Comprehensive audit trail
- **Backward Compatibility** - Legacy endpoints preserved

## Example Usage

### Create a menu item (requires admin login):
```python
import requests

# Login first
login_response = requests.post('http://localhost:8000/admin/', {
    'username': 'admin',
    'password': 'password'
})

# Create menu item
response = requests.post('http://localhost:8000/PerpexBistro/api/menu-items/', 
    json={
        'name': 'Caesar Salad',
        'description': 'Fresh romaine with parmesan and croutons',
        'price': 9.99,
        'restaurant': 1,
        'is_available': True
    },
    cookies=login_response.cookies
)
print(response.json())
```

### Update a menu item:
```python
response = requests.put('http://localhost:8000/PerpexBistro/api/menu-items/1/', 
    json={
        'name': 'Premium Caesar Salad',
        'description': 'Fresh romaine with premium parmesan and homemade croutons',
        'price': 12.99,
        'restaurant': 1,
        'is_available': True
    },
    cookies=login_response.cookies
)
```

## Security Notes
- All write operations require authentication and admin privileges
- Input validation prevents malicious data
- Transaction safety ensures data consistency
- Comprehensive logging for audit trails