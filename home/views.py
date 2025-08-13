

# Import the render function to display templates
from django.shortcuts import render
# Import settings to access RESTAURANT_NAME
from django.conf import settings

# This view renders the homepage using our new styled template

def home_view(request):
	"""
	View to render the homepage with the restaurant's name from settings.
	Args:
		request: The HTTP request object.
	Returns:
		HttpResponse: Rendered homepage with restaurant name in context.
	"""
	context = {
		'restaurant_name': getattr(settings, 'RESTAURANT_NAME', 'Our Restaurant')
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
