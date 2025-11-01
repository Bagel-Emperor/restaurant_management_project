# DailySpecial Custom Manager - Implementation Guide

## Overview
This document describes the implementation of the `DailySpecial` model with a custom Django manager that efficiently filters daily specials to show only upcoming (today's and future) specials.

## Problem Statement
The existing system used a simple boolean field (`is_daily_special`) on the `MenuItem` model, which couldn't handle date-based scheduling of daily specials. We needed a more robust solution to:

1. Schedule specials for specific dates
2. Automatically filter out past specials
3. Display only relevant (upcoming) specials to customers
4. Track promotional descriptions per special

## Solution Architecture

### DailySpecial Model
Located in `home/models.py`, the `DailySpecial` model provides:

```python
class DailySpecial(models.Model):
    menu_item = ForeignKey to MenuItem (CASCADE delete)
    special_date = DateField (when the special is active)
    description = TextField (optional promotional text)
    created_at = DateTimeField (auto_now_add)
    updated_at = DateTimeField (auto_now)
```

**Key Features:**
- **Unique Together Constraint**: Prevents scheduling the same menu item twice on the same date
- **Cascade Delete**: Specials are automatically removed when menu items are deleted
- **Ordering**: Default ordering by `special_date` (earliest first)
- **Related Name**: Access specials from MenuItem via `menu_item.daily_specials.all()`

### DailySpecialManager (Custom Manager)
The custom manager inherits from `django.db.models.Manager` and provides:

#### `upcoming()` Method
Returns a QuerySet of daily specials where `special_date >= today`.

**Features:**
- Uses `datetime.date.today()` for current date comparison
- Returns QuerySet (can be chained with additional filters)
- Ordered by `special_date` (earliest first)
- Efficient single-query implementation

**Usage Examples:**
```python
# Get all upcoming specials
upcoming = DailySpecial.objects.upcoming()

# Get only available upcoming specials
available_upcoming = DailySpecial.objects.upcoming().filter(
    menu_item__is_available=True
)

# Get count of upcoming specials
count = DailySpecial.objects.upcoming().count()

# Get today's specials only
from datetime import date
today_specials = DailySpecial.objects.upcoming().filter(
    special_date=date.today()
)
```

### Additional Model Methods

#### `is_upcoming()`
Instance method that returns `True` if the special's date is today or in the future.

**Usage:**
```python
special = DailySpecial.objects.first()
if special.is_upcoming():
    print("This special is still relevant!")
```

## Database Schema

### Migration: `home/migrations/0024_dailyspecial.py`
Creates the `DailySpecial` table with:
- Foreign key to `MenuItem`
- `special_date` field (indexed for query performance)
- `description` TextField
- `created_at` and `updated_at` timestamps
- Unique constraint on `(menu_item, special_date)`

## Django Admin Integration

### DailySpecialAdmin Configuration
Located in `home/admin.py`, provides:

**List Display:**
- Menu item name
- Special date
- Is upcoming? (boolean indicator)
- Created timestamp

**Features:**
- Date hierarchy navigation by `special_date`
- Filtering by date, restaurant, and category
- Search by menu item name and description
- Fieldsets for organized form layout
- Read-only system fields (created_at, updated_at)

**Custom List Display Method:**
```python
def is_upcoming(self, obj):
    """Display whether the special is upcoming in the list view."""
    return obj.is_upcoming()
is_upcoming.boolean = True
```

## Testing

### Test Suite: `home/tests/test_daily_special_manager.py`
Comprehensive test coverage with **21 tests** across two test classes:

#### DailySpecialManagerUpcomingTests (9 tests)
Tests the `upcoming()` manager method:
1. ✅ Returns today's special
2. ✅ Returns future specials
3. ✅ Excludes past specials
4. ✅ Mixed dates (past, present, future)
5. ✅ Correct ordering (earliest first)
6. ✅ Empty queryset when no specials exist
7. ✅ Empty queryset when only past specials exist
8. ✅ Can be chained with additional filters
9. ✅ Handles multiple specials on same date

#### DailySpecialModelTests (12 tests)
Tests model functionality:
1. ✅ Create daily special
2. ✅ String representation
3. ✅ Unique together constraint
4. ✅ Optional description field
5. ✅ `is_upcoming()` for today
6. ✅ `is_upcoming()` for future
7. ✅ `is_upcoming()` for past
8. ✅ Cascade delete with menu item
9. ✅ Multiple specials for same item on different dates
10. ✅ Related name access from MenuItem
11. ✅ Default ordering by special_date
12. ✅ `updated_at` changes on save

**Test Results:**
```
Ran 21 tests in 0.096s
OK
```

## Demonstration Script

### `demo_daily_special_manager.py`
Interactive demonstration showing:
1. Data setup (restaurant, category, menu items)
2. Creating specials for various dates (past, today, future)
3. Testing `DailySpecial.objects.upcoming()` method
4. Verification that past specials are excluded
5. Verification that ordering is correct
6. Testing filter chaining capability

**Run with:**
```bash
Get-Content demo_daily_special_manager.py | python manage.py shell
```

**Output:**
```
Total upcoming specials found: 3

Upcoming Specials (ordered by date):
1. Test Special Item 2 - Date: 2025-11-01 (TODAY)
2. Test Special Item 3 - Date: 2025-11-02 (FUTURE)
3. Test Special Item 1 - Date: 2025-11-08 (FUTURE)

✓ Past special correctly excluded
✓ Today's special correctly included
✓ Future specials correctly included
✓ Results correctly ordered by date
```

## API Integration (Future Enhancement)

### Suggested Serializer
```python
class DailySpecialSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    menu_item_price = serializers.DecimalField(source='menu_item.price', 
                                               max_digits=6, decimal_places=2, 
                                               read_only=True)
    
    class Meta:
        model = DailySpecial
        fields = ['id', 'menu_item', 'menu_item_name', 'menu_item_price', 
                  'special_date', 'description']
```

### Suggested API View
```python
class UpcomingDailySpecialsAPIView(ListAPIView):
    """API endpoint for upcoming daily specials."""
    serializer_class = DailySpecialSerializer
    
    def get_queryset(self):
        return DailySpecial.objects.upcoming().filter(
            menu_item__is_available=True
        ).select_related('menu_item')
```

## Performance Considerations

### Query Optimization
1. **Single Query**: The `upcoming()` method uses a single database query with filtering
2. **Indexing**: The `special_date` field should be indexed for faster date comparisons
3. **Select Related**: When displaying menu item details, use `select_related('menu_item')` to avoid N+1 queries

### Example Optimized Query
```python
# Efficient query with related data
upcoming_specials = DailySpecial.objects.upcoming()\
    .select_related('menu_item', 'menu_item__category', 'menu_item__restaurant')\
    .filter(menu_item__is_available=True)
```

## Migration History

| Migration | Description |
|-----------|-------------|
| `0024_dailyspecial.py` | Create DailySpecial model with foreign key to MenuItem, special_date, description, timestamps, and unique constraint |

## Files Modified/Created

### Created Files:
1. `home/tests/test_daily_special_manager.py` (21 tests, 600+ lines)
2. `home/migrations/0024_dailyspecial.py` (migration file)
3. `demo_daily_special_manager.py` (demonstration script, 180+ lines)
4. `DAILY_SPECIAL_MANAGER_GUIDE.md` (this documentation)

### Modified Files:
1. `home/models.py` - Added `DailySpecialManager` and `DailySpecial` model
2. `home/admin.py` - Added `DailySpecialAdmin` configuration

## Usage Recommendations

### For Restaurant Managers
1. Use Django admin to schedule daily specials in advance
2. Set specific dates for promotional items
3. Include engaging descriptions to attract customers
4. Review upcoming specials regularly to ensure accuracy

### For Developers
1. Use `DailySpecial.objects.upcoming()` for customer-facing displays
2. Chain with `.filter(menu_item__is_available=True)` for active items only
3. Use `select_related()` for optimized queries with menu item details
4. Consider caching upcoming specials if high traffic expected

### For Marketing
1. Schedule specials during slow business days to drive traffic
2. Create themed specials for holidays or events
3. Use descriptive promotional text to highlight value
4. Plan specials in advance for consistent promotion

## Future Enhancements

### Potential Features:
1. **Recurring Specials**: Add support for "Every Monday" type patterns
2. **Time-based Specials**: Add time fields for breakfast/lunch/dinner specials
3. **Multi-day Specials**: Support date ranges instead of single dates
4. **Notification System**: Auto-notify customers about upcoming specials
5. **Analytics**: Track which specials drive the most orders
6. **Image Support**: Add special-specific promotional images

### API Endpoints (Suggested):
- `GET /api/daily-specials/upcoming/` - List all upcoming specials
- `GET /api/daily-specials/today/` - Today's specials only
- `GET /api/daily-specials/{id}/` - Detail view of a specific special
- `POST /api/daily-specials/` - Create new special (admin only)

## Conclusion

This implementation provides a robust, scalable solution for managing daily specials with proper date filtering. The custom manager pattern follows Django best practices and provides a clean, reusable API for querying upcoming specials throughout the application.

**Key Achievements:**
✅ Custom Django manager with `upcoming()` method  
✅ Comprehensive 21-test suite (100% passing)  
✅ Django admin integration with enhanced UI  
✅ Database migration applied successfully  
✅ Demonstration script validates functionality  
✅ Documentation and examples provided  

**Commit:** `e1299c4` - "Implement DailySpecial model with custom manager to filter upcoming specials - Task complete with 21 comprehensive tests"
