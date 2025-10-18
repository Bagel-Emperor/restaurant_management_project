# Restaurant Information API Guide

## Overview

The **Restaurant Information API** provides a comprehensive endpoint to retrieve all relevant information about the restaurant, including name, address, phone number, opening hours, and other important details. This endpoint is designed for frontend applications, mobile apps, or any client that needs to display complete restaurant information.

## Endpoint

```
GET /PerpexBistro/api/restaurant-info/
```

## Authentication

- **Required:** No (Public endpoint)
- **Anyone can access this endpoint without authentication**

## Request

No parameters required. Simply send a GET request to the endpoint.

### Example Request

```bash
GET /PerpexBistro/api/restaurant-info/
```

## Response

### Success Response (200 OK)

```json
{
    "success": true,
    "restaurant": {
        "id": 1,
        "name": "Perpex Bistro",
        "owner_name": "John Doe",
        "email": "contact@perpexbistro.com",
        "phone_number": "555-0100",
        "opening_hours": {
            "Monday": "9:00 AM - 10:00 PM",
            "Tuesday": "9:00 AM - 10:00 PM",
            "Wednesday": "9:00 AM - 10:00 PM",
            "Thursday": "9:00 AM - 10:00 PM",
            "Friday": "9:00 AM - 11:00 PM",
            "Saturday": "10:00 AM - 11:00 PM",
            "Sunday": "10:00 AM - 9:00 PM"
        },
        "address": "123 Main Street",
        "city": "New York",
        "state": "NY",
        "zip_code": "10001",
        "full_address": "123 Main Street, New York, NY 10001",
        "created_at": "2025-01-01T00:00:00Z"
    }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Indicates if the request was successful |
| `restaurant` | object | Restaurant information object |
| `restaurant.id` | integer | Unique identifier for the restaurant |
| `restaurant.name` | string | Restaurant name |
| `restaurant.owner_name` | string | Name of the restaurant owner |
| `restaurant.email` | string | Contact email address |
| `restaurant.phone_number` | string | Contact phone number |
| `restaurant.opening_hours` | object | JSON object with opening hours for each day |
| `restaurant.address` | string | Street address (null if no location) |
| `restaurant.city` | string | City (null if no location) |
| `restaurant.state` | string | State abbreviation (null if no location) |
| `restaurant.zip_code` | string | ZIP/Postal code (null if no location) |
| `restaurant.full_address` | string | Formatted complete address (null if no location) |
| `restaurant.created_at` | string (ISO 8601) | Restaurant creation timestamp |

### Error Responses

#### 404 Not Found - No Restaurant Exists

```json
{
    "success": false,
    "error": "Restaurant information not found. Please contact support."
}
```

**When:** No restaurant exists in the database.

#### 500 Internal Server Error

```json
{
    "success": false,
    "error": "Unable to retrieve restaurant information. Please try again later."
}
```

**When:** Server error during database query or serialization.

## Usage Examples

### Python with `requests`

```python
import requests

# Get restaurant information
response = requests.get('http://localhost:8000/PerpexBistro/api/restaurant-info/')

if response.status_code == 200:
    data = response.json()
    if data['success']:
        restaurant = data['restaurant']
        
        print(f"Restaurant: {restaurant['name']}")
        print(f"Phone: {restaurant['phone_number']}")
        print(f"Email: {restaurant['email']}")
        print(f"Address: {restaurant['full_address']}")
        print("\nOpening Hours:")
        for day, hours in restaurant['opening_hours'].items():
            print(f"  {day}: {hours}")
    else:
        print(f"Error: {data['error']}")
else:
    print(f"HTTP Error: {response.status_code}")
```

### Python with Django REST Framework Test Client

```python
from rest_framework.test import APIClient

client = APIClient()
response = client.get('/PerpexBistro/api/restaurant-info/')

print(response.status_code)  # 200
print(response.data['restaurant']['name'])  # "Perpex Bistro"
```

### JavaScript (Fetch API)

```javascript
async function getRestaurantInfo() {
    try {
        const response = await fetch('/PerpexBistro/api/restaurant-info/');
        const data = await response.json();
        
        if (data.success) {
            const restaurant = data.restaurant;
            
            console.log('Restaurant:', restaurant.name);
            console.log('Phone:', restaurant.phone_number);
            console.log('Address:', restaurant.full_address);
            
            // Display opening hours
            Object.entries(restaurant.opening_hours).forEach(([day, hours]) => {
                console.log(`${day}: ${hours}`);
            });
        } else {
            console.error('Error:', data.error);
        }
    } catch (error) {
        console.error('Request failed:', error);
    }
}

