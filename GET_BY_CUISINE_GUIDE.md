# Model Method: Get Menu Items by Cuisine - Testing Guide

## Overview
The `MenuItem.get_by_cuisine()` classmethod filters menu items by cuisine type (category name).

## Implementation Details
- **Location**: `home/models.py` - `MenuItem` model
- **Method Type**: `@classmethod`
- **Parameter**: `cuisine_type` (str) - The cuisine/category name to filter by
- **Returns**: QuerySet of MenuItem objects
- **Note**: In this project, "cuisine" maps to `MenuCategory.name`

## Method Signature
```python
@classmethod
def get_by_cuisine(cls, cuisine_type):
    """
    Filter menu items by cuisine type (category name).
    
    Args:
        cuisine_type (str): The cuisine/category type to filter by
    
    Returns:
        QuerySet: Filtered queryset of MenuItem objects
    """
```

## Testing in Django Shell

### 1. Import Required Models
```python
from home.models import MenuItem, MenuCategory, Restaurant
from decimal import Decimal
```

### 2. Create Test Data (if not already exists)
```python
# Create a restaurant
restaurant = Restaurant.objects.create(
    name="Test Restaurant",
    owner_name="Test Owner",
    email="test@example.com",
    phone_number="555-0123"
)

# Create categories (cuisines)
italian = MenuCategory.objects.create(name="Italian", description="Italian cuisine")
chinese = MenuCategory.objects.create(name="Chinese", description="Chinese cuisine")
desserts = MenuCategory.objects.create(name="Desserts", description="Dessert items")

# Create menu items
pasta = MenuItem.objects.create(
    name="Spaghetti Carbonara",
    description="Classic Italian pasta",
    price=Decimal('15.99'),
    restaurant=restaurant,
    category=italian,
    is_available=True
)

pizza = MenuItem.objects.create(
    name="Margherita Pizza",
    description="Traditional Italian pizza",
    price=Decimal('12.99'),
    restaurant=restaurant,
    category=italian,
    is_available=True
)

fried_rice = MenuItem.objects.create(
    name="Yangzhou Fried Rice",
    description="Traditional Chinese fried rice",
    price=Decimal('10.99'),
    restaurant=restaurant,
    category=chinese,
    is_available=True
)

tiramisu = MenuItem.objects.create(
    name="Tiramisu",
    description="Italian coffee dessert",
    price=Decimal('7.99'),
    restaurant=restaurant,
    category=desserts,
    is_available=True
)
```

### 3. Test Basic Usage
```python
# Get all Italian items
italian_items = MenuItem.get_by_cuisine('Italian')
print(f"Italian items count: {italian_items.count()}")  # Output: 2
for item in italian_items:
    print(f"  - {item.name}: ${item.price}")

# Get all Chinese items
chinese_items = MenuItem.get_by_cuisine('Chinese')
print(f"Chinese items count: {chinese_items.count()}")  # Output: 1
```

### 4. Test Case-Insensitive Search
```python
# All of these should return the same results
italian_lower = MenuItem.get_by_cuisine('italian')
italian_upper = MenuItem.get_by_cuisine('ITALIAN')
italian_mixed = MenuItem.get_by_cuisine('ItAlIaN')

print(italian_lower.count())  # Output: 2
print(italian_upper.count())  # Output: 2
print(italian_mixed.count())  # Output: 2
```

### 5. Test Empty Results
```python
# Nonexistent cuisine
mexican = MenuItem.get_by_cuisine('Mexican')
print(mexican.exists())  # Output: False
print(mexican.count())   # Output: 0

# None/empty string
none_result = MenuItem.get_by_cuisine(None)
empty_result = MenuItem.get_by_cuisine('')
print(none_result.count())   # Output: 0
print(empty_result.count())  # Output: 0
```

