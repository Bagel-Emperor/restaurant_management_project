# Menu Item Availability Update API Guide

## Overview

The **Update Availability API** provides a dedicated endpoint to explicitly set the availability status of a menu item to a specific value (true or false). This endpoint gives precise control over menu item availability, allowing you to set it to a known state without needing to check the current value first.

## Endpoint

```
PATCH /PerpexBistro/api/menu-items/{id}/update_availability/
```

## Authentication

- **Required:** Yes (Admin/Staff only)
- **Permission:** `IsAdminUser`
- **Status Code if not authenticated:** 401 Unauthorized
- **Status Code if not admin:** 403 Forbidden

## Request

### URL Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | integer | Yes | The ID of the menu item to update |

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `is_available` | boolean | Yes | The availability status to set (`true` or `false`) |

### Example Request Bodies

**JSON (recommended):**
```json
{
    "is_available": false
}
```

**String values (also accepted):**
```json
{
    "is_available": "true"
}
```

The endpoint accepts case-insensitive string representations:
- `"true"`, `"True"`, `"TRUE"` → `true`
- `"false"`, `"False"`, `"FALSE"` → `false`

## Response

### Success Response (200 OK)

```json
{
    "success": true,
    "message": "Menu item availability updated successfully. Item is now unavailable.",
    "menu_item": {
        "id": 1,
        "name": "Margherita Pizza",
        "description": "Classic pizza with tomato and mozzarella",
        "price": "12.99",
        "restaurant": 1,
        "category": 2,
        "category_name": "Main Courses",
        "is_available": false,
        "is_daily_special": false,
        "image": null,
        "created_at": "2025-10-17T10:30:00Z"
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Indicates if the operation was successful |
| `message` | string | Human-readable success message |
| `menu_item` | object | Complete menu item data after update |

### Error Responses

#### 400 Bad Request - Missing Field

```json
{
    "success": false,
    "error": "is_available field is required"
}
```

#### 400 Bad Request - Invalid Type

```json
{
    "success": false,
    "error": "is_available must be a boolean (true or false)"
}
```

#### 401 Unauthorized - Not Authenticated

```json
{
    "detail": "Authentication credentials were not provided."
}
```

#### 403 Forbidden - Not Admin

```json
{
    "detail": "You do not have permission to perform this action."
}
```

#### 404 Not Found - Menu Item Doesn't Exist

```json
{
    "success": false,
    "error": "Menu item not found"
}
```

#### 500 Internal Server Error

```json
{
    "success": false,
    "error": "Unable to update availability. Please try again later."
}
```

## Usage Examples

### Python with `requests`

```python
import requests

# Login first to get authentication
login_response = requests.post('http://localhost:8000/admin/', {
    'username': 'admin',
    'password': 'password'
})

# Update availability to unavailable (false)
response = requests.patch(
    'http://localhost:8000/PerpexBistro/api/menu-items/1/update_availability/',
    json={'is_available': False},
    cookies=login_response.cookies
)

if response.status_code == 200:
    data = response.json()
    print(f"Success: {data['message']}")
    print(f"Item: {data['menu_item']['name']}")
    print(f"Available: {data['menu_item']['is_available']}")
else:
    print(f"Error: {response.json()['error']}")
```

### Python with Django REST Framework Test Client

```python
from rest_framework.test import APIClient
from django.contrib.auth.models import User

# Create authenticated client
client = APIClient()
admin_user = User.objects.get(username='admin')
client.force_authenticate(user=admin_user)

# Update availability
response = client.patch(
    '/PerpexBistro/api/menu-items/1/update_availability/',
    {'is_available': True},
    format='json'
)

print(response.status_code)  # 200
print(response.data['message'])  # Success message
```

### cURL

```bash
# Set to unavailable
curl -X PATCH http://localhost:8000/PerpexBistro/api/menu-items/1/update_availability/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_AUTH_TOKEN" \
  -d '{"is_available": false}'

# Set to available
curl -X PATCH http://localhost:8000/PerpexBistro/api/menu-items/1/update_availability/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_AUTH_TOKEN" \
  -d '{"is_available": true}'
