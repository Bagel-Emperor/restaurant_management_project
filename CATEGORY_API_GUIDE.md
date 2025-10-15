# Category-based Menu Item API Documentation

## Overview
This API allows filtering menu items by category, providing a structured way to organize and retrieve menu items based on their assigned categories.

## Endpoints

### 1. Menu Category CRUD Operations

#### List All Menu Categories
```
GET /PerpexBistro/api/menu-categories/
```

**Description**: Retrieve a list of all available menu categories (ordered alphabetically by name).

**Authentication**: Not required (public access)

**Response Example**:
```json
[
    {
        "id": 1,
        "name": "Appetizers"
    },
    {
        "id": 2,
        "name": "Desserts"
    },
    {
        "id": 3,
        "name": "Main Courses"
    }
]
```

#### Retrieve Single Menu Category
```
GET /PerpexBistro/api/menu-categories/{id}/
```

**Description**: Retrieve details of a specific menu category by ID.

**Authentication**: Not required (public access)

**Response Example**:
```json
{
    "id": 1,
    "name": "Appetizers"
}
```

#### Create Menu Category
```
POST /PerpexBistro/api/menu-categories/
```

**Description**: Create a new menu category.

**Authentication**: Required (must be authenticated user)

**Request Body**:
```json
{
    "name": "Beverages"
}
```

**Response Example** (201 Created):
```json
{
    "id": 4,
    "name": "Beverages"
}
```

**Notes**: 
- Category creation is logged in the system
- Category names must be unique

#### Update Menu Category
```
PUT /PerpexBistro/api/menu-categories/{id}/
PATCH /PerpexBistro/api/menu-categories/{id}/
```

**Description**: Update an existing menu category (PUT for full update, PATCH for partial).

**Authentication**: Required (must be authenticated user)

**Request Body**:
```json
{
    "name": "Drinks & Beverages"
}
```

**Response Example** (200 OK):
```json
{
    "id": 4,
    "name": "Drinks & Beverages"
}
```

**Notes**: Category updates are logged in the system

#### Delete Menu Category
```
DELETE /PerpexBistro/api/menu-categories/{id}/
```

**Description**: Delete a menu category.

**Authentication**: Required (must be authenticated user)

**Response**: 204 No Content

**Notes**: 
- Category deletion is logged in the system
- Consider impact on menu items with this category before deletion

### 2. List Menu Items (with Category Support)
```
GET /PerpexBistro/api/menu-items/
```

**Description**: Retrieve all menu items with category information included.

**Response Example**:
```json
[
    {
        "id": 1,
        "name": "Caesar Salad",
        "description": "Fresh romaine lettuce with caesar dressing",
        "price": "12.99",
        "restaurant": 1,
        "category": 1,
        "category_name": "Appetizers",
        "is_available": true,
        "image": null,
        "created_at": "2025-09-22T06:22:36.037724Z"
    },
    {
        "id": 2,
        "name": "Grilled Salmon",
        "description": "Fresh salmon with herbs",
        "price": "24.99",
        "restaurant": 1,
        "category": 2,
        "category_name": "Main Courses",
        "is_available": true,
        "image": null,
        "created_at": "2025-09-22T06:22:36.037724Z"
    }
]
```

### 3. Filter Menu Items by Category

#### Filter by Category ID
```
GET /PerpexBistro/api/menu-items/?category=1
```

#### Filter by Category Name (case-insensitive, partial matching)
```
GET /PerpexBistro/api/menu-items/?category=appetizers
```

#### Filter by Partial Category Name
```
GET /PerpexBistro/api/menu-items/?category=app
```
This will match "Appetizers" category.

### 4. Combined Filtering

You can combine category filtering with other existing filters:

#### Category + Availability
```
GET /PerpexBistro/api/menu-items/?category=1&available=true
```

#### Category + Restaurant
```
GET /PerpexBistro/api/menu-items/?category=2&restaurant=1
```

#### Category + Restaurant + Availability
```
GET /PerpexBistro/api/menu-items/?category=1&restaurant=1&available=true
```

## Database Schema Changes

### MenuItem Model Updates
- Added `category` field as ForeignKey to MenuCategory
- Relationship: `MenuItem.category -> MenuCategory`
- Allows null values (menu items can exist without categories)

### Serializer Enhancements
- Added `category_name` field for easy access to category name
- Uses SerializerMethodField to handle null categories gracefully

## Features

### ✅ Implemented Features
1. **Full CRUD for Categories**: Create, Read, Update, and Delete menu categories via REST API
2. **Category Relationship**: MenuItem has a ForeignKey to MenuCategory
3. **Category Filtering**: Filter menu items by category ID or name
4. **Partial Name Matching**: Filter using partial category names (case-insensitive)
5. **Combined Filtering**: Combine category filters with existing restaurant/availability filters
6. **Graceful Null Handling**: Menu items without categories return `null` for category fields
7. **Optimized Queries**: Uses `select_related()` for efficient database queries
8. **Audit Logging**: All category create/update/delete operations are logged

### 🎯 API Behavior
- **Public Read Access**: List and retrieve operations are publicly accessible (no authentication required)
- **Authenticated Write Access**: Create, update, and delete operations require authentication
- **Case-Insensitive**: Category name filtering is case-insensitive
- **Partial Matching**: Supports partial category name matching using `icontains`
- **Empty Results**: Invalid categories return empty result sets (not errors)
- **Backward Compatible**: Existing API functionality remains unchanged

## Usage Examples

### Frontend Integration
```javascript
// Get all categories for a dropdown menu
fetch('/PerpexBistro/api/menu-categories/')
  .then(response => response.json())
  .then(categories => {
    categories.forEach(cat => {
      console.log(`${cat.name} (ID: ${cat.id})`);
    });
  });

// Filter menu items by selected category
const categoryId = 1;
fetch(`/PerpexBistro/api/menu-items/?category=${categoryId}`)
  .then(response => response.json())
  .then(menuItems => {
    menuItems.forEach(item => {
      console.log(`${item.name} - ${item.category_name}`);
    });
  });
```

### Python/Django Usage
```python
from home.models import MenuItem, MenuCategory

# Get all appetizers
appetizers = MenuItem.objects.filter(category__name__icontains='appetizers')

# Get available main courses
main_courses = MenuItem.objects.filter(
    category__name='Main Courses',
    is_available=True
)
```

## Testing

Comprehensive test suite included:
- 11 unit tests covering all filtering scenarios
- Tests for combined filtering
- Edge cases (null categories, invalid inputs)
- Response structure validation

Run tests with:
```bash
python manage.py test tests.test_category_menu_api
```