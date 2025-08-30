from datetime import datetime
from django.conf import settings

from home.models import Restaurant, RestaurantLocation

def format_opening_hours(hours_dict):
    # Standard order for days of the week
    days_order = [
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    ]
    if not isinstance(hours_dict, dict):
        return str(hours_dict)
    return ", ".join(f"{day}: {hours_dict.get(day, 'Closed')}" for day in days_order)

def current_year(request):
    # Try to get the first restaurant and its location
    restaurant = Restaurant.objects.first()
    location = getattr(restaurant, 'location', None) if restaurant else None
    if location:
        address = f"{location.address}, {location.city}, {location.state} {location.zip_code}"
    else:
        address = getattr(settings, 'RESTAURANT_ADDRESS', '123 Main St, Springfield, USA')
    # Get opening hours from the Restaurant model if available
    if restaurant and restaurant.opening_hours:
        hours_str = format_opening_hours(restaurant.opening_hours)
    else:
        hours_str = getattr(settings, 'RESTAURANT_HOURS', 'Mon-Fri: 11am-9pm, Sat-Sun: 10am-10pm')
    return {
        'current_year': datetime.now().year,
        'restaurant_hours': hours_str,
        'restaurant_name': getattr(settings, 'RESTAURANT_NAME', 'Perpex Bistro'),
        'restaurant_address': address,
    }
