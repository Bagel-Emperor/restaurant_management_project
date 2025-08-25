from django.urls import path
from .views import CustomerOrderListView

urlpatterns = [
	path('orders/', CustomerOrderListView.as_view(), name='customer-order-list'),
]