from django.urls import path
from .views import home_view, about_view, contact_view, menu_view, restaurant_list_create, restaurant_detail

# URL patterns define which view is called for each URL
urlpatterns = [
    # '' means the root of this app; home_view will handle it
    path('', home_view, name='home'),
    # 'about/' for the about page
    path('about/', about_view, name='about'),
    # 'contact/' for the contact page
    path('contact/', contact_view, name='contact'),
    # 'menu/' for the menu page
    path('menu/', menu_view, name='menu'),
    # API endpoints for restaurant CRUD
    path('api/restaurants/', restaurant_list_create, name='restaurant-list-create'),
    path('api/restaurants/<int:pk>/', restaurant_detail, name='restaurant-detail'),
]