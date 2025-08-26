from datetime import datetime
from django.conf import settings

def current_year(request):
    return {
        'current_year': datetime.now().year,
        'restaurant_hours': getattr(settings, 'RESTAURANT_HOURS', 'Mon-Fri: 11am-9pm, Sat-Sun: 10am-10pm'),
        'restaurant_name': getattr(settings, 'RESTAURANT_NAME', 'Perpex Bistro'),
        'restaurant_address': getattr(settings, 'RESTAURANT_ADDRESS', '123 Main St, Springfield, USA'),
    }
