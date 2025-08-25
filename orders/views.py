
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from .models import Order, Customer
from .serializers import OrderSerializer

class CustomerOrderListView(generics.ListAPIView):
	serializer_class = OrderSerializer
	permission_classes = [permissions.AllowAny]

	def get_queryset(self):
		customer_id = self.request.query_params.get('customer_id')
		user = self.request.user if self.request.user.is_authenticated else None

		if customer_id:
			# Filter by customer_id (guest or admin lookup)
			return Order.objects.filter(customer_id=customer_id)
		elif user:
			# If you later link Order to User, filter by user here
			# For now, return empty queryset for authenticated users (no User FK yet)
			return Order.objects.none()
		else:
			return Order.objects.none()
