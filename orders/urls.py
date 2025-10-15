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
    DriverRegistrationView,
    OrderCancellationView,
    CouponValidationView,
    RideRequestView,
    AvailableRidesView,
    AcceptRideView,
    UpdateLocationView,
    TrackRideView,
    CompleteRideView,
    CancelRideView,
    RiderHistoryView,
    DriverHistoryView,
    UpdateOrderStatusView,
    # Task 10B & 11B: Fare calculation and payment views
    calculate_fare,
    mark_ride_as_paid
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
    path('orders/<str:order_id>/cancel/', OrderCancellationView.as_view(), name='order-cancel'),
    path('orders/<int:order_id>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/update-status/', UpdateOrderStatusView.as_view(), name='order-update-status'),
    path('customers/', CustomerListCreateAPIView.as_view(), name='customer-list-create'),
    
    # Coupon validation endpoint
    path('coupons/validate/', CouponValidationView.as_view(), name='coupon-validate'),
    
    # Registration endpoints
    path('register/rider/', RiderRegistrationView.as_view(), name='rider-registration'),
    path('register/driver/', DriverRegistrationView.as_view(), name='driver-registration'),
    
    # Ride booking endpoints (Rider → Driver workflow)
    path('ride/request/', RideRequestView.as_view(), name='ride-request'),
    path('ride/available/', AvailableRidesView.as_view(), name='available-rides'),
    path('ride/accept/<int:ride_id>/', AcceptRideView.as_view(), name='accept-ride'),
    
    # Task 6: Real-time location tracking
    path('ride/update-location/', UpdateLocationView.as_view(), name='update-location'),
    path('ride/track/<int:ride_id>/', TrackRideView.as_view(), name='track-ride'),
    
    # Task 7: Complete & cancel rides
    path('ride/complete/<int:ride_id>/', CompleteRideView.as_view(), name='complete-ride'),
    path('ride/cancel/<int:ride_id>/', CancelRideView.as_view(), name='cancel-ride'),
    
    # Task 8: Ride history with pagination
    path('rider/history/', RiderHistoryView.as_view(), name='rider-history'),
    path('driver/history/', DriverHistoryView.as_view(), name='driver-history'),
    
    # Task 10B: Calculate and store ride fare
    path('ride/calculate-fare/<int:ride_id>/', calculate_fare, name='calculate-fare'),
    
    # Task 11B: Mark ride as paid
    path('ride/payment/<int:ride_id>/', mark_ride_as_paid, name='mark-ride-paid'),
    
    # JWT Authentication endpoints (custom views with enhanced features)
    path('auth/login/', jwt_login, name='jwt-login'),
    path('auth/logout/', jwt_logout, name='jwt-logout'),
    path('auth/profile/', jwt_user_profile, name='jwt-user-profile'),
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='custom-token-obtain'),
    path('auth/token/refresh/', CustomTokenRefreshView.as_view(), name='custom-token-refresh'),
    
    # Include router URLs for profile management
    path('', include(router.urls)),
]