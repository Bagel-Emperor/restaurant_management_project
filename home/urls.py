from django.urls import path
from .views import (
    home_view, about_view, contact_view, menu_view,
    create_restaurant, list_restaurants, get_restaurant, update_restaurant, delete_restaurant
)

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
    # API endpoints for restaurant CRUD (one per method)
    path('api/restaurants/', list_restaurants, name='restaurant-list'),
    path('api/restaurants/create/', create_restaurant, name='restaurant-create'),
    path('api/restaurants/<int:pk>/', get_restaurant, name='restaurant-detail'),
    path('api/restaurants/<int:pk>/update/', update_restaurant, name='restaurant-update'),
    path('api/restaurants/<int:pk>/delete/', delete_restaurant, name='restaurant-delete'),
]