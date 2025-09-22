# Menu Item Search API Documentation

## Overview
This comprehensive search API allows users to search, filter, and sort menu items using multiple criteria. It provides powerful search capabilities across menu item names and descriptions, along with advanced filtering options.

## Search Endpoint

### Base URL
```
GET /PerpexBistro/api/menu-items/
```

## Search Parameters

### 1. Text Search
**Parameter**: `search`  
**Description**: Search across menu item names and descriptions (case-insensitive, partial matching)

```bash
# Search for items containing "caesar"
GET /PerpexBistro/api/menu-items/?search=caesar

# Search for items containing "grilled" in name or description  
GET /PerpexBistro/api/menu-items/?search=grilled

# Search for partial matches
GET /PerpexBistro/api/menu-items/?search=choc
```

### 2. Category Filtering
**Parameter**: `category`  
**Description**: Filter by category ID or name

```bash
# Filter by category ID
GET /PerpexBistro/api/menu-items/?category=1

# Filter by category name (case-insensitive)
GET /PerpexBistro/api/menu-items/?category=appetizers

# Partial category name matching
GET /PerpexBistro/api/menu-items/?category=main
```

### 3. Price Range Filtering
**Parameters**: `min_price`, `max_price`  
**Description**: Filter by price range

```bash
# Items with minimum price of $20
GET /PerpexBistro/api/menu-items/?min_price=20.00

# Items with maximum price of $15
GET /PerpexBistro/api/menu-items/?max_price=15.00

# Items in price range $10-$20
GET /PerpexBistro/api/menu-items/?min_price=10.00&max_price=20.00
```

### 4. Availability Filtering
**Parameter**: `available`  
**Description**: Filter by availability status

```bash
# Only available items
GET /PerpexBistro/api/menu-items/?available=true

# Only unavailable items
GET /PerpexBistro/api/menu-items/?available=false
```

### 5. Restaurant Filtering
**Parameter**: `restaurant`  
**Description**: Filter by restaurant ID

```bash
# Items from specific restaurant
GET /PerpexBistro/api/menu-items/?restaurant=1
```

### 6. Sorting/Ordering
**Parameter**: `ordering`  
**Description**: Sort results by various fields

```bash
# Sort by price (ascending)
GET /PerpexBistro/api/menu-items/?ordering=price

# Sort by price (descending)
GET /PerpexBistro/api/menu-items/?ordering=-price

# Sort by name (ascending)
GET /PerpexBistro/api/menu-items/?ordering=name

# Sort by name (descending)
GET /PerpexBistro/api/menu-items/?ordering=-name

# Sort by creation date (newest first)
GET /PerpexBistro/api/menu-items/?ordering=-created_at

# Sort by category name
GET /PerpexBistro/api/menu-items/?ordering=category__name
```

## Combined Search Examples

### 1. Search + Category + Price Range
```bash
GET /PerpexBistro/api/menu-items/?search=grilled&category=main&min_price=20.00
```
Find grilled items in main courses costing at least $20.

### 2. Search + Availability + Sorting
```bash
GET /PerpexBistro/api/menu-items/?search=caesar&available=true&ordering=price
```
Find available caesar items sorted by price.

### 3. Category + Price Range + Restaurant
```bash
GET /PerpexBistro/api/menu-items/?category=appetizers&max_price=15.00&restaurant=1&ordering=name
```
Find appetizers under $15 from restaurant 1, sorted by name.

### 4. Complex Multi-Filter Search
```bash
GET /PerpexBistro/api/menu-items/?search=chicken&category=main&min_price=15.00&max_price=25.00&available=true&ordering=-price
```
Find available chicken dishes in main courses between $15-$25, sorted by price descending.

## Response Format

### Paginated Response Structure
```json
{
    "count": 25,
    "next": "http://127.0.0.1:8000/PerpexBistro/api/menu-items/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Caesar Salad",
            "description": "Fresh romaine lettuce with caesar dressing and croutons",
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
            "name": "Chicken Caesar Wrap",
            "description": "Grilled chicken with caesar salad in a tortilla wrap",
            "price": "15.99",
            "restaurant": 1,
            "category": 2,
            "category_name": "Main Courses",
            "is_available": true,
            "image": null,
            "created_at": "2025-09-22T06:22:36.037724Z"
        }
    ]
}
```

### Search Response Fields
- **count**: Total number of matching items
- **next**: URL for next page (if any)
- **previous**: URL for previous page (if any)
- **results**: Array of matching menu items

