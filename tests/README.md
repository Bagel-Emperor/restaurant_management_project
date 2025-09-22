# Tests Directory

This directory contains test files and utilities for the Restaurant Management System.

## Files

### `test_menu_api.py`
Comprehensive test suite for the MenuItemViewSet API endpoint. Tests:
- Authentication and authorization
- CRUD operations (Create, Read, Update, Delete)
- Input validation (price positivity, name requirements)
- Custom actions (toggle availability)
- Filtering capabilities
- Error handling

**Usage:**
```bash
python tests/test_menu_api.py
```

## Running Tests

To run individual test files:
```bash
cd restaurant_management_project
python tests/test_menu_api.py
```

To run Django's built-in tests:
```bash
python manage.py test
```

## Test Data

Tests create temporary data that is cleaned up automatically. They use:
- Test restaurant "Test Restaurant"
- Test admin user "testadmin"
- Temporary menu items for testing CRUD operations