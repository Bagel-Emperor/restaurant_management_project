
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from django.contrib.auth.models import User
from .models import Order, Customer
from .serializers import OrderSerializer, CustomerSerializer, OrderHistorySerializer

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
			# Filter by authenticated user
			return Order.objects.filter(user=user)
		else:
			return Order.objects.none()



class CreateOrderView(APIView):
	permission_classes = [permissions.AllowAny]

	def post(self, request, *args, **kwargs):
		data = request.data.copy()
		customer_data = data.pop('customer', None)

		customer = None
		user = None
		if request.user.is_authenticated:
			# Link order to authenticated user
			user = request.user
		elif customer_data:
			serializer = CustomerSerializer(data=customer_data)
			serializer.is_valid(raise_exception=True)
			customer = serializer.save()

		total_price = data.get('total_price')
		if total_price is None:
			return Response({'error': 'total_price is required.'}, status=status.HTTP_400_BAD_REQUEST)

		order_data = {
			'user': user.id if user else None,
			'customer': customer.id if customer else None,
			'total_amount': total_price,
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


class UserOrderHistoryView(generics.ListAPIView):
	"""
	API endpoint for authenticated users to retrieve their order history.
	Returns orders with order items, status, and comprehensive details.
	"""
	serializer_class = OrderHistorySerializer
	permission_classes = [permissions.IsAuthenticated]
	authentication_classes = [SessionAuthentication, TokenAuthentication]

	def get_queryset(self):
		"""Return orders for the authenticated user, ordered by most recent first"""
		user = self.request.user
		return Order.objects.filter(user=user).select_related('status').prefetch_related(
			'order_items__menu_item'
		).order_by('-created_at')

	def list(self, request, *args, **kwargs):
		"""Override list to add additional metadata"""
		queryset = self.get_queryset()
		serializer = self.get_serializer(queryset, many=True)
		
		return Response({
			'count': queryset.count(),
			'orders': serializer.data
		})
