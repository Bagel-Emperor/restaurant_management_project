from datetime import datetime
from django.conf import settings
from home.models import Restaurant, RestaurantLocation

def current_year(request):
    # Try to get the first restaurant and its location
    restaurant = Restaurant.objects.first()
    location = getattr(restaurant, 'location', None) if restaurant else None
    if location:
        address = f"{location.address}, {location.city}, {location.state} {location.zip_code}"
    else:
        address = getattr(settings, 'RESTAURANT_ADDRESS', '123 Main St, Springfield, USA')
    return {
        'current_year': datetime.now().year,
        'restaurant_hours': getattr(settings, 'RESTAURANT_HOURS', 'Mon-Fri: 11am-9pm, Sat-Sun: 10am-10pm'),
        'restaurant_name': getattr(settings, 'RESTAURANT_NAME', 'Perpex Bistro'),
        'restaurant_address': address,
    }
