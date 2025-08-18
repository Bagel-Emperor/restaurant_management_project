from django.urls import path
from .views import (
    home_view, about_view, contact_view, menu_view,
    create_restaurant, list_restaurants, get_restaurant, update_restaurant, delete_restaurant,
    create_menu_item, list_menu_items, get_menu_item, update_menu_item, delete_menu_item
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

    # API endpoints for menu item CRUD (one per method)
    path('api/menu-items/', list_menu_items, name='menuitem-list'),
    path('api/menu-items/create/', create_menu_item, name='menuitem-create'),
    path('api/menu-items/<int:pk>/', get_menu_item, name='menuitem-detail'),
    path('api/menu-items/<int:pk>/update/', update_menu_item, name='menuitem-update'),
    path('api/menu-items/<int:pk>/delete/', delete_menu_item, name='menuitem-delete'),
]