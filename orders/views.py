
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Order, Customer, UserProfile, OrderStatus
from .serializers import OrderSerializer, CustomerSerializer, OrderHistorySerializer, UserProfileSerializer, OrderDetailSerializer
from .choices import OrderStatusChoices

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
			'order_id': order.order_id,  # Use user-friendly order ID
			'database_id': order.id,     # Include database ID for internal use
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
			'count': len(serializer.data),
			'orders': serializer.data
		})


class OrderDetailView(generics.RetrieveAPIView):
	"""
	API endpoint to retrieve detailed information about a specific order by ID.
	
	Features:
	- Retrieves comprehensive order details including items, customer info, and status
	- Requires authentication for all order access
	- Authenticated users can only access their own orders (superusers can access any)
	- Returns detailed error messages for non-existent or unauthorized orders
	"""
	serializer_class = OrderDetailSerializer
	permission_classes = [permissions.IsAuthenticated]
	authentication_classes = [SessionAuthentication, TokenAuthentication]
	lookup_field = 'id'
	lookup_url_kwarg = 'order_id'
	
	def get_queryset(self):
		"""
		Optimize queryset with select_related and prefetch_related for performance.
		Using separate select_related calls to handle nullable relationships safely.
		"""
		return Order.objects.select_related('status').select_related('customer').select_related('user').prefetch_related(
			'order_items__menu_item'
		)
	
	def get_object(self):
		"""
		Retrieve order with proper authorization checks.
		
		Authorization logic:
		1. Authentication is required for all order access
		2. Authenticated users can only access their own orders
		3. Superusers can access any order
		"""
		queryset = self.get_queryset()
		order_id = self.kwargs.get(self.lookup_url_kwarg)
		
		try:
			order = queryset.get(id=order_id)
		except Order.DoesNotExist:
			raise NotFound(f"Order with ID {order_id} not found.")
		
		# Permission checking
		user = self.request.user
		
		# Require authentication for all order access
		if not user.is_authenticated:
			raise PermissionDenied("Authentication required to view order details.")
		
		# Superusers can access any order
		if user.is_superuser:
			return order
		
		# Authenticated users can only access their own orders
		if order.user == user:
			return order
		
		# If order belongs to a different user or is a guest order, deny access
		raise PermissionDenied("You do not have permission to view this order.")
	
	def retrieve(self, request, *args, **kwargs):
		"""
		Override retrieve to add additional metadata and error handling
		"""
		try:
			instance = self.get_object()
			serializer = self.get_serializer(instance)
			
			return Response({
				'success': True,
				'order': serializer.data,
				'message': f'Order {instance.id} retrieved successfully'
			})
			
		except NotFound as e:
			return Response({
				'success': False,
				'error': str(e),
				'order': None
			}, status=status.HTTP_404_NOT_FOUND)
			
		except PermissionDenied as e:
			return Response({
				'success': False,
				'error': str(e),
				'order': None
			}, status=status.HTTP_403_FORBIDDEN)
		
		except Exception as e:
			return Response({
				'success': False,
				'error': 'An unexpected error occurred while retrieving the order.',
				'order': None
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserProfileViewSet(viewsets.ModelViewSet):
	"""
	ViewSet for managing user profiles.
	Supports retrieving and updating user profile information.
	Only authenticated users can access their own profile.
	
	Note: This ViewSet always operates on the authenticated user's profile,
	regardless of the pk parameter in URLs for security reasons.
	"""
	serializer_class = UserProfileSerializer
	permission_classes = [permissions.IsAuthenticated]
	authentication_classes = [SessionAuthentication, TokenAuthentication]
	http_method_names = ['get', 'put', 'patch', 'options', 'head']  # No DELETE, no POST (profiles are created automatically)
	
	def get_object(self):
		"""
		Get or create the user profile for the authenticated user.
		This ensures every user has a profile.
		
		Note: For security, this always returns the authenticated user's profile
		regardless of the pk parameter in the URL.
		"""
		user = self.request.user
		profile, created = UserProfile.objects.get_or_create(user=user)
		
		# Check object permissions
		self.check_object_permissions(self.request, profile)
		return profile
	
	def check_object_permissions(self, request, obj):
		"""
		Ensure users can only access their own profile.
		"""
		super().check_object_permissions(request, obj)
		if obj.user != request.user:
			raise PermissionDenied("You can only access your own profile.")
	
	def list(self, request, *args, **kwargs):
		"""
		Override list to return the user's own profile instead of a list.
		This provides a convenient endpoint for getting the current user's profile.
		"""
		profile = self.get_object()
		serializer = self.get_serializer(profile)
		return Response(serializer.data)
	
	def retrieve(self, request, *args, **kwargs):
		"""
		Retrieve the authenticated user's profile.
		
		Security Note: The pk parameter is ignored for security reasons.
		This always returns the authenticated user's profile to prevent
		users from accessing other users' profiles.
		"""
		profile = self.get_object()
		serializer = self.get_serializer(profile)
		return Response(serializer.data)
	
	def update(self, request, *args, **kwargs):
		"""
		Update the user's profile (PUT request).
		"""
		partial = kwargs.pop('partial', False)
		profile = self.get_object()
		serializer = self.get_serializer(profile, data=request.data, partial=partial)
		serializer.is_valid(raise_exception=True)
		self.perform_update(serializer)
		
		return Response(serializer.data)
	
	def partial_update(self, request, *args, **kwargs):
		"""
		Partially update the user's profile (PATCH request).
		"""
		kwargs['partial'] = True
		return self.update(request, *args, **kwargs)
	
	@action(detail=False, methods=['get'])
	def me(self, request):
		"""
		Convenience endpoint to get current user's profile at /api/profile/me/
		"""
		profile = self.get_object()
		serializer = self.get_serializer(profile)
		return Response(serializer.data)


# ================================
# REGISTRATION API VIEWS
# ================================

class RiderRegistrationView(APIView):
	"""
	API endpoint for rider registration.
	
	Creates a new User account and associated Rider profile with comprehensive
	validation. Handles password hashing, email verification, and profile creation.
	
	POST /api/register/rider/
	"""
	permission_classes = [permissions.AllowAny]  # Public registration
	
	def post(self, request, *args, **kwargs):
		"""
		Register a new rider.
		
		Expected JSON format:
		{
			"username": "john_rider",
			"email": "john@example.com",
			"password": "securepassword123",
			"first_name": "John",
			"last_name": "Doe",
			"phone": "+1234567890",
			"preferred_payment": "card",
			"default_pickup_address": "123 Main St, City",
			"default_pickup_latitude": 40.7128,
			"default_pickup_longitude": -74.0060
		}
		"""
		from .serializers import RiderRegistrationSerializer
		
		try:
			serializer = RiderRegistrationSerializer(data=request.data)
			
			if serializer.is_valid():
				user = serializer.save()
				
				return Response({
					'success': True,
					'message': 'Rider registered successfully',
					'data': serializer.to_representation(user)
				}, status=status.HTTP_201_CREATED)
			
			else:
				return Response({
					'success': False,
					'message': 'Registration failed due to validation errors',
					'errors': serializer.errors
				}, status=status.HTTP_400_BAD_REQUEST)
		
		except Exception as e:
			return Response({
				'success': False,
				'message': 'An unexpected error occurred during registration',
				'error': str(e)
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DriverRegistrationView(APIView):
	"""
	API endpoint for driver registration.
	
	Creates a new User account and associated Driver profile with comprehensive
	validation including vehicle information and license verification.
	
	POST /api/register/driver/
	"""
	permission_classes = [permissions.AllowAny]  # Public registration
	
	def post(self, request, *args, **kwargs):
		"""
		Register a new driver.
		
		Expected JSON format:
		{
			"username": "mike_driver",
			"email": "mike@example.com",
			"password": "securepassword123",
			"first_name": "Mike",
			"last_name": "Smith",
			"phone": "+1987654321",
			"license_number": "DL12345678",
			"license_expiry": "2025-12-31",
			"vehicle_make": "Toyota",
			"vehicle_model": "Camry",
			"vehicle_year": 2020,
			"vehicle_color": "Silver",
			"vehicle_type": "sedan",
			"license_plate": "ABC123"
		}
		"""
		from .serializers import DriverRegistrationSerializer
		
		try:
			serializer = DriverRegistrationSerializer(data=request.data)
			
			if serializer.is_valid():
				user = serializer.save()
				
				return Response({
					'success': True,
					'message': 'Driver registered successfully',
					'data': serializer.to_representation(user)
				}, status=status.HTTP_201_CREATED)
			
			else:
				return Response({
					'success': False,
					'message': 'Registration failed due to validation errors',
					'errors': serializer.errors
				}, status=status.HTTP_400_BAD_REQUEST)
		
		except Exception as e:
			return Response({
				'success': False,
				'message': 'An unexpected error occurred during registration',
				'error': str(e)
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderCancellationView(APIView):
	"""
	API endpoint for cancelling orders.
	
	Allows users to cancel their orders by updating the order status to 'Cancelled'.
	Only the order owner (user or customer) can cancel their order, and only orders
	that are not already completed or cancelled can be cancelled.
	"""
	permission_classes = [permissions.AllowAny]  # Will handle authorization manually
	authentication_classes = [SessionAuthentication, TokenAuthentication]

	def delete(self, request, order_id, *args, **kwargs):
		"""
		Cancel an order by setting its status to 'Cancelled'.
		
		Args:
			order_id: The user-friendly order ID (e.g., 'ORD-ABC123') or database ID
			
		Returns:
			200: Order successfully cancelled
			400: Order cannot be cancelled (already completed/cancelled)
			403: User not authorized to cancel this order
			404: Order not found
		"""
		try:
			# Try to find order by user-friendly order_id first, then by database id
			order = None
			if order_id.startswith('ORD-'):
				try:
					order = Order.objects.get(order_id=order_id)
				except Order.DoesNotExist:
					pass
			else:
				# Assume it's a database ID if it's numeric
				try:
					order = Order.objects.get(id=int(order_id))
				except (ValueError, Order.DoesNotExist):
					# Try as order_id if not numeric
					try:
						order = Order.objects.get(order_id=order_id)
					except Order.DoesNotExist:
						pass
			
			# If order not found, return 404
			if order is None:
				return Response({
					'success': False,
					'message': 'Order not found',
					'order_id': order_id
				}, status=status.HTTP_404_NOT_FOUND)
			
			# Check if user is authorized to cancel this order
			user = request.user if request.user.is_authenticated else None
			customer_id = request.data.get('customer_id') or request.query_params.get('customer_id')
			
			# Authorization logic: user must own the order or provide correct customer_id
			is_authorized = False
			if user and order.user == user:
				is_authorized = True
			elif customer_id and order.customer and str(order.customer.id) == str(customer_id):
				is_authorized = True
			# Removed insecure fallback for guest orders without proper identification
			
			if not is_authorized:
				return Response({
					'success': False,
					'message': 'You are not authorized to cancel this order',
					'error': 'Permission denied'
				}, status=status.HTTP_403_FORBIDDEN)
			
			# Check if order can be cancelled (not already completed or cancelled)
			if order.status.name in [OrderStatusChoices.COMPLETED, OrderStatusChoices.CANCELLED]:
				return Response({
					'success': False,
					'message': f'Cannot cancel order that is already {order.status.name.lower()}',
					'current_status': order.status.name,
					'order_id': order.order_id or str(order.id)
				}, status=status.HTTP_400_BAD_REQUEST)
			
			# Get or create cancelled status
			cancelled_status, _ = OrderStatus.objects.get_or_create(
				name=OrderStatusChoices.CANCELLED
			)
			
			# Update order status to cancelled
			previous_status = order.status.name
			order.status = cancelled_status
			order.save()
			
			return Response({
				'success': True,
				'message': 'Order cancelled successfully',
				'order_id': order.order_id or str(order.id),
				'previous_status': previous_status,
				'current_status': OrderStatusChoices.CANCELLED,
				'cancelled_at': timezone.now().isoformat()
			}, status=status.HTTP_200_OK)
			
		except Exception as e:
			return Response({
				'success': False,
				'message': 'An unexpected error occurred while cancelling the order',
				'error': str(e)
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CouponValidationView(APIView):
	"""
	API endpoint for validating coupon codes.
	
	Accepts POST requests with a coupon code and validates it against
	database constraints including existence, active status, date validity,
	and usage limits.
	"""
	permission_classes = [permissions.AllowAny]  # Allow both authenticated and guest users
	
	def post(self, request, *args, **kwargs):
		"""
		Validate a coupon code.
		
		Expected request data:
		{
			"code": "COUPON_CODE"
		}
		
		Returns:
		- 200: Coupon is valid with discount information
		- 400: Invalid request data or coupon validation failed
		- 404: Coupon code not found
		- 500: Server error
		"""
		try:
			# Extract coupon code from request
			coupon_code = request.data.get('code')
			
			if not coupon_code:
				return Response({
					'success': False,
					'message': 'Coupon code is required',
					'error_code': 'MISSING_CODE'
				}, status=status.HTTP_400_BAD_REQUEST)
			
			# Clean and validate code format
			coupon_code = coupon_code.strip().upper()
			
			if not coupon_code:
				return Response({
					'success': False,
					'message': 'Coupon code cannot be empty',
					'error_code': 'EMPTY_CODE'
				}, status=status.HTTP_400_BAD_REQUEST)
			
			# Import Coupon model here to avoid circular imports
			from .models import Coupon
			
			# Try to find the coupon
			try:
				coupon = Coupon.objects.get(code=coupon_code)
			except Coupon.DoesNotExist:
				return Response({
					'success': False,
					'message': 'Invalid coupon code',
					'error_code': 'COUPON_NOT_FOUND',
					'code': coupon_code
				}, status=status.HTTP_404_NOT_FOUND)
			
			# Check if coupon is active
			if not coupon.is_active:
				return Response({
					'success': False,
					'message': 'This coupon is no longer active',
					'error_code': 'COUPON_INACTIVE',
					'code': coupon_code
				}, status=status.HTTP_400_BAD_REQUEST)
			
			# Check date validity
			current_date = timezone.now().date()
			
			if current_date < coupon.valid_from:
				return Response({
					'success': False,
					'message': f'This coupon is not valid until {coupon.valid_from.strftime("%Y-%m-%d")}',
					'error_code': 'COUPON_NOT_YET_VALID',
					'code': coupon_code,
					'valid_from': coupon.valid_from.isoformat()
				}, status=status.HTTP_400_BAD_REQUEST)
			
			if current_date > coupon.valid_until:
				return Response({
					'success': False,
					'message': f'This coupon expired on {coupon.valid_until.strftime("%Y-%m-%d")}',
					'error_code': 'COUPON_EXPIRED',
					'code': coupon_code,
					'valid_until': coupon.valid_until.isoformat()
				}, status=status.HTTP_400_BAD_REQUEST)
			
			# Check usage limits
			if not coupon.is_usage_available():
				return Response({
					'success': False,
					'message': 'This coupon has reached its usage limit',
					'error_code': 'COUPON_USAGE_EXCEEDED',
					'code': coupon_code,
					'max_usage': coupon.max_usage,
					'current_usage': coupon.usage_count
				}, status=status.HTTP_400_BAD_REQUEST)
			
			# Coupon is valid - return success response with discount information
			response_data = {
				'success': True,
				'message': 'Coupon is valid and can be applied',
				'coupon': {
					'code': coupon.code,
					'discount_percentage': float(coupon.discount_percentage),
					'description': coupon.description,
					'valid_from': coupon.valid_from.isoformat(),
					'valid_until': coupon.valid_until.isoformat(),
					'usage_count': coupon.usage_count,
					'max_usage': coupon.max_usage
				}
			}
			
			return Response(response_data, status=status.HTTP_200_OK)
			
		except Exception as e:
			# Log the error for debugging
			import logging
			logger = logging.getLogger(__name__)
			logger.error(f"Error validating coupon '{coupon_code}': {str(e)}", exc_info=True)
			
			return Response({
				'success': False,
				'message': 'An unexpected error occurred while validating the coupon',
				'error_code': 'INTERNAL_ERROR'
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