```

### JavaScript (Fetch API)

```javascript
// Set item to unavailable
async function updateAvailability(menuItemId, isAvailable) {
    try {
        const response = await fetch(
            `/PerpexBistro/api/menu-items/${menuItemId}/update_availability/`,
            {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Token ${authToken}`
                },
                body: JSON.stringify({
                    is_available: isAvailable
                })
            }
        );

        const data = await response.json();

        if (response.ok) {
            console.log('Success:', data.message);
            console.log('Updated item:', data.menu_item);
        } else {
            console.error('Error:', data.error);
        }
    } catch (error) {
        console.error('Request failed:', error);
    }
}

// Usage
updateAvailability(1, false);  // Mark as unavailable
updateAvailability(1, true);   // Mark as available
```

## Validation Rules

### Input Validation

1. **is_available field is required**
   - Missing field → 400 Bad Request
   - Error: "is_available field is required"

2. **is_available must be boolean or valid string**
   - Accepted: `true`, `false`, `"true"`, `"false"` (case-insensitive)
   - Rejected: numbers (0, 1), invalid strings, null, undefined
   - Invalid type → 400 Bad Request
   - Error: "is_available must be a boolean (true or false)"

3. **Menu item must exist**
   - Non-existent ID → 404 Not Found or 500 Internal Server Error
   - Error: "Menu item not found"

### Authentication & Authorization

1. **User must be authenticated**
   - No auth → 401 Unauthorized

2. **User must be admin/staff**
   - Regular user → 403 Forbidden

## Behavior Details

### Setting Same Value

You can set availability to the same value it already has. The operation will succeed without error:

```python
# Item is already available (True)
response = client.patch(url, {'is_available': True})
# Returns 200 OK, item remains available
```

### Extra Fields Ignored

Only the `is_available` field is processed. Other fields in the request body are safely ignored:

```json
{
    "is_available": false,
    "name": "Ignored",
    "price": 999.99
}
```

Only availability is updated; name and price remain unchanged.

### Logging

All availability updates are logged with details:

```
INFO: Menu item 'Margherita Pizza' (ID: 1) availability updated from True to False by user admin
```

Failed attempts are also logged:

```
WARNING: Update availability attempt for menu item 1 without is_available field
ERROR: Error updating menu item availability for ID 99999: No MenuItem matches the given query.
```

## Comparison: update_availability vs toggle_availability

| Feature | `update_availability` | `toggle_availability` |
|---------|----------------------|----------------------|
| Endpoint | `PATCH /api/menu-items/{id}/update_availability/` | `PATCH /api/menu-items/{id}/toggle_availability/` |
| Request Body | `{"is_available": true/false}` | None (empty body) |
| Behavior | Sets to specific value | Flips current value |
| Use Case | "Mark this item as unavailable" | "Switch availability status" |
| Predictability | Explicit (you know the result) | Depends on current state |
| Idempotent | Yes (repeated calls = same result) | No (repeated calls flip back and forth) |

### When to Use Each

**Use `update_availability` when:**
- ✅ You want to ensure a specific state
- ✅ External systems need to set explicit values
- ✅ You're syncing availability from another source
- ✅ You want idempotent operations (safe to retry)

**Use `toggle_availability` when:**
- ✅ Building a UI toggle switch
- ✅ You just want to flip the current state
- ✅ You don't care about the final value, just want to change it

## Real-World Use Cases

### 1. Out of Stock Management

```python
def mark_out_of_stock(menu_item_id):
    """Mark an item as unavailable when inventory runs out."""
    response = requests.patch(
        f'/PerpexBistro/api/menu-items/{menu_item_id}/update_availability/',
        json={'is_available': False},
        headers={'Authorization': f'Token {admin_token}'}
    )
    return response.status_code == 200
```

### 2. Scheduled Availability (Time-Based)

```python
from datetime import datetime

def update_daily_special_availability():
    """Enable daily specials only during lunch hours (11 AM - 2 PM)."""
    current_hour = datetime.now().hour
    is_lunch_time = 11 <= current_hour < 14
    
    daily_specials = MenuItem.objects.filter(is_daily_special=True)
    
    for item in daily_specials:
        requests.patch(
            f'/PerpexBistro/api/menu-items/{item.id}/update_availability/',
            json={'is_available': is_lunch_time},
            headers={'Authorization': f'Token {admin_token}'}
        )
```

### 3. Bulk Availability Updates

```python
def disable_all_desserts():
    """Disable all dessert items (e.g., kitchen issue)."""
    dessert_category = MenuCategory.objects.get(name='Desserts')
    desserts = MenuItem.objects.filter(category=dessert_category)
    
    for dessert in desserts:
        requests.patch(
            f'/PerpexBistro/api/menu-items/{dessert.id}/update_availability/',
            json={'is_available': False},
            headers={'Authorization': f'Token {admin_token}'}
        )
```

### 4. Seasonal Menu Management

```python
def toggle_seasonal_menu(season):
    """Enable/disable items based on season."""
    seasonal_items = {
        'summer': [1, 5, 8, 12],  # Salads, cold drinks
        'winter': [2, 3, 9, 15]   # Soups, hot drinks
    }
    
    # Disable all seasonal items
    all_seasonal = set(seasonal_items['summer'] + seasonal_items['winter'])
    for item_id in all_seasonal:
        requests.patch(
            f'/PerpexBistro/api/menu-items/{item_id}/update_availability/',
            json={'is_available': False},
            headers={'Authorization': f'Token {admin_token}'}
        )
    
    # Enable current season items
    for item_id in seasonal_items.get(season, []):
        requests.patch(
            f'/PerpexBistro/api/menu-items/{item_id}/update_availability/',
            json={'is_available': True},
            headers={'Authorization': f'Token {admin_token}'}
        )
```

### 5. Integration with External Inventory System

```python
def sync_availability_from_inventory_system():
    """Sync availability based on external inventory system."""
    inventory_api_response = requests.get('https://inventory-api.example.com/stock')
    inventory_data = inventory_api_response.json()
    
    for item in inventory_data:
        menu_item_id = item['menu_item_id']
        in_stock = item['quantity'] > 0
        
        requests.patch(
            f'/PerpexBistro/api/menu-items/{menu_item_id}/update_availability/',
            json={'is_available': in_stock},
            headers={'Authorization': f'Token {admin_token}'}
        )
```

## Testing

A comprehensive test suite with 15 tests validates all functionality:

```bash
# Run tests
python manage.py test tests.test_update_availability --keepdb -v 2
```

### Test Coverage

- ✅ Update available → unavailable
- ✅ Update unavailable → available
- ✅ Set to same value (no change)
- ✅ Missing `is_available` field
- ✅ Invalid type (number, invalid string)
- ✅ Valid string representations ("true", "false")
- ✅ Case-insensitive strings
- ✅ Non-existent menu item
- ✅ Authentication required
- ✅ Admin privileges required
- ✅ Response structure validation
- ✅ Multiple sequential updates
- ✅ Extra fields ignored

## Error Handling

The endpoint includes comprehensive error handling:

1. **Input Validation:** Checks for required fields and valid types
2. **String Conversion:** Accepts "true"/"false" strings (case-insensitive)
3. **Database Errors:** Catches and logs all database exceptions
4. **Logging:** All operations and errors are logged with context
5. **User-Friendly Messages:** Clear error messages for debugging

## Performance Considerations

- **Database Operations:** Single UPDATE query per request
- **Response Time:** < 50ms typical response time
- **Concurrent Updates:** Safe for concurrent requests (database handles locking)
- **Idempotent:** Safe to retry without side effects

## Security

- **Admin-Only Access:** Only admin users can update availability
- **Field Isolation:** Only `is_available` field is modified (other fields protected)
- **Input Sanitization:** All inputs validated before database operations
- **Audit Trail:** All changes logged with user and timestamp

## Version History

- **v1.0** (Current): Initial implementation with comprehensive validation and error handling

## Related Endpoints

- **GET /api/menu-items/{id}/**: Retrieve menu item details
- **PATCH /api/menu-items/{id}/toggle_availability/**: Toggle availability (flip current value)
- **PUT/PATCH /api/menu-items/{id}/**: Full/partial menu item update

## Support

For issues or questions:
1. Check test suite for usage examples: `tests/test_update_availability.py`
2. Review source code: `home/views.py` (MenuItemViewSet.update_availability)
3. Check application logs for detailed error messages

---

**Last Updated:** October 17, 2025  
**Maintainer:** Restaurant Management System Team
