from django.urls import path
# Import the home_view we just created
from .views import home_view

# URL patterns define which view is called for each URL
urlpatterns = [
	# '' means the root of this app; home_view will handle it
	path('', home_view, name='home'),
]