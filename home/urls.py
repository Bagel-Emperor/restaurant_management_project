from django.urls import path
from .views import home_view, about_view, contact_view

# URL patterns define which view is called for each URL
urlpatterns = [
    # '' means the root of this app; home_view will handle it
    path('', home_view, name='home'),
    # 'about/' for the about page
    path('about/', about_view, name='about'),
    # 'contact/' for the contact page
    path('contact/', contact_view, name='contact'),
]