getRestaurantInfo();
```

### JavaScript (Axios)

```javascript
import axios from 'axios';

axios.get('/PerpexBistro/api/restaurant-info/')
    .then(response => {
        if (response.data.success) {
            const restaurant = response.data.restaurant;
            console.log('Restaurant Info:', restaurant);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
```

### cURL

```bash
curl -X GET http://localhost:8000/PerpexBistro/api/restaurant-info/
```

### jQuery

```javascript
$.ajax({
    url: '/PerpexBistro/api/restaurant-info/',
    type: 'GET',
    success: function(data) {
        if (data.success) {
            var restaurant = data.restaurant;
            $('#restaurant-name').text(restaurant.name);
            $('#restaurant-phone').text(restaurant.phone_number);
            $('#restaurant-address').text(restaurant.full_address);
        }
    },
    error: function(xhr) {
        console.error('Error:', xhr.status);
    }
});
```

## Real-World Use Cases

### 1. Contact Page Display

```python
def display_contact_info():
    """Display restaurant contact information on contact page."""
    response = requests.get('/PerpexBistro/api/restaurant-info/')
    data = response.json()
    
    if data['success']:
        restaurant = data['restaurant']
        return {
            'name': restaurant['name'],
            'phone': restaurant['phone_number'],
            'email': restaurant['email'],
            'address': restaurant['full_address']
        }
```

### 2. Mobile App Integration

```javascript
// React Native component
import React, { useState, useEffect } from 'react';
import { View, Text } from 'react-native';

function RestaurantInfoScreen() {
    const [restaurant, setRestaurant] = useState(null);
    
    useEffect(() => {
        fetch('https://api.perpexbistro.com/api/restaurant-info/')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    setRestaurant(data.restaurant);
                }
            });
    }, []);
    
    if (!restaurant) return <Text>Loading...</Text>;
    
    return (
        <View>
            <Text style={{fontSize: 24}}>{restaurant.name}</Text>
            <Text>{restaurant.phone_number}</Text>
            <Text>{restaurant.full_address}</Text>
        </View>
    );
}
```

### 3. Google Maps Integration

```javascript
async function showRestaurantOnMap() {
    const response = await fetch('/PerpexBistro/api/restaurant-info/');
    const data = await response.json();
    
    if (data.success) {
        const restaurant = data.restaurant;
        const address = restaurant.full_address;
        
        // Initialize Google Maps with restaurant location
        const map = new google.maps.Map(document.getElementById('map'), {
            center: { lat: 40.7128, lng: -74.0060 }, // Would geocode address
            zoom: 15
        });
        
        new google.maps.Marker({
            position: { lat: 40.7128, lng: -74.0060 },
            map: map,
            title: restaurant.name
        });
    }
}
```

### 4. Opening Hours Display Widget

```javascript
function displayOpeningHours() {
    fetch('/PerpexBistro/api/restaurant-info/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const hours = data.restaurant.opening_hours;
                const today = new Date().toLocaleDateString('en-US', { weekday: 'long' });
                
                // Highlight today's hours
                Object.entries(hours).forEach(([day, time]) => {
                    const element = document.getElementById(`hours-${day}`);
                    element.textContent = `${day}: ${time}`;
                    if (day === today) {
                        element.style.fontWeight = 'bold';
                        element.style.color = 'green';
                    }
                });
            }
        });
}
```

### 5. Email Signature Generator

```python
def generate_email_signature():
    """Generate email signature with restaurant info."""
    response = requests.get('/PerpexBistro/api/restaurant-info/')
    data = response.json()
    
    if data['success']:
        restaurant = data['restaurant']
        signature = f"""
        --
        {restaurant['name']}
        {restaurant['full_address']}
        Phone: {restaurant['phone_number']}
        Email: {restaurant['email']}
        """
        return signature
```

### 6. Social Media Bio Update

```python
def get_restaurant_bio():
    """Generate bio text for social media profiles."""
    response = requests.get('/PerpexBistro/api/restaurant-info/')
    data = response.json()
    
    if data['success']:
        restaurant = data['restaurant']
        bio = f"{restaurant['name']} | {restaurant['city']}, {restaurant['state']} | "
        bio += f"Call us: {restaurant['phone_number']}"
        return bio
