from django.urls import path
from .views import CustomerOrderListView, CreateOrderView, CustomerListCreateAPIView, UserOrderHistoryView

urlpatterns = [
	path('orders/', CustomerOrderListView.as_view(), name='customer-order-list'),
	path('orders/create/', CreateOrderView.as_view(), name='order-create'),
	path('orders/history/', UserOrderHistoryView.as_view(), name='user-order-history'),
	path('customers/', CustomerListCreateAPIView.as_view(), name='customer-list-create'),
]