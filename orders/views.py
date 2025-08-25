
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from .models import Order, Customer
from .serializers import OrderSerializer, CustomerSerializer

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


# API view to create orders, auto-creating Customer for guests
from rest_framework import status
from rest_framework.views import APIView

class OrderCreateView(APIView):
	permission_classes = [permissions.AllowAny]

	def post(self, request, *args, **kwargs):
		data = request.data.copy()
		customer_data = data.pop('customer', None)

		customer = None
		if request.user.is_authenticated:
			# If you later link Order to User, associate here
			pass  # Placeholder for user linkage
		elif customer_data:
			# Validate and create Customer for guest
			serializer = CustomerSerializer(data=customer_data)
			serializer.is_valid(raise_exception=True)
			customer = serializer.save()

		order_data = {
			'customer': customer.id if customer else None,
			'total_amount': data.get('total_price'),
			'status': data.get('status', 'pending'),
		}
		order_serializer = OrderSerializer(data=order_data)
		order_serializer.is_valid(raise_exception=True)
		order = order_serializer.save()

		response_data = {
			'order_id': order.id,
			'status': 'success',
			'customer': CustomerSerializer(customer).data if customer else None,
		}
		return Response(response_data, status=status.HTTP_201_CREATED)


# API view to list and create customers
class CustomerListCreateAPIView(APIView):
	permission_classes = [permissions.AllowAny]

	def get(self, request, *args, **kwargs):
		customers = Customer.objects.all().order_by('-created_at')
		serializer = CustomerSerializer(customers, many=True)
		return Response(serializer.data)

	def post(self, request, *args, **kwargs):
		serializer = CustomerSerializer(data=request.data)
		# Allow partial/empty data for guest/quick entry
		serializer.is_valid(raise_exception=True)
		customer = serializer.save()
		return Response(CustomerSerializer(customer).data, status=status.HTTP_201_CREATED)
