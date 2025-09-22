# Email Validation Utility - Usage Guide

## Overview
The email validation utility provides robust, reusable email validation functions with proper error handling and logging. It's integrated throughout the application for consistent email validation.

## Functions Available

### `is_valid_email(email, strict=True)`
Basic email validation that returns True/False.

```python
from restaurant_management.utils import is_valid_email

# Valid emails
is_valid_email("user@example.com")          # True
is_valid_email("test.email+tag@domain.co")  # True

# Invalid emails  
is_valid_email("invalid.email")             # False
is_valid_email("@domain.com")               # False
is_valid_email("user@")                     # False
```

### `validate_email_with_details(email, strict=True)`
Detailed validation with specific error messages.

```python
from restaurant_management.utils import validate_email_with_details

valid, error = validate_email_with_details("user@example.com")
# Returns: (True, None)

valid, error = validate_email_with_details("invalid")
# Returns: (False, "Email address must contain @ symbol")
```

### `normalize_email(email)`
Normalizes email addresses for consistent storage.

```python
from restaurant_management.utils import normalize_email

normalized = normalize_email("  USER@EXAMPLE.COM  ")
# Returns: "user@example.com"
```

### `is_disposable_email_domain(email)`
Checks for known disposable email providers.

```python
from restaurant_management.utils import is_disposable_email_domain

is_disposable_email_domain("test@10minutemail.com")  # True
is_disposable_email_domain("user@gmail.com")         # False
```

## Integration Points

### 1. Account Views (`account/views.py`)
- Staff login validation
- Email normalization before authentication

### 2. Contact Forms (`home/forms.py`)
- ContactSubmissionForm with custom email validation
- Enhanced form widgets with better UX

### 3. Order Serializers (`orders/serializers.py`)
- CustomerSerializer with email validation
- Detailed error messages for API responses

## Error Handling
All functions include proper exception handling and logging. Validation errors are logged at the WARNING level, while unexpected errors are logged at ERROR level.

## Testing
The validation utility can be tested manually:

```python
# In Django shell
from restaurant_management.utils import *

# Test various email formats
test_emails = [
    "valid@example.com",
    "invalid.email",
    "user@domain.co.uk",
    "@invalid.com",
    "user@",
    ""
]

for email in test_emails:
    valid, error = validate_email_with_details(email)
    print(f"{email}: {valid} - {error}")
```