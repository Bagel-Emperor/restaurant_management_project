# Daily Specials API Guide

## Overview
The Daily Specials API endpoint provides a way to retrieve all menu items that are marked as daily specials and are currently available. This endpoint is publicly accessible and returns paginated results.

## Endpoint Details

### URL
```
GET /api/daily-specials/
```

### Authentication
**None required** - This is a public endpoint accessible to all users.

### Method
`GET`

### Response Format
The endpoint returns a paginated JSON response with the following structure:

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 5,
      "name": "Grilled Salmon Special",
      "description": "Fresh Atlantic salmon with lemon butter sauce",
      "price": "22.50",
      "category_name": "Main Course",
      "restaurant_name": "Perpex Bistro",
      "image": "/media/menu_items/salmon.jpg",
      "is_available": true
    },
    {
      "id": 8,
      "name": "Truffle Pasta Special",
      "description": "Handmade pasta with black truffle cream sauce",
      "price": "28.99",
      "category_name": "Pasta",
      "restaurant_name": "Perpex Bistro",
      "image": null,
      "is_available": true
    }
  ]
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique identifier for the menu item |
| `name` | string | Name of the menu item |
| `description` | string | Detailed description of the item |
| `price` | string (decimal) | Price of the item in decimal format |
| `category_name` | string | Name of the category this item belongs to |
| `restaurant_name` | string | Name of the restaurant offering this item |
| `image` | string (nullable) | URL to the item's image (null if no image) |
| `is_available` | boolean | Availability status (always true for returned items) |

## Filtering Logic

The endpoint automatically filters menu items based on two conditions:
1. **`is_daily_special = True`** - Item is marked as a daily special
2. **`is_available = True`** - Item is currently available for order

Items that are marked as daily specials but are not available will NOT be returned by this endpoint.

## Usage Examples

### Using cURL
```bash
curl -X GET http://localhost:8000/api/daily-specials/
```

### Using Python (requests)
```python
import requests

response = requests.get('http://localhost:8000/api/daily-specials/')
data = response.json()

print(f"Found {data['count']} daily specials:")
for item in data['results']:
    print(f"- {item['name']}: ${item['price']} ({item['category_name']})")
```

### Using JavaScript (fetch)
```javascript
fetch('http://localhost:8000/api/daily-specials/')
  .then(response => response.json())
  .then(data => {
    console.log(`Found ${data.count} daily specials:`);
    data.results.forEach(item => {
      console.log(`- ${item.name}: $${item.price} (${item.category_name})`);
    });
  });
```

### Using Django Test Client
```python
from django.test import Client

client = Client()
response = client.get('/api/daily-specials/')
data = response.json()

assert response.status_code == 200
assert 'results' in data
```

## Testing

A comprehensive test script is available at `test_daily_specials.py` in the project root. Run it with:

```bash
python test_daily_specials.py
```

The test script validates:
- ✅ API endpoint returns 200 OK
- ✅ Response contains only daily specials that are available
- ✅ Response format matches DailySpecialSerializer
- ✅ All returned items have correct flags
- ✅ API endpoint is publicly accessible

## Implementation Details

### Model Field
The `MenuItem` model includes an `is_daily_special` field:
```python
is_daily_special = models.BooleanField(
    default=False,
    help_text="Mark this item as a daily special"
)
```

### Serializer
The `DailySpecialSerializer` provides computed fields for category and restaurant names:
```python
class DailySpecialSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()
    restaurant_name = serializers.SerializerMethodField()
    
    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'description', 'price', 'category_name', 
                  'restaurant_name', 'image', 'is_available']
```

### View
The view uses Django REST Framework's `ListAPIView` with optimized queries:
```python
class DailySpecialsAPIView(ListAPIView):
    serializer_class = DailySpecialSerializer
    
    def get_queryset(self):
        return MenuItem.objects.filter(
            is_daily_special=True,
            is_available=True
        ).select_related('category', 'restaurant')
```

## Performance Considerations

- The endpoint uses `select_related()` to prevent N+1 query issues
- Results are paginated automatically by Django REST Framework
- No authentication checks, making it very fast for public access

## Common Use Cases

1. **Display daily specials on homepage**: Fetch and display featured items
2. **Restaurant menu boards**: Show today's special offerings
3. **Mobile app integration**: Highlight special deals
4. **Email campaigns**: Generate content for promotional emails

## Troubleshooting

### No items returned?
- Check that items have `is_daily_special=True` in the database
- Verify items have `is_available=True`
- Check items exist for the restaurant

### Wrong items returned?
- Verify the `is_daily_special` flag is set correctly
- Check the `is_available` flag on items
- Use Django admin to inspect database values

## Related Documentation
- [Menu Item API Guide](MENU_ITEM_API_GUIDE.md)
- [Order Manager Guide](ORDER_MANAGER_GUIDE.md)
- [API Authentication](JWT_AUTHENTICATION.md)
