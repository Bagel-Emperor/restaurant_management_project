"""
Utility functions for the home application.

This module contains reusable utility functions for restaurant operations,
including opening hours validation, restaurant status checking, and other
restaurant management utilities.
"""

import logging
from datetime import datetime, time
from typing import Optional, Dict, Any, Tuple
import re

from django.conf import settings

# Import models at module level to avoid repeated import overhead
try:
    from .models import Restaurant
except ImportError:
    # Handle case where models aren't available (e.g., during migrations)
    Restaurant = None

logger = logging.getLogger(__name__)


def parse_time_range(time_str: str) -> Tuple[Optional[time], Optional[time]]:
    """
    Parse a time range string into start and end time objects.
    
    Supports formats like:
    - "9am-5pm"
    - "9:00am-5:30pm" 
    - "09:00-17:30"
    - "Closed" (returns None, None)
    - "24/7" or "24 hours" (returns 00:00, 23:59)
    
    Args:
        time_str (str): Time range string to parse
        
    Returns:
        tuple[Optional[time], Optional[time]]: (start_time, end_time) or (None, None) if closed
    
    Example:
        >>> parse_time_range("9am-5pm")
        (datetime.time(9, 0), datetime.time(17, 0))
        >>> parse_time_range("Closed")
        (None, None)
    """
    if not time_str or not isinstance(time_str, str):
        return None, None
    
    time_str = time_str.strip().lower()
    
    # Handle special cases
    if time_str in ['closed', 'close', '']:
        return None, None
    
    if time_str in ['24/7', '24 hours', 'all day']:
        return time(0, 0), time(23, 59)
    
    # Parse time ranges like "9am-5pm", "9:30am-5:30pm", "09:00-17:30"
    time_patterns = [
        # 12-hour format with am/pm
        r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)\s*-\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)',
        # 24-hour format
        r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})',
        # Simple hour format
        r'(\d{1,2})\s*-\s*(\d{1,2})'
    ]
    
    for pattern in time_patterns:
        match = re.match(pattern, time_str)
        if match:
            try:
                groups = match.groups()
                
                if len(groups) == 6:  # 12-hour format with am/pm
                    start_hour = int(groups[0])
                    start_min = int(groups[1]) if groups[1] else 0
                    start_period = groups[2]
                    end_hour = int(groups[3])
                    end_min = int(groups[4]) if groups[4] else 0
                    end_period = groups[5]
                    
                    # Convert to 24-hour format
                    if start_period == 'pm' and start_hour != 12:
                        start_hour += 12
                    elif start_period == 'am' and start_hour == 12:
                        start_hour = 0
                    
                    if end_period == 'pm' and end_hour != 12:
                        end_hour += 12
                    elif end_period == 'am' and end_hour == 12:
                        end_hour = 0
                    
                    return time(start_hour, start_min), time(end_hour, end_min)
                
                elif len(groups) == 4:  # 24-hour format
                    start_hour, start_min, end_hour, end_min = map(int, groups)
                    return time(start_hour, start_min), time(end_hour, end_min)
                
                elif len(groups) == 2:  # Simple hour format
                    start_hour, end_hour = map(int, groups)
                    return time(start_hour, 0), time(end_hour, 0)
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse time range '{time_str}': {e}")
                continue
    
    logger.warning(f"Could not parse time range: '{time_str}'")
    return None, None


def get_restaurant_hours() -> Dict[str, str]:
    """
    Get restaurant opening hours from database or fallback to settings.
    
    Returns:
        Dict[str, str]: Dictionary with day names as keys and time ranges as values
        
    Example:
        {
            'Monday': '9am-5pm',
            'Tuesday': '9am-5pm', 
            'Wednesday': 'Closed',
            ...
        }
    """
    try:
        # Try to get hours from database (Restaurant model)
        if Restaurant is not None:
            restaurant = Restaurant.objects.first()
            
            if restaurant and restaurant.opening_hours:
                # Ensure all days are present
                days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                hours = {}
                
                for day in days:
                    hours[day] = restaurant.opening_hours.get(day, 'Closed')
                
                return hours
            
    except Exception as e:
        logger.warning(f"Could not retrieve restaurant hours from database: {e}")
    
    # Fallback to settings
    settings_hours = getattr(settings, 'RESTAURANT_HOURS', 'Mon-Fri: 9am-5pm, Sat-Sun: 10am-10pm')
    
    # Parse settings format (e.g., "Mon-Fri: 9am-5pm, Sat-Sun: 10am-10pm")
    return parse_settings_hours(settings_hours)


def parse_settings_hours(settings_hours: str) -> Dict[str, str]:
    """
    Parse the RESTAURANT_HOURS setting string into a proper hours dictionary.
    
    Args:
        settings_hours (str): Settings string like "Mon-Fri: 9am-5pm, Sat-Sun: 10am-10pm"
        
    Returns:
        Dict[str, str]: Dictionary with full day names and time ranges
    """
    days_mapping = {
        'mon': 'Monday', 'tue': 'Tuesday', 'wed': 'Wednesday', 'thu': 'Thursday',
        'fri': 'Friday', 'sat': 'Saturday', 'sun': 'Sunday',
        'monday': 'Monday', 'tuesday': 'Tuesday', 'wednesday': 'Wednesday', 
        'thursday': 'Thursday', 'friday': 'Friday', 'saturday': 'Saturday', 'sunday': 'Sunday'
    }
    
    # Default all days to closed
    hours = {day: 'Closed' for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']}
    
    try:
        # Split by comma and process each part
        parts = settings_hours.split(',')
        
        for part in parts:
            part = part.strip()
            if ':' not in part:
                continue
                
            day_range, time_range = part.split(':', 1)
            day_range = day_range.strip().lower()
            time_range = time_range.strip()
            
            # Handle day ranges like "Mon-Fri" or individual days
            if '-' in day_range:
                start_day, end_day = day_range.split('-')
                start_day = start_day.strip()
                end_day = end_day.strip()
                
                # Map common abbreviations
                if start_day in days_mapping and end_day in days_mapping:
                    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    start_idx = day_names.index(days_mapping[start_day])
                    end_idx = day_names.index(days_mapping[end_day])
                    
                    for i in range(start_idx, end_idx + 1):
                        hours[day_names[i]] = time_range
            else:
                # Single day
                if day_range in days_mapping:
                    hours[days_mapping[day_range]] = time_range
    
    except Exception as e:
        logger.warning(f"Error parsing settings hours '{settings_hours}': {e}")
        # Return default business hours
        return {
            'Monday': '9am-5pm', 'Tuesday': '9am-5pm', 'Wednesday': '9am-5pm',
            'Thursday': '9am-5pm', 'Friday': '9am-5pm', 'Saturday': 'Closed', 'Sunday': 'Closed'
        }
    
    return hours


def is_restaurant_open(check_time: Optional[datetime] = None) -> bool:
    """
    Check if the restaurant is open at a specific time (or currently if no time specified).
    
    This function uses Python's datetime module to get the current day of the week
    and current time, then compares against the restaurant's defined opening hours.
    
    Opening hours are retrieved from:
    1. Restaurant model in database (preferred)
    2. RESTAURANT_HOURS setting in settings.py (fallback)
    3. Default business hours (final fallback)
    
    Args:
        check_time (datetime, optional): Time to check. Defaults to current time.
    
    Returns:
        bool: True if restaurant is open at specified time, False otherwise
        
    Example:
        >>> is_restaurant_open()
        True  # If called during business hours
        
        >>> is_restaurant_open(datetime(2023, 12, 25, 14, 30))
        False  # If called outside business hours or on closed days
        
    Integration:
        - Used by order system to validate orders during business hours
        - Can be used in templates to show "Open/Closed" status
        - API endpoints can check before processing orders
        - Marketing systems can schedule promotions during open hours
    """
    try:
        # Get date and time to check (current if not specified)
        check_datetime = check_time or datetime.now()
        current_day = check_datetime.strftime('%A')  # Full day name (e.g., 'Monday')
        current_time = check_datetime.time()
        
        # Get restaurant hours
        restaurant_hours = get_restaurant_hours()
        
        # Get today's hours
        today_hours = restaurant_hours.get(current_day, 'Closed')
        
        # Parse today's time range
        start_time, end_time = parse_time_range(today_hours)
        
        # If closed or couldn't parse times
        if start_time is None or end_time is None:
            logger.debug(f"Restaurant is closed on {current_day} (hours: {today_hours})")
            return False
        
        # Check if current time falls within opening hours
        is_open = start_time <= current_time <= end_time
        
        logger.debug(f"Restaurant status check - Day: {current_day}, Time: {current_time}, "
                    f"Hours: {today_hours}, Open: {is_open}")
        
        return is_open
        
    except Exception as e:
        logger.error(f"Error checking restaurant open status: {e}")
        # Safe fallback - assume closed on error
        return False


def get_restaurant_status(check_time: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Get comprehensive restaurant status information.
    
    Returns detailed information about current status, hours, and next opening time.
    
    Args:
        check_time (datetime, optional): Time to check status for. Defaults to current time.
    
    Returns:
        Dict[str, Any]: Dictionary containing:
            - is_open (bool): Whether restaurant is currently open
            - current_day (str): Current day name
            - current_time (str): Current time formatted
            - today_hours (str): Today's operating hours
            - next_opening (str): Next opening time if closed
            
    Example:
        {
            'is_open': True,
            'current_day': 'Monday',
            'current_time': '2:30 PM',
            'today_hours': '9am-5pm',
            'status_message': 'Open until 5:00 PM'
        }
    """
    try:
        check_datetime = check_time or datetime.now()
        current_day = check_datetime.strftime('%A')
        current_time_str = check_datetime.strftime('%I:%M %p')
        
        restaurant_hours = get_restaurant_hours()
        today_hours = restaurant_hours.get(current_day, 'Closed')
        is_open = is_restaurant_open(check_datetime)
        
        status = {
            'is_open': is_open,
            'current_day': current_day,
            'current_time': current_time_str,
            'today_hours': today_hours,
            'all_hours': restaurant_hours
        }
        
        # Add status message
        if is_open:
            start_time, end_time = parse_time_range(today_hours)
            if end_time:
                # Format time and remove leading zero from hour only (not from minutes)
                formatted_time = end_time.strftime('%I:%M %p')
                if formatted_time.startswith('0'):
                    formatted_time = formatted_time[1:]
                status['status_message'] = f"Open until {formatted_time}"
            else:
                status['status_message'] = "Currently open"
        else:
            status['status_message'] = f"Closed today ({today_hours})"
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting restaurant status: {e}")
        return {
            'is_open': False,
            'current_day': 'Unknown',
            'current_time': 'Unknown',
            'today_hours': 'Unknown',
            'status_message': 'Status unavailable',
            'error': str(e)
        }


def validate_email(email: Optional[str]) -> bool:
    """
    Validate an email address using regular expression matching.
    
    This function checks if an email address follows the standard email format:
    - Contains exactly one @ symbol
    - Has valid characters before and after @
    - Has a domain with at least one dot
    
    Args:
        email (Optional[str]): The email address to validate (can be None)
        
    Returns:
        bool: True if the email is valid, False otherwise
        
    Examples:
        >>> validate_email("user@example.com")
        True
        >>> validate_email("invalid.email")
        False
        >>> validate_email("user@domain")
        False
        >>> validate_email("")
        False
        
    Notes:
        - Uses a regex pattern that covers most common email formats
        - Handles edge cases like empty strings, None values
        - Case-insensitive validation
    """
    # Handle None or non-string inputs
    if not email or not isinstance(email, str):
        return False
    
    # Strip whitespace
    email = email.strip()
    
    # Check for empty string after stripping
    if not email:
        return False
    
    # Regular expression pattern for email validation
    # Pattern explanation:
    # ^[a-zA-Z0-9._%+-]+ : Start with alphanumeric chars and common email chars
    # @ : Must have exactly one @ symbol
    # [a-zA-Z0-9.-]+ : Domain name with alphanumeric, dots, hyphens
    # \. : Must have a dot in domain
    # [a-zA-Z]{2,}$ : Top-level domain (at least 2 letters)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Use re.match to validate the email format
    if re.match(pattern, email):
        # Additional check: email shouldn't be too long
        if len(email) <= 254:  # RFC 5321 limit
            return True
    
    return False


def calculate_discount(original_price, discount_percentage):
    """
    Calculate the discounted price for a menu item.
    
    This is a utility function for calculating discounts on individual menu items.
    Takes an original price and a discount percentage, then returns the final
    price after applying the discount.
    
    Args:
        original_price (float, int, or Decimal): The original price of the item.
            Must be a positive number (>= 0).
        discount_percentage (float, int, or Decimal): The discount percentage to apply.
            Must be between 0 and 100 (inclusive).
    
    Returns:
        Decimal: The discounted price, rounded to 2 decimal places.
            Returns the original price if discount is 0%.
    
    Raises:
        ValueError: If original_price is negative.
        ValueError: If discount_percentage is not between 0 and 100.
        TypeError: If inputs cannot be converted to numbers.
    
    Examples:
        >>> calculate_discount(100, 20)
        Decimal('80.00')
        
        >>> calculate_discount(10.50, 0)
        Decimal('10.50')
        
        >>> calculate_discount(50, 50)
        Decimal('25.00')
        
        >>> calculate_discount(99.99, 15)
        Decimal('84.99')
        
        >>> calculate_discount(-10, 20)
        ValueError: original_price must be non-negative
        
        >>> calculate_discount(100, -5)
        ValueError: discount_percentage must be between 0 and 100
        
        >>> calculate_discount(100, 150)
        ValueError: discount_percentage must be between 0 and 100
    """
    from decimal import Decimal, InvalidOperation
    
    # Input validation and type conversion
    try:
        # Convert inputs to Decimal for precise currency calculations
        original_price = Decimal(str(original_price))
        discount_percentage = Decimal(str(discount_percentage))
    except (InvalidOperation, ValueError, TypeError) as e:
        raise TypeError(
            f"Invalid input types: original_price and discount_percentage must be numeric. "
            f"Received: original_price={type(original_price).__name__}, "
            f"discount_percentage={type(discount_percentage).__name__}"
        ) from e
    
    # Validate original_price is non-negative
    if original_price < 0:
        raise ValueError(
            f"original_price must be non-negative. Received: {original_price}"
        )
    
    # Validate discount_percentage is between 0 and 100
    if discount_percentage < 0 or discount_percentage > 100:
        raise ValueError(
            f"discount_percentage must be between 0 and 100. Received: {discount_percentage}"
        )
    
    # If no discount, return original price
    if discount_percentage == 0:
        return original_price.quantize(Decimal('0.01'))
    
    # Calculate discount amount: original_price × (discount_percentage / 100)
    discount_amount = original_price * (discount_percentage / Decimal('100'))
    
    # Calculate final price: original_price - discount_amount
    discounted_price = original_price - discount_amount
    
    # Round to 2 decimal places for currency precision
    # Uses ROUND_HALF_EVEN (banker's rounding) by default
    return discounted_price.quantize(Decimal('0.01'))


# ================================
# PHONE NUMBER VALIDATION
# ================================

def validate_phone_number(phone_number: str) -> bool:
    """
    Validate if a string matches a basic valid phone number format.
    
    This function uses regular expressions to check if the input string represents
    a valid phone number. It supports common phone number formats including:
    - 10-digit US phone numbers (e.g., 5551234567)
    - Phone numbers with hyphens (e.g., 555-123-4567)
    - Phone numbers with spaces (e.g., 555 123 4567)
    - Phone numbers with parentheses (e.g., (555) 123-4567)
    - Phone numbers with country code prefix (e.g., +1-555-123-4567, +1 555 123 4567)
    - Phone numbers with dots (e.g., 555.123.4567)
    - International format (e.g., +44 20 7123 4567)
    
    Args:
        phone_number (str): The phone number string to validate
        
    Returns:
        bool: True if the phone number matches a valid format, False otherwise
    
    Examples:
        >>> from home.utils import validate_phone_number
        
        >>> # Valid US phone numbers (10 digits)
        >>> validate_phone_number("5551234567")
        True
        
        >>> validate_phone_number("555-123-4567")
        True
        
        >>> validate_phone_number("(555) 123-4567")
        True
        
        >>> validate_phone_number("555.123.4567")
        True
        
        >>> validate_phone_number("555 123 4567")
        True
        
        >>> # Valid with country code
        >>> validate_phone_number("+1-555-123-4567")
        True
        
        >>> validate_phone_number("+1 555 123 4567")
        True
        
        >>> validate_phone_number("+15551234567")
        True
        
        >>> # Valid international numbers (11-12 digits with country code)
        >>> validate_phone_number("+44 20 7123 4567")
        True
        
        >>> validate_phone_number("+33 1 42 86 82 00")
        True
        
        >>> # Invalid formats
        >>> validate_phone_number("123")  # Too short
        False
        
        >>> validate_phone_number("abcd1234567")  # Contains letters
        False
        
        >>> validate_phone_number("")  # Empty string
        False
        
        >>> validate_phone_number("555-123-456")  # Too few digits
        False
        
        >>> validate_phone_number("12345678901234")  # Too many digits
        False
    
    Notes:
        - Accepts 10-15 digits total
        - Allows optional '+' prefix for country codes
        - Allows common separators: hyphens, spaces, dots, parentheses
        - Strips whitespace before validation
        - Returns False for None, empty strings, or non-string inputs
        - Does not verify if the phone number actually exists or is in service
    
    Validation Rules:
        - Must contain 10-15 digits
        - Optional '+' at the start for country code
        - Allowed separators: space, hyphen, dot, parentheses
        - No letters or special characters (except allowed separators)
    """
    # Handle None or non-string inputs
    if not phone_number or not isinstance(phone_number, str):
        return False
    
    # Strip leading/trailing whitespace
    phone_number = phone_number.strip()
    
    # Check for empty string after stripping
    if not phone_number:
        return False
    
    # Regular expression pattern for phone number validation
    # This pattern matches strict US phone number format (3-3-4 digit pattern):
    # - Optional country code: +1, +44, etc. (1-3 digits after +)
    # - Optional area code in parentheses: (555) or just 555
    # - Main phone number with various separators (spaces, hyphens, dots)
    # - Exactly 10 digits in 3-3-4 format (or 11-13 with country code)
    
    phone_pattern = re.compile(
        r'^'                          # Start of string
        r'(\+\d{1,3}\s?)?'           # Optional country code: +1, +44, etc.
        r'(\(\d{3}\)|\d{3})'         # Area code: (555) or 555
        r'[\s\.-]?'                   # Optional separator
        r'\d{3}'                      # First 3 digits
        r'[\s\.-]?'                   # Optional separator
        r'\d{4}'                      # Last 4 digits
        r'$'                          # End of string
    )
    
    # Alternative pattern for international numbers with more flexibility
    # Matches 10-18 characters (including digits and separators like spaces, hyphens, dots)
    # Actual digit count (10-15 digits) is validated separately below
    international_pattern = re.compile(
        r'^'                          # Start of string
        r'\+?'                        # Optional + for country code
        r'[\d\s\.\-\(\)]{10,18}'     # 10-18 characters (digits + separators)
        r'$'                          # End of string
    )
    
    # First try the strict US phone number pattern
    if phone_pattern.match(phone_number):
        return True
    
    # Then try the international pattern
    if international_pattern.match(phone_number):
        # Count actual digits to ensure we have 10-15 digits
        digit_count = sum(1 for char in phone_number if char.isdigit())
        return 10 <= digit_count <= 15
    
    return False


# ================================
# RESTAURANT OPERATING HOURS
# ================================

def get_today_operating_hours():
    """
    Get the restaurant's operating hours for the current day of the week.
    
    This function determines today's day of the week and queries the
    DailyOperatingHours model to retrieve the corresponding opening
    and closing times. Useful for displaying current hours on the
    website or checking if the restaurant is open today.
    
    Returns:
        tuple: A tuple containing (open_time, close_time) if hours are found,
               or (None, None) if no hours exist for today or the restaurant
               is closed on the current day.
               
               - open_time (datetime.time or None): Opening time for today
               - close_time (datetime.time or None): Closing time for today
    
    Examples:
        >>> from home.utils import get_today_operating_hours
        >>> from datetime import time
        
        >>> # If today is Monday and hours are 9am-5pm
        >>> open_time, close_time = get_today_operating_hours()
        >>> print(f"Open: {open_time}, Close: {close_time}")
        Open: 09:00:00, Close: 17:00:00
        
        >>> # If today is Sunday and the restaurant is closed
        >>> open_time, close_time = get_today_operating_hours()
        >>> print(f"Open: {open_time}, Close: {close_time}")
        Open: None, Close: None
        
        >>> # Check if restaurant is open today
        >>> open_time, close_time = get_today_operating_hours()
        >>> if open_time and close_time:
        ...     print(f"We're open from {open_time} to {close_time}!")
        ... else:
        ...     print("Sorry, we're closed today.")
        
        >>> # Use in a view to display hours
        >>> open_time, close_time = get_today_operating_hours()
        >>> if open_time:
        ...     hours_str = f"{open_time.strftime('%I:%M %p')} - {close_time.strftime('%I:%M %p')}"
        ...     context = {'todays_hours': hours_str}
    
    Notes:
        - Uses Python's datetime.datetime.now().weekday() to determine the current day
        - Monday is 0, Sunday is 6 (following Python's datetime convention)
        - Returns (None, None) if no DailyOperatingHours entry exists for today
        - Returns (None, None) if the restaurant is marked as closed (is_closed=True)
        - The times returned are datetime.time objects, not strings
        - This function queries the database each time it's called
    
    Database Requirements:
        - Requires DailyOperatingHours model with the following fields:
          * day_of_week (IntegerField): 0-6 representing Monday-Sunday
          * open_time (TimeField): Opening time
          * close_time (TimeField): Closing time
          * is_closed (BooleanField): Whether closed on this day
    
    Raises:
        No exceptions are raised. If the model doesn't exist or the query
        fails, the function returns (None, None) and logs the error.
    """
    try:
        # Get the current day of the week (0 = Monday, 6 = Sunday)
        today = datetime.now().weekday()
        
        # Import the model here to avoid circular imports
        from .models import DailyOperatingHours
        
        # Query the DailyOperatingHours model for today's entry
        operating_hours = DailyOperatingHours.objects.filter(
            day_of_week=today
        ).first()
        
        # If no entry found or restaurant is closed today, return (None, None)
        if not operating_hours or operating_hours.is_closed:
            return (None, None)
        
        # Return the open and close times as a tuple
        return (operating_hours.open_time, operating_hours.close_time)
    
    except ImportError as e:
        # Model doesn't exist or can't be imported
        logger.error(f"Failed to import DailyOperatingHours model: {e}")
        return (None, None)
    except Exception as e:
        # Database errors, query failures, or other unexpected issues
        logger.error(f"Error retrieving today's operating hours: {e}", exc_info=True)
        return (None, None)


def get_distinct_cuisines():
    """
    Get a list of unique cuisine/category names from menu items.
    
    Note: This project uses MenuCategory, not a Cuisine model.
    Returns distinct category names from all menu items.
    
    Returns:
        list: List of unique category name strings
        
    Example:
        >>> get_distinct_cuisines()
        ['Appetizers', 'Main Course', 'Desserts', 'Beverages']
    """
    from .models import MenuItem
    
    cuisines = list(
        MenuItem.objects
        .exclude(category__isnull=True)
        .values_list('category__name', flat=True)
        .distinct()
        .order_by('category__name')
    )
    
    return cuisines


def calculate_average_rating(reviews_queryset) -> float:
    """
    Calculate the average rating from a queryset of reviews.
    
    This utility function computes the mean rating value from a collection
    of restaurant reviews. It handles edge cases such as empty querysets
    and ensures robust error handling.
    
    Args:
        reviews_queryset: A Django queryset of UserReview objects.
                         Expected to have a 'rating' field (IntegerField 1-5).
    
    Returns:
        float: The average rating rounded to 2 decimal places.
               Returns 0.0 if the queryset is empty or has no valid ratings.
    
    Edge Cases:
        - Empty queryset: Returns 0.0
        - No reviews: Returns 0.0
        - Single review: Returns that review's rating as a float
        - Multiple reviews: Returns the arithmetic mean
    
    Example:
        >>> from home.models import UserReview
        >>> reviews = UserReview.objects.filter(menu_item_id=1)
        >>> avg_rating = calculate_average_rating(reviews)
        >>> print(f"Average rating: {avg_rating}")
        Average rating: 4.33
        
        >>> empty_reviews = UserReview.objects.none()
        >>> calculate_average_rating(empty_reviews)
        0.0
    
    Notes:
        - This function is queryset-agnostic and can work with any filtered
          subset of reviews (by menu item, user, date range, etc.)
        - Uses Python's built-in sum/len for simplicity and clarity
        - Rounds to 2 decimal places for consistent display formatting
    """
    try:
        # Count the number of reviews
        review_count = reviews_queryset.count()
        
        # Handle empty queryset
        if review_count == 0:
            return 0.0
        
        # Calculate sum of all ratings
        total_rating = sum(review.rating for review in reviews_queryset)
        
        # Calculate and return average (rounded to 2 decimal places)
        average = total_rating / review_count
        return round(average, 2)
    
    except (TypeError, AttributeError, ZeroDivisionError) as e:
        # Log the error for debugging purposes
        logger.error(f"Error calculating average rating: {str(e)}")
        return 0.0
    except Exception as e:
        # Catch any unexpected errors
        logger.error(f"Unexpected error in calculate_average_rating: {str(e)}")
        return 0.0
