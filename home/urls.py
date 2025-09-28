from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    home_view, about_view, contact_view, menu_view, reservations_view, feedback_view, faq_view,
    create_restaurant, list_restaurants, get_restaurant, update_restaurant, delete_restaurant,
    create_menu_item, list_menu_items, get_menu_item, update_menu_item, delete_menu_item,
    MenuCategoryListAPIView, MenuItemViewSet,
    # Cart API views
    cart_summary, add_to_cart_api, remove_from_cart_api, update_cart_item_api, clear_cart_api,
    # Contact form API view
    ContactSubmissionCreateAPIView
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'menu-items', MenuItemViewSet, basename='menuitem')

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
    # 'reservations/' for the reservations page
    path('reservations/', reservations_view, name='reservations'),
    # 'feedback/' for the feedback page
    path('feedback/', feedback_view, name='feedback'),
    # 'faq/' for the FAQ page
    path('faq/', faq_view, name='faq'),
    # API endpoints for restaurant CRUD (one per method)
    path('api/restaurants/', list_restaurants, name='restaurant-list'),
    path('api/restaurants/create/', create_restaurant, name='restaurant-create'),
    path('api/restaurants/', list_restaurants, name='restaurant-list'),
    # Removed 'api/restaurants/create/' to follow REST conventions; POST to 'api/restaurants/' now creates a restaurant
    path('api/restaurants/<int:pk>/', get_restaurant, name='restaurant-detail'),
    path('api/restaurants/<int:pk>/update/', update_restaurant, name='restaurant-update'),
    path('api/restaurants/<int:pk>/delete/', delete_restaurant, name='restaurant-delete'),

    # API endpoint for menu categories
    path('api/menu-categories/', MenuCategoryListAPIView.as_view(), name='menu-category-list'),

    # API endpoints for menu items using ViewSet (replaces individual CRUD endpoints)
    path('api/', include(router.urls)),
    
    # Legacy individual menu item endpoints (keeping for backward compatibility)
    path('api/menu-items/legacy/', list_menu_items, name='menuitem-legacy-list'),
    path('api/menu-items/legacy/create/', create_menu_item, name='menuitem-legacy-create'),
    path('api/menu-items/legacy/<int:pk>/', get_menu_item, name='menuitem-legacy-detail'),
    path('api/menu-items/legacy/<int:pk>/update/', update_menu_item, name='menuitem-legacy-update'),
    path('api/menu-items/legacy/<int:pk>/delete/', delete_menu_item, name='menuitem-legacy-delete'),
    
    # Shopping Cart API endpoints
    path('api/cart/', cart_summary, name='cart-summary'),
    path('api/cart/add/', add_to_cart_api, name='add-to-cart'),
    path('api/cart/remove/<int:menu_item_id>/', remove_from_cart_api, name='remove-from-cart'),
    path('api/cart/update/<int:menu_item_id>/', update_cart_item_api, name='update-cart-item'),
    path('api/cart/clear/', clear_cart_api, name='clear-cart'),
    
    # Contact Form API endpoint
    path('api/contact/', ContactSubmissionCreateAPIView.as_view(), name='contact-api'),
]