```

## Features

### ✅ Public Access
- No authentication required
- Perfect for embedding in public-facing pages
- CORS-friendly for external integrations

### ✅ Comprehensive Data
- All restaurant details in one request
- Includes location information
- Formatted opening hours (JSON)
- Ready-to-display full address

### ✅ Flexible Location Handling
- Returns `null` for location fields if no location exists
- Non-breaking if RestaurantLocation model hasn't been set up yet
- Graceful degradation

### ✅ Consistent Format
- Predictable JSON structure
- Boolean success flag
- Clear error messages

## Data Model

The endpoint retrieves data from two related models:

### Restaurant Model
- `name`: CharField (100 chars)
- `owner_name`: CharField (100 chars)
- `email`: EmailField (unique)
- `phone_number`: CharField (20 chars)
- `opening_hours`: JSONField (stores dict)
- `created_at`: DateTimeField (auto)

### RestaurantLocation Model (OneToOne)
- `address`: CharField (255 chars)
- `city`: CharField (100 chars)
- `state`: CharField (50 chars)
- `zip_code`: CharField (20 chars)

## Opening Hours Format

The `opening_hours` field is a JSON object where:
- **Keys:** Day names (e.g., "Monday", "Tuesday")
- **Values:** Time ranges (e.g., "9:00 AM - 10:00 PM")

### Example

```json
{
    "Monday": "9:00 AM - 10:00 PM",
    "Tuesday": "9:00 AM - 10:00 PM",
    "Wednesday": "9:00 AM - 10:00 PM",
    "Thursday": "9:00 AM - 10:00 PM",
    "Friday": "9:00 AM - 11:00 PM",
    "Saturday": "10:00 AM - 11:00 PM",
    "Sunday": "10:00 AM - 9:00 PM"
}
```

### Empty Hours
If no opening hours are set, the field will be an empty object:
```json
{
    "opening_hours": {}
}
```

## Behavior Details

### Multiple Restaurants
If multiple restaurants exist in the database, the endpoint returns information for the **first** restaurant (ordered by ID). This is by design, as the endpoint represents "the restaurant" (main/default restaurant).

### Missing Location
If the restaurant has no associated `RestaurantLocation` record:
- `address`, `city`, `state`, `zip_code`, `full_address` will be `null`
- Other fields will still be populated normally
- No error is raised

### No Restaurant
If no restaurant exists in the database:
- Returns 404 Not Found
- Includes user-friendly error message
- Logs warning for administrators

## Testing

A comprehensive test suite with 15 tests validates all functionality:

```bash
# Run tests
python manage.py test tests.test_restaurant_info --keepdb -v 2
```

### Test Coverage

- ✅ Successful retrieval
- ✅ All fields present
- ✅ Correct values
- ✅ Full address formatting
- ✅ Opening hours structure
- ✅ Restaurant without location
- ✅ No restaurant exists (404)
- ✅ Public access (no auth)
- ✅ Multiple restaurants (returns first)
- ✅ Response structure
- ✅ Empty opening hours
- ✅ Valid JSON format
- ✅ Multiple requests consistency
- ✅ ID field included
- ✅ created_at field included

## Performance

- **Database Queries:** 1-2 queries (Restaurant + Location with `select_related`)
- **Response Time:** < 50ms typical
- **Caching:** Consider adding caching for high-traffic sites
- **Optimization:** Uses `select_related('location')` to avoid N+1 queries

## Error Handling

The endpoint includes comprehensive error handling:

1. **Database Errors:** Catches and logs all exceptions
2. **Missing Data:** Gracefully handles missing location
3. **Serialization Errors:** Handles malformed data
4. **Logging:** All operations and errors are logged

## Security

- **Read-Only:** GET endpoint only, no data modification
- **No PII Exposure:** Only public restaurant information
- **Input Validation:** No user input accepted
- **Rate Limiting:** Consider adding for production use

## Version History

- **v1.0** (Current): Initial implementation with comprehensive location support and opening hours

## Related Endpoints

- **GET /api/restaurants/**: List all restaurants (CRUD endpoint)
- **GET /api/restaurants/{id}/**: Get specific restaurant by ID
- **GET /api/daily-specials/**: Get daily specials from the restaurant

## Support

For issues or questions:
1. Check test suite for usage examples: `tests/test_restaurant_info.py`
2. Review source code: `home/views.py` (`restaurant_info` function)
3. Check serializer: `home/serializers.py` (`RestaurantInfoSerializer`)
4. Check application logs for detailed error messages

---

**Last Updated:** October 17, 2025  
**Maintainer:** Restaurant Management System Team
