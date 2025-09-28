from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomerOrderListView, 
    CreateOrderView, 
    CustomerListCreateAPIView, 
    UserOrderHistoryView,
    OrderDetailView,
    UserProfileViewSet,
    RiderRegistrationView,
    DriverRegistrationView
)
from .jwt_views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    jwt_login,
    jwt_logout,
    jwt_user_profile
)

# Create a router for viewsets
router = DefaultRouter()
router.register(r'profile', UserProfileViewSet, basename='userprofile')

urlpatterns = [
    path('orders/', CustomerOrderListView.as_view(), name='customer-order-list'),
    path('orders/create/', CreateOrderView.as_view(), name='order-create'),
    path('orders/history/', UserOrderHistoryView.as_view(), name='user-order-history'),
    path('orders/<int:order_id>/', OrderDetailView.as_view(), name='order-detail'),
    path('customers/', CustomerListCreateAPIView.as_view(), name='customer-list-create'),
    
    # Registration endpoints
    path('register/rider/', RiderRegistrationView.as_view(), name='rider-registration'),
    path('register/driver/', DriverRegistrationView.as_view(), name='driver-registration'),
    
    # JWT Authentication endpoints (custom views with enhanced features)
    path('auth/login/', jwt_login, name='jwt-login'),
    path('auth/logout/', jwt_logout, name='jwt-logout'),
    path('auth/profile/', jwt_user_profile, name='jwt-user-profile'),
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='custom-token-obtain'),
    path('auth/token/refresh/', CustomTokenRefreshView.as_view(), name='custom-token-refresh'),
    
    # Include router URLs for profile management
    path('', include(router.urls)),
]