### Menu Item Fields
- **id**: Unique identifier
- **name**: Menu item name
- **description**: Item description
- **price**: Item price (string format)
- **restaurant**: Restaurant ID
- **category**: Category ID (null if uncategorized)
- **category_name**: Category name (null if uncategorized)
- **is_available**: Availability status
- **image**: Image URL (null if no image)
- **created_at**: Creation timestamp

## Pagination

- **Default page size**: 20 items per page
- **Page parameter**: `page`
- **Navigation**: Use `next` and `previous` URLs from response

```bash
# Get page 2 of search results
GET /PerpexBistro/api/menu-items/?search=pizza&page=2

# Get page 3 with filters
GET /PerpexBistro/api/menu-items/?category=main&available=true&page=3
```

## Error Handling

### Invalid Price Filters
```json
{
    "min_price": ["Invalid minimum price. Must be a valid number."]
}
```

### Invalid Restaurant ID
```json
{
    "restaurant": ["Invalid restaurant ID. Must be a valid integer."]
}
```

## Frontend Integration Examples

### JavaScript/Fetch API
```javascript
// Basic search
const searchMenuItems = async (query) => {
    const response = await fetch(`/PerpexBistro/api/menu-items/?search=${encodeURIComponent(query)}`);
    const data = await response.json();
    return data.results || data;
};

// Advanced search with filters
const advancedSearch = async (filters) => {
    const params = new URLSearchParams();
    
    if (filters.search) params.append('search', filters.search);
    if (filters.category) params.append('category', filters.category);
    if (filters.minPrice) params.append('min_price', filters.minPrice);
    if (filters.maxPrice) params.append('max_price', filters.maxPrice);
    if (filters.available !== undefined) params.append('available', filters.available);
    if (filters.ordering) params.append('ordering', filters.ordering);
    
    const response = await fetch(`/PerpexBistro/api/menu-items/?${params}`);
    return await response.json();
};

// Usage examples
searchMenuItems('caesar').then(items => console.log(items));

advancedSearch({
    search: 'chicken',
    category: 'main',
    minPrice: 15,
    maxPrice: 25,
    available: true,
    ordering: '-price'
}).then(data => console.log(data));
```

### React Component Example
```jsx
const MenuSearch = () => {
    const [searchTerm, setSearchTerm] = useState('');
    const [category, setCategory] = useState('');
    const [priceRange, setPriceRange] = useState({ min: '', max: '' });
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);

    const performSearch = async () => {
        setLoading(true);
        const params = new URLSearchParams();
        
        if (searchTerm) params.append('search', searchTerm);
        if (category) params.append('category', category);
        if (priceRange.min) params.append('min_price', priceRange.min);
        if (priceRange.max) params.append('max_price', priceRange.max);
        
        try {
            const response = await fetch(`/PerpexBistro/api/menu-items/?${params}`);
            const data = await response.json();
            setResults(data.results || data);
        } catch (error) {
            console.error('Search failed:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <input 
                type="text"
                placeholder="Search menu items..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && performSearch()}
            />
            <button onClick={performSearch} disabled={loading}>
                {loading ? 'Searching...' : 'Search'}
            </button>
            
            {/* Display results */}
            <div>
                {results.map(item => (
                    <div key={item.id}>
                        <h3>{item.name}</h3>
                        <p>{item.description}</p>
                        <p>${item.price} - {item.category_name}</p>
                    </div>
                ))}
            </div>
        </div>
    );
};
```

## Performance Features

- **Optimized Queries**: Uses `select_related()` for efficient database queries
- **Pagination**: Handles large result sets efficiently
- **Indexed Searches**: Case-insensitive searches using database indexes
- **Minimal Queries**: Related data fetched in single query to avoid N+1 problems

## Search Use Cases

1. **Customer Menu Browsing**: Search for specific dishes
2. **Dietary Filtering**: Find items by category (vegetarian, desserts, etc.)
3. **Budget Shopping**: Filter by price range
4. **Restaurant-Specific Search**: Search within a specific restaurant
5. **Admin Management**: Sort and filter for restaurant management
6. **Mobile App Integration**: Efficient API for mobile applications

## Testing

The search API includes comprehensive test coverage:
- Text search functionality (name and description)
- Case-insensitive and partial matching
- Price range filtering
- Category filtering
- Combined filtering scenarios
- Ordering and sorting
- Pagination behavior
- Error handling
- Performance optimization verification

Run tests with:
```bash
python manage.py test tests.test_menu_search_api
```