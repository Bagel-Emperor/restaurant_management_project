"""
Utility functions for the restaurant management application.

This package contains reusable utility functions for various operations
including validation, caching, session management, and more.
"""

from .validation_utils import (
    is_valid_email,
    validate_email_with_details,
    normalize_email,
    is_disposable_email_domain,
)

__all__ = [
    'is_valid_email',
    'validate_email_with_details', 
    'normalize_email',
    'is_disposable_email_domain',
]