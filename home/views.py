
# Import the render function to display templates
from django.shortcuts import render

# This view renders the homepage using our new styled template
def home_view(request):
	# 'request' is the HTTP request object
	# 'home/index.html' is the path to our template
	# The third argument (context) is optional and can be used to pass data to the template
def home_view(request):
    """
    Render the homepage using the 'home/index.html' template.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: The rendered homepage.
    """
	# 'request' is the HTTP request object
	# 'home/index.html' is the path to our template
	# The third argument (context) is optional and can be used to pass data to the template
def home_view(request):
    # 'request' is the HTTP request object
    # 'home/index.html' is the path to our template
    # The third argument (context) is optional and can be used to pass data to the template
    return render(request, 'home/index.html')


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
