from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomerOrderListView, 
    CreateOrderView, 
    CustomerListCreateAPIView, 
    UserOrderHistoryView,
    OrderDetailView,
    UserProfileViewSet
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
    
    # Include router URLs for profile management
    path('', include(router.urls)),
]