### 6. Test QuerySet Chaining
```python
# Filter by cuisine and availability
available_italian = MenuItem.get_by_cuisine('Italian').filter(is_available=True)
print(f"Available Italian items: {available_italian.count()}")

# Filter by cuisine and price range
affordable_italian = MenuItem.get_by_cuisine('Italian').filter(price__lt=Decimal('15.00'))
print(f"Italian items under $15: {affordable_italian.count()}")

# Order by price
italian_by_price = MenuItem.get_by_cuisine('Italian').order_by('price')
for item in italian_by_price:
    print(f"{item.name}: ${item.price}")
```

### 7. Test with select_related (Query Optimization)
```python
# Optimize database queries
items = MenuItem.get_by_cuisine('Italian').select_related('category', 'restaurant')
for item in items:
    print(f"{item.name} - {item.category.name} from {item.restaurant.name}")
```

## Test Results

### Unit Tests
All 25 comprehensive unit tests pass:
- ✅ Basic cuisine filtering (Italian, Chinese, Desserts, Appetizers)
- ✅ Case-insensitive search
- ✅ Empty/None cuisine handling
- ✅ QuerySet type verification
- ✅ QuerySet chaining capabilities
- ✅ Ordering and filtering
- ✅ Query optimization (select_related, prefetch_related)
- ✅ Featured items and daily specials filtering
- ✅ Multiple restaurants support
- ✅ Special characters in cuisine names

### Test Command
```bash
python manage.py test home.tests.test_get_by_cuisine -v 2
```

## Expected Behavior

### Returns QuerySet
The method returns a Django QuerySet, not a list. This allows:
- Chaining with other QuerySet methods (`.filter()`, `.order_by()`, etc.)
- Lazy evaluation (queries only run when data is accessed)
- Query optimization (`.select_related()`, `.prefetch_related()`, `.only()`)

### Case-Insensitive Matching
Uses `category__name__iexact` for case-insensitive matching:
- `'Italian'` matches `'italian'`, `'ITALIAN'`, `'ItAlIaN'`

### Null Safety
Handles edge cases gracefully:
- `None` returns empty QuerySet
- Empty string `''` returns empty QuerySet
- Nonexistent cuisine returns empty QuerySet

### Excludes Null Categories
Items with `category=None` are automatically excluded from results.

## Integration with Existing Code

This method complements the existing `get_distinct_cuisines()` utility:
```python
from home.utils import get_distinct_cuisines

# Get all available cuisines
cuisines = get_distinct_cuisines()
print(cuisines)  # ['Appetizers', 'Chinese', 'Desserts', 'Italian']

# Get items for each cuisine
for cuisine in cuisines:
    items = MenuItem.get_by_cuisine(cuisine)
    print(f"{cuisine}: {items.count()} items")
```

## Performance Considerations

### Efficient Filtering
- Single database query using `filter(category__name__iexact=...)`
- No additional queries for null checks

### Query Optimization
Returns QuerySet for optimization opportunities:
```python
# Reduce queries with select_related
items = MenuItem.get_by_cuisine('Italian').select_related('category', 'restaurant')

# Fetch only needed fields
items = MenuItem.get_by_cuisine('Italian').only('name', 'price')

# Prefetch related data
items = MenuItem.get_by_cuisine('Italian').prefetch_related('ingredients')
```

## Common Use Cases

### 1. Display Cuisine-Specific Menu
```python
cuisine = 'Italian'
items = MenuItem.get_by_cuisine(cuisine).filter(is_available=True)
```

### 2. Featured Items by Cuisine
```python
featured_italian = MenuItem.get_by_cuisine('Italian').filter(is_featured=True)
```

### 3. Daily Specials by Cuisine
```python
chinese_specials = MenuItem.get_by_cuisine('Chinese').filter(is_daily_special=True)
```

### 4. Price-Based Filtering
```python
budget_options = MenuItem.get_by_cuisine('Italian').filter(price__lte=Decimal('10.00'))
```

## Conclusion

The `get_by_cuisine()` method provides a clean, efficient way to filter menu items by cuisine type (category name) with:
- ✅ 25 comprehensive tests passing
- ✅ Case-insensitive search
- ✅ QuerySet chaining support
- ✅ Null safety
- ✅ Query optimization capabilities
- ✅ Integration with existing utilities

**Task Status**: ✅ COMPLETED
