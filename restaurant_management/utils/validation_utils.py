"""
Email validation utilities for the restaurant management application.

This module provides reusable email validation functions with proper error handling
and logging to ensure data integrity across the application.
"""

import re
import logging
from email.utils import parseaddr
from typing import Tuple, Optional

# Configure logger for this module
logger = logging.getLogger(__name__)

def is_valid_email(email: str, strict: bool = True) -> bool:
    """
    Validate an email address using Python's built-in email validation.
    
    Args:
        email (str): The email address to validate
        strict (bool): If True, use strict RFC 5322 validation. If False, use basic regex validation.
        
    Returns:
        bool: True if the email is valid, False otherwise
        
    Examples:
        >>> is_valid_email("user@example.com")
        True
        >>> is_valid_email("invalid.email")
        False
        >>> is_valid_email("user@domain", strict=False)
        True
    """
    if not email or not isinstance(email, str):
        logger.warning(f"Invalid email input: {type(email)} - {email}")
        return False
    
    # Remove leading/trailing whitespace
    email = email.strip()
    
    if not email:
        return False
    
    try:
        if strict:
            # Use Python's email.utils.parseaddr for RFC 5322 compliance
            parsed_name, parsed_email = parseaddr(email)
            
            # parseaddr should return empty name and valid email for simple addresses
            if not parsed_email or '@' not in parsed_email:
                return False
                
            # Additional checks for common issues
            local_part, domain = parsed_email.rsplit('@', 1)
            
            # Basic checks
            if not local_part or not domain:
                return False
                
            # Check for valid domain format (at least one dot)
            if '.' not in domain:
                return False
                
            # Check length constraints (RFC 5321)
            if len(local_part) > 64 or len(domain) > 253 or len(parsed_email) > 254:
                return False
                
            return True
        else:
            # Basic regex validation for less strict checking
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return bool(re.match(pattern, email))
            
    except Exception as e:
        logger.error(f"Error validating email '{email}': {str(e)}")
        return False


def validate_email_with_details(email: str, strict: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Validate an email address and return detailed error information.
    
    Args:
        email (str): The email address to validate
        strict (bool): If True, use strict validation
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
        
    Examples:
        >>> validate_email_with_details("user@example.com")
        (True, None)
        >>> validate_email_with_details("invalid")
        (False, "Email address must contain @ symbol")
    """
    if not email or not isinstance(email, str):
        return False, "Email must be a non-empty string"
    
    email = email.strip()
    
    if not email:
        return False, "Email address cannot be empty"
    
    if '@' not in email:
        return False, "Email address must contain @ symbol"
    
    if email.count('@') > 1:
        return False, "Email address cannot contain multiple @ symbols"
    
    try:
        local_part, domain = email.rsplit('@', 1)
        
        if not local_part:
            return False, "Email address must have content before @ symbol"
            
        if not domain:
            return False, "Email address must have a domain after @ symbol"
        
        if strict:
            if '.' not in domain:
                return False, "Domain must contain at least one dot"
            
            if len(local_part) > 64:
                return False, "Local part (before @) cannot exceed 64 characters"
                
            if len(domain) > 253:
                return False, "Domain cannot exceed 253 characters"
                
            if len(email) > 254:
                return False, "Email address cannot exceed 254 characters"
            
            # Check for valid characters
            if not re.match(r'^[a-zA-Z0-9._%+-]+$', local_part):
                return False, "Local part contains invalid characters"
                
            if not re.match(r'^[a-zA-Z0-9.-]+$', domain):
                return False, "Domain contains invalid characters"
        
        if is_valid_email(email, strict):
            return True, None
        else:
            return False, "Email format is invalid"
            
    except Exception as e:
        logger.error(f"Error validating email '{email}': {str(e)}")
        return False, f"Validation error: {str(e)}"


def normalize_email(email: str) -> str:
    """
    Normalize an email address by converting to lowercase and stripping whitespace.
    
    Args:
        email (str): The email address to normalize
        
    Returns:
        str: Normalized email address
        
    Examples:
        >>> normalize_email("  USER@EXAMPLE.COM  ")
        "user@example.com"
    """
    if not email or not isinstance(email, str):
        return ""
    
    return email.strip().lower()


def is_disposable_email_domain(email: str) -> bool:
    """
    Check if an email address uses a known disposable email domain.
    
    Note: This is a basic implementation. For production use, consider
    integrating with a comprehensive disposable email service.
    
    Args:
        email (str): The email address to check
        
    Returns:
        bool: True if the domain is likely disposable, False otherwise
    """
    if not is_valid_email(email, strict=False):
        return False
    
    try:
        domain = email.split('@')[1].lower()
        
        # Common disposable email domains (expand this list as needed)
        disposable_domains = {
            '10minutemail.com',
            'temp-mail.org',
            'guerrillamail.com',
            'mailinator.com',
            'yopmail.com',
            'throwaway.email',
            'tempail.com',
            'getnada.com'
        }
        
        return domain in disposable_domains
        
    except Exception as e:
        logger.warning(f"Error checking disposable domain for '{email}': {str(e)}")
        return False