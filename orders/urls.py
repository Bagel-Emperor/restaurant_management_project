from django.urls import path
from .views import CustomerOrderListView, OrderCreateView, CustomerListCreateAPIView

urlpatterns = [
	path('orders/', CustomerOrderListView.as_view(), name='customer-order-list'),
	path('orders/create/', OrderCreateView.as_view(), name='order-create'),
	path('customers/', CustomerListCreateAPIView.as_view(), name='customer-list-create'),
]