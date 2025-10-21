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


def validate_email(email: str) -> bool:
    """
    Validate an email address using regular expression matching.
    
    This function checks if an email address follows the standard email format:
    - Contains exactly one @ symbol
    - Has valid characters before and after @
    - Has a domain with at least one dot
    
    Args:
        email (str): The email address to validate
        
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