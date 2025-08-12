
# Import the render function to display templates
from django.shortcuts import render

# This view renders the homepage using our new styled template
def home_view(request):
	# 'request' is the HTTP request object
	# 'home/index.html' is the path to our template
	# The third argument (context) is optional and can be used to pass data to the template
	return render(request, 'home/index.html')
