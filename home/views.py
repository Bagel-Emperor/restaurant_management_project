
# Import the render function to display templates
from django.shortcuts import render
# Import settings to access RESTAURANT_NAME
from django.conf import settings

# Menu page view
def menu_view(request):
    """
    View to render the menu page with a hardcoded list of menu items.
    Args:
        request: The HTTP request object.
    Returns:
        HttpResponse: Rendered menu page with menu items in context.
    """
    menu_items = [
        {'name': 'Margherita Pizza', 'price': '12.99'},
        {'name': 'Caesar Salad', 'price': '8.99'},
        {'name': 'Grilled Salmon', 'price': '16.99'},
        {'name': 'Spaghetti Carbonara', 'price': '13.99'},
        {'name': 'Chocolate Lava Cake', 'price': '6.99'},
    ]
    context = {
        'menu_items': menu_items,
    }
    return render(request, 'home/menu.html', context)

# This view renders the homepage using our new styled template

def home_view(request):
    """
    View to render the homepage with the restaurant's name and phone number from settings.
    Args:
        request: The HTTP request object.
    Returns:
        HttpResponse: Rendered homepage with restaurant name and phone in context.
    """
    context = {
        'restaurant_name': getattr(settings, 'RESTAURANT_NAME', 'Our Restaurant'),
        'restaurant_phone': getattr(settings, 'RESTAURANT_PHONE', ''),
    }
    return render(request, 'home/index.html', context)

# Custom 404 error handler view
def custom_404_view(request, exception):
	"""
	Custom view to render the 404 error page using the 404.html template.
	Args:
		request: The HTTP request object.
		exception: The exception that triggered the 404.
	Returns:
		HttpResponse: Rendered 404 error page.
	"""
	return render(request, 'home/404.html', status=404)
    
    
# About page view
def about_view(request):
    """
    View to render the about page for the restaurant.
    Args:
        request: The HTTP request object.
    Returns:
        HttpResponse: Rendered about page.
    """
    context = {
        'restaurant_name': getattr(settings, 'RESTAURANT_NAME', 'Our Restaurant'),
        'restaurant_description': (
            'Perpex Bistro is a modern restaurant dedicated to providing a delightful dining experience. '
            'Our menu features a blend of classic and contemporary dishes, crafted with fresh, local ingredients. '
            'Whether you\'re here for a quick lunch or a special dinner, we strive to make every visit memorable.'
        ),
    }
    return render(request, 'home/about.html', context)

# Contact page view

def contact_view(request):
    """
    View to render the contact page for the restaurant.
    Args:
        request: The HTTP request object.
    Returns:
        HttpResponse: Rendered contact page.
    """
    context = {
        'restaurant_name': getattr(settings, 'RESTAURANT_NAME', 'Our Restaurant'),
        'contact_email': 'contact@perpexbistro.com',
        'contact_phone': '(555) 123-4567',
        'contact_email': 'contact@perpexbistro.com',
        'contact_phone': getattr(settings, 'RESTAURANT_PHONE', '(555) 123-4567'),
        'contact_address': '123 Main Street, Cityville, USA',
    }
    return render(request, 'home/contact.html', context)
