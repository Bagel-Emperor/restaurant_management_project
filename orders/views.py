
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone
from decimal import Decimal
from .models import Order, Customer, UserProfile, OrderStatus, Rider, Driver, Ride
from .serializers import (
    OrderSerializer, CustomerSerializer, OrderHistorySerializer, 
    UserProfileSerializer, OrderDetailSerializer, RideSerializer, 
    RideRequestSerializer, UpdateOrderStatusSerializer,
    FareCalculationSerializer, RidePaymentSerializer,
    DriverEarningsSerializer, DriverAvailabilitySerializer
)
from .choices import OrderStatusChoices
import logging

# Module-level logger for efficient logging across all views
logger = logging.getLogger(__name__)

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
		# Initialize coupon_code to prevent UnboundLocalError in exception handling
		coupon_code = None
		
		try:
			# Use DRF Serializer for centralized validation and normalization
			from .serializers import CouponValidationSerializer
			serializer = CouponValidationSerializer(data=request.data)
			
			if not serializer.is_valid():
				# Return DRF's standardized error format
				return Response({
					'success': False,
					'message': 'Invalid coupon code format',
					'error_code': 'VALIDATION_ERROR',
					'errors': serializer.errors
				}, status=status.HTTP_400_BAD_REQUEST)
			
			# Get the validated and normalized coupon code
			coupon_code = serializer.validated_data['code']
			
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
			# Use safe logging to handle cases where coupon_code might be undefined
			logger.error(f"Error validating coupon '{coupon_code or 'undefined'}': {str(e)}", exc_info=True)
			
			return Response({
				'success': False,
				'message': 'An unexpected error occurred while validating the coupon',
				'error_code': 'INTERNAL_ERROR'
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# Ride Booking Views (Rider → Driver)
# ============================================================================

class RideRequestView(APIView):
	"""
	API view for riders to request a new ride.
	
	POST /api/ride/request/
	
	Requires JWT authentication. Automatically assigns the ride to the
	authenticated rider. Creates a ride with status='REQUESTED'.
	
	Expected request body:
	{
		"pickup_address": "Koramangala, Bangalore",
		"dropoff_address": "MG Road, Bangalore",
		"pickup_lat": 12.9352,
		"pickup_lng": 77.6147,
		"drop_lat": 12.9763,
		"drop_lng": 77.6033
	}
	"""
	
	permission_classes = [permissions.IsAuthenticated]
	
	def post(self, request):
		"""Create a new ride request."""
		try:
			# Verify user has a rider profile
			try:
				rider = request.user.rider_profile
			except AttributeError:
				logger.warning(f"User {request.user.username} attempted to request ride without rider profile")
				return Response({
					'success': False,
					'message': 'User does not have a rider profile',
					'error_code': 'NO_RIDER_PROFILE'
				}, status=status.HTTP_403_FORBIDDEN)
			
			# Validate request data
			serializer = RideRequestSerializer(data=request.data)
			
			if not serializer.is_valid():
				logger.warning(f"Invalid ride request data from rider {rider.user.username}: {serializer.errors}")
				return Response({
					'success': False,
					'message': 'Invalid ride request data',
					'errors': serializer.errors,
					'error_code': 'INVALID_DATA'
				}, status=status.HTTP_400_BAD_REQUEST)
			
			# Create the ride
			ride = serializer.save(rider=rider)
			
			logger.info(f"New ride request created: Ride #{ride.pk} by rider {rider.user.username}")
			
			# Return full ride details
			response_serializer = RideSerializer(ride)
			
			return Response({
				'success': True,
				'message': 'Ride requested successfully',
				'ride': response_serializer.data
			}, status=status.HTTP_201_CREATED)
			
		except Exception as e:
			logger.error(f"Error creating ride request: {str(e)}", exc_info=True)
			return Response({
				'success': False,
				'message': 'An unexpected error occurred while requesting the ride',
				'error_code': 'INTERNAL_ERROR'
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AvailableRidesView(APIView):
	"""
	API view for drivers to see available (unassigned) ride requests.
	
	GET /api/ride/available/
	
	Requires JWT authentication. Returns all rides with status='REQUESTED'
	and no driver assigned. Orders by requested_at (oldest first) to ensure
	fair allocation.
	
	Drivers can use this to find rides they can accept.
	"""
	
	permission_classes = [permissions.IsAuthenticated]
	
	def get(self, request):
		"""List all available ride requests."""
		try:
			# Verify user has a driver profile
			try:
				driver = request.user.driver_profile
			except AttributeError:
				logger.warning(f"User {request.user.username} attempted to view available rides without driver profile")
				return Response({
					'success': False,
					'message': 'User does not have a driver profile',
					'error_code': 'NO_DRIVER_PROFILE'
				}, status=status.HTTP_403_FORBIDDEN)
			
			# Get all unassigned ride requests
			available_rides = Ride.objects.filter(
				status=Ride.STATUS_REQUESTED,
				driver__isnull=True
			).order_by('requested_at')
			
			# Serialize the rides
			serializer = RideSerializer(available_rides, many=True)
			
			# Cache count to avoid duplicate database query
			rides_count = available_rides.count()
			
			logger.info(f"Driver {driver.user.username} viewed {rides_count} available rides")
			
			return Response({
				'success': True,
				'count': rides_count,
				'rides': serializer.data
			}, status=status.HTTP_200_OK)
			
		except Exception as e:
			logger.error(f"Error fetching available rides: {str(e)}", exc_info=True)
			return Response({
				'success': False,
				'message': 'An unexpected error occurred while fetching available rides',
				'error_code': 'INTERNAL_ERROR'
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AcceptRideView(APIView):
	"""
	API view for drivers to accept a ride request.
	
	POST /api/ride/accept/<ride_id>/
	
	Requires JWT authentication. Assigns the ride to the authenticated driver
	and changes status to 'ONGOING'. Uses atomic transactions to prevent
	race conditions where multiple drivers try to accept the same ride.
	
	Returns error if ride is already accepted or not in REQUESTED status.
	"""
	
	permission_classes = [permissions.IsAuthenticated]
	
	def post(self, request, ride_id):
		"""Accept a ride request."""
		from django.db import transaction
		
		try:
			# Verify user has a driver profile
			try:
				driver = request.user.driver_profile
			except AttributeError:
				logger.warning(f"User {request.user.username} attempted to accept ride without driver profile")
				return Response({
					'success': False,
					'message': 'User does not have a driver profile',
					'error_code': 'NO_DRIVER_PROFILE'
				}, status=status.HTTP_403_FORBIDDEN)
			
			# Use atomic transaction to prevent race conditions
			with transaction.atomic():
				try:
					# Lock the ride row to prevent concurrent updates
					ride = Ride.objects.select_for_update().get(pk=ride_id)
				except Ride.DoesNotExist:
					logger.warning(f"Driver {driver.user.username} attempted to accept non-existent ride #{ride_id}")
					return Response({
						'success': False,
						'message': f'Ride with ID {ride_id} not found',
						'error_code': 'RIDE_NOT_FOUND'
					}, status=status.HTTP_404_NOT_FOUND)
				
				# Try to accept the ride - model method handles all validation
				success = ride.accept_ride(driver)
				
				if not success:
					# Model method failed - ride not available
					logger.warning(f"Driver {driver.user.username} failed to accept ride #{ride_id} (status: {ride.status}, driver: {ride.driver})")
					return Response({
						'success': False,
						'message': f'Ride is no longer available (current status: {ride.get_status_display()})',
						'error_code': 'RIDE_NOT_AVAILABLE',
						'current_status': ride.status
					}, status=status.HTTP_400_BAD_REQUEST)
				
				logger.info(f"Ride #{ride_id} accepted by driver {driver.user.username}")
			
			# Return updated ride details
			serializer = RideSerializer(ride)
			
			return Response({
				'success': True,
				'message': 'Ride accepted successfully',
				'ride': serializer.data
			}, status=status.HTTP_200_OK)
		
		except Exception as e:
			logger.error(f"Error accepting ride #{ride_id}: {str(e)}", exc_info=True)
			return Response({
				'success': False,
				'message': 'An unexpected error occurred while accepting the ride',
				'error_code': 'INTERNAL_ERROR'
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# TASK 6: Real-Time Location Tracking
# ============================================================================

class UpdateLocationView(APIView):
	"""
	POST /api/ride/update-location/
	
	Allows authenticated drivers to update their current GPS location.
	This simulates real-time tracking where driver apps send coordinates
	every few seconds during an active ride.
	"""
	permission_classes = [permissions.IsAuthenticated]
	
	def post(self, request):
		"""Update driver's current location."""
		try:
			# Verify user has a driver profile
			try:
				driver = request.user.driver_profile
			except AttributeError:
				logger.warning(f"User {request.user.username} attempted to update location without driver profile")
				return Response({
					'success': False,
					'message': 'User does not have a driver profile',
					'error_code': 'NO_DRIVER_PROFILE'
				}, status=status.HTTP_403_FORBIDDEN)
			
			# Validate required fields
			latitude = request.data.get('latitude')
			longitude = request.data.get('longitude')
			
			if latitude is None or longitude is None:
				return Response({
					'success': False,
					'message': 'Both latitude and longitude are required',
					'error_code': 'MISSING_COORDINATES'
				}, status=status.HTTP_400_BAD_REQUEST)
			
			# Validate coordinate ranges
			try:
				lat = Decimal(str(latitude))
				lng = Decimal(str(longitude))
				
				if not (Decimal('-90') <= lat <= Decimal('90')):
					return Response({
						'success': False,
						'message': 'Latitude must be between -90 and 90',
						'error_code': 'INVALID_LATITUDE'
					}, status=status.HTTP_400_BAD_REQUEST)
				
				if not (Decimal('-180') <= lng <= Decimal('180')):
					return Response({
						'success': False,
						'message': 'Longitude must be between -180 and 180',
						'error_code': 'INVALID_LONGITUDE'
					}, status=status.HTTP_400_BAD_REQUEST)
				
			except (ValueError, TypeError):
				return Response({
					'success': False,
					'message': 'Invalid coordinate format',
					'error_code': 'INVALID_COORDINATES'
				}, status=status.HTTP_400_BAD_REQUEST)
			
			# Update driver location
			driver.current_latitude = lat
			driver.current_longitude = lng
			driver.save(update_fields=['current_latitude', 'current_longitude'])
			
			logger.info(f"Driver {driver.user.username} updated location to ({lat}, {lng})")
			
			return Response({
				'success': True,
				'message': 'Location updated successfully',
				'latitude': str(lat),
				'longitude': str(lng)
			}, status=status.HTTP_200_OK)
			
		except Exception as e:
			logger.error(f"Error updating driver location: {str(e)}", exc_info=True)
			return Response({
				'success': False,
				'message': 'An unexpected error occurred while updating location',
				'error_code': 'INTERNAL_ERROR'
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TrackRideView(APIView):
	"""
	GET /api/ride/track/<ride_id>/
	
	Allows riders to track their driver's current location during an ONGOING ride.
	Returns the driver's latest GPS coordinates for map display.
	"""
	permission_classes = [permissions.IsAuthenticated]
	
	def get(self, request, ride_id):
		"""Get driver's current location for a specific ride."""
		try:
			# Get the ride
			try:
				ride = Ride.objects.select_related('rider', 'driver').get(pk=ride_id)
			except Ride.DoesNotExist:
				return Response({
					'success': False,
					'message': f'Ride with ID {ride_id} not found',
					'error_code': 'RIDE_NOT_FOUND'
				}, status=status.HTTP_404_NOT_FOUND)
			
			# Verify user is the rider for this ride
			try:
				rider = request.user.rider_profile
				if ride.rider.id != rider.id:
					logger.warning(f"Rider {rider.user.username} attempted to track ride #{ride_id} belonging to another rider")
					return Response({
						'success': False,
						'message': 'You can only track your own rides',
						'error_code': 'PERMISSION_DENIED'
					}, status=status.HTTP_403_FORBIDDEN)
			except AttributeError:
				logger.warning(f"User {request.user.username} attempted to track ride without rider profile")
				return Response({
					'success': False,
					'message': 'User does not have a rider profile',
					'error_code': 'NO_RIDER_PROFILE'
				}, status=status.HTTP_403_FORBIDDEN)
			
			# Check ride status - only allow tracking for ONGOING rides
			if ride.status != Ride.STATUS_ONGOING:
				return Response({
					'success': False,
					'message': f'Cannot track ride with status: {ride.get_status_display()}',
					'error_code': 'INVALID_RIDE_STATUS',
					'current_status': ride.status
				}, status=status.HTTP_400_BAD_REQUEST)
			
			# Check if driver has location data
			if ride.driver is None:
				return Response({
					'success': False,
					'message': 'Ride has no assigned driver',
					'error_code': 'NO_DRIVER_ASSIGNED'
				}, status=status.HTTP_400_BAD_REQUEST)
			
			if ride.driver.current_latitude is None or ride.driver.current_longitude is None:
				return Response({
					'success': False,
					'message': 'Driver location not available',
					'error_code': 'LOCATION_UNAVAILABLE'
				}, status=status.HTTP_404_NOT_FOUND)
			
			# Return driver's current location
			logger.info(f"Rider {rider.user.username} tracking driver {ride.driver.user.username} for ride #{ride_id}")
			
			return Response({
				'success': True,
				'ride_id': ride.id,
				'driver_latitude': str(ride.driver.current_latitude),
				'driver_longitude': str(ride.driver.current_longitude),
				'driver_name': ride.driver.user.username,
				'vehicle': f"{ride.driver.vehicle_color} {ride.driver.vehicle_make} {ride.driver.vehicle_model}",
				'license_plate': ride.driver.license_plate
			}, status=status.HTTP_200_OK)
			
		except Exception as e:
			logger.error(f"Error tracking ride #{ride_id}: {str(e)}", exc_info=True)
			return Response({
				'success': False,
				'message': 'An unexpected error occurred while tracking ride',
				'error_code': 'INTERNAL_ERROR'
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# TASK 7: Complete & Cancel Ride Status Transitions
# ============================================================================

class CompleteRideView(APIView):
	"""
	POST /api/ride/complete/<ride_id>/
	
	Allows drivers to mark an ONGOING ride as COMPLETED.
	Enforces strict validation: only assigned driver can complete,
	and ride must be in ONGOING status.
	"""
	permission_classes = [permissions.IsAuthenticated]
	
	def post(self, request, ride_id):
		"""Mark a ride as completed."""
		try:
			# Verify user has a driver profile
			try:
				driver = request.user.driver_profile
			except AttributeError:
				logger.warning(f"User {request.user.username} attempted to complete ride without driver profile")
				return Response({
					'success': False,
					'message': 'User does not have a driver profile',
					'error_code': 'NO_DRIVER_PROFILE'
				}, status=status.HTTP_403_FORBIDDEN)
			
			# Get the ride
			try:
				ride = Ride.objects.select_related('driver', 'rider').get(pk=ride_id)
			except Ride.DoesNotExist:
				return Response({
					'success': False,
					'message': f'Ride with ID {ride_id} not found',
					'error_code': 'RIDE_NOT_FOUND'
				}, status=status.HTTP_404_NOT_FOUND)
			
			# Verify driver is assigned to this ride
			if ride.driver is None or ride.driver.id != driver.id:
				logger.warning(f"Driver {driver.user.username} attempted to complete ride #{ride_id} not assigned to them")
				return Response({
					'success': False,
					'message': 'You can only complete rides assigned to you',
					'error_code': 'PERMISSION_DENIED'
				}, status=status.HTTP_403_FORBIDDEN)
			
			# Verify ride is in ONGOING status
			if ride.status != Ride.STATUS_ONGOING:
				return Response({
					'success': False,
					'message': f'Cannot complete ride with status: {ride.get_status_display()}',
					'error_code': 'INVALID_STATUS',
					'current_status': ride.status
				}, status=status.HTTP_400_BAD_REQUEST)
			
			# Mark ride as completed
			success = ride.complete_ride()
			
			if not success:
				logger.error(f"Failed to complete ride #{ride_id}")
				return Response({
					'success': False,
					'message': 'Failed to complete ride',
					'error_code': 'COMPLETION_FAILED'
				}, status=status.HTTP_400_BAD_REQUEST)
			
			logger.info(f"Ride #{ride_id} completed by driver {driver.user.username}")
			
			return Response({
				'success': True,
				'message': 'Ride marked as completed',
				'ride_id': ride.id,
				'status': ride.status
			}, status=status.HTTP_200_OK)
			
		except Exception as e:
			logger.error(f"Error completing ride #{ride_id}: {str(e)}", exc_info=True)
			return Response({
				'success': False,
				'message': 'An unexpected error occurred while completing ride',
				'error_code': 'INTERNAL_ERROR'
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CancelRideView(APIView):
	"""
	POST /api/ride/cancel/<ride_id>/
	
	Allows riders to cancel a REQUESTED ride before it's accepted.
	Once a ride is ONGOING or COMPLETED, it cannot be cancelled.
	"""
	permission_classes = [permissions.IsAuthenticated]
	
	def post(self, request, ride_id):
		"""Cancel a ride request."""
		try:
			# Verify user has a rider profile
			try:
				rider = request.user.rider_profile
			except AttributeError:
				logger.warning(f"User {request.user.username} attempted to cancel ride without rider profile")
				return Response({
					'success': False,
					'message': 'User does not have a rider profile',
					'error_code': 'NO_RIDER_PROFILE'
				}, status=status.HTTP_403_FORBIDDEN)
			
			# Get the ride
			try:
				ride = Ride.objects.select_related('rider', 'driver').get(pk=ride_id)
			except Ride.DoesNotExist:
				return Response({
					'success': False,
					'message': f'Ride with ID {ride_id} not found',
					'error_code': 'RIDE_NOT_FOUND'
				}, status=status.HTTP_404_NOT_FOUND)
			
			# Verify rider owns this ride
			if ride.rider.id != rider.id:
				logger.warning(f"Rider {rider.user.username} attempted to cancel ride #{ride_id} belonging to another rider")
				return Response({
					'success': False,
					'message': 'You can only cancel your own rides',
					'error_code': 'PERMISSION_DENIED'
				}, status=status.HTTP_403_FORBIDDEN)
			
			# Verify ride is still in REQUESTED status
			if ride.status != Ride.STATUS_REQUESTED:
				return Response({
					'success': False,
					'message': 'Cannot cancel a ride that is already ongoing or completed',
					'error_code': 'INVALID_STATUS',
					'current_status': ride.status,
					'status_display': ride.get_status_display()
				}, status=status.HTTP_400_BAD_REQUEST)
			
			# Cancel the ride
			success = ride.cancel_ride()
			
			if not success:
				logger.error(f"Failed to cancel ride #{ride_id}")
				return Response({
					'success': False,
					'message': 'Failed to cancel ride',
					'error_code': 'CANCELLATION_FAILED'
				}, status=status.HTTP_400_BAD_REQUEST)
			
			logger.info(f"Ride #{ride_id} cancelled by rider {rider.user.username}")
			
			return Response({
				'success': True,
				'message': 'Ride cancelled successfully',
				'ride_id': ride.id,
				'status': ride.status
			}, status=status.HTTP_200_OK)
			
		except Exception as e:
			logger.error(f"Error cancelling ride #{ride_id}: {str(e)}", exc_info=True)
			return Response({
				'success': False,
				'message': 'An unexpected error occurred while cancelling ride',
				'error_code': 'INTERNAL_ERROR'
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# TASK 8: Rider & Driver Ride History with Pagination
# ============================================================================

class RiderHistoryView(generics.ListAPIView):
	"""
	GET /api/rider/history/
	
	Returns paginated ride history for the authenticated rider.
	Shows only COMPLETED and CANCELLED rides.
	Automatically paginates with 10 rides per page (configured in settings).
	"""
	serializer_class = RideSerializer
	permission_classes = [permissions.IsAuthenticated]
	
	def get_queryset(self):
		"""Filter rides by authenticated rider, show only completed/cancelled."""
		try:
			rider = self.request.user.rider_profile
		except AttributeError:
			logger.warning(f"User {self.request.user.username} attempted to view rider history without rider profile")
			return Ride.objects.none()
		
		# Return only completed or cancelled rides for this rider
		queryset = Ride.objects.filter(
			rider=rider,
			status__in=[Ride.STATUS_COMPLETED, Ride.STATUS_CANCELLED]
		).select_related('driver', 'driver__user').order_by('-requested_at')
		
		logger.info(f"Rider {rider.user.username} viewed ride history")
		
		return queryset
	
	def list(self, request, *args, **kwargs):
		"""Override list to add success flag and handle no profile case."""
		try:
			rider = request.user.rider_profile
		except AttributeError:
			return Response({
				'success': False,
				'message': 'User does not have a rider profile',
				'error_code': 'NO_RIDER_PROFILE'
			}, status=status.HTTP_403_FORBIDDEN)
		
		# Call parent's list method for automatic pagination
		response = super().list(request, *args, **kwargs)
		
		# Wrap response in success structure
		return Response({
			'success': True,
			'count': response.data['count'],
			'next': response.data['next'],
			'previous': response.data['previous'],
			'results': response.data['results']
		}, status=status.HTTP_200_OK)


class DriverHistoryView(generics.ListAPIView):
	"""
	GET /api/driver/history/
	
	Returns paginated ride history for the authenticated driver.
	Shows only COMPLETED and CANCELLED rides.
	Automatically paginates with 10 rides per page (configured in settings).
	"""
	serializer_class = RideSerializer
	permission_classes = [permissions.IsAuthenticated]
	
	def get_queryset(self):
		"""Filter rides by authenticated driver, show only completed/cancelled."""
		try:
			driver = self.request.user.driver_profile
		except AttributeError:
			logger.warning(f"User {self.request.user.username} attempted to view driver history without driver profile")
			return Ride.objects.none()
		
		# Return only completed or cancelled rides for this driver
		queryset = Ride.objects.filter(
			driver=driver,
			status__in=[Ride.STATUS_COMPLETED, Ride.STATUS_CANCELLED]
		).select_related('rider', 'rider__user').order_by('-requested_at')
		
		logger.info(f"Driver {driver.user.username} viewed ride history")
		
		return queryset
	
	def list(self, request, *args, **kwargs):
		"""Override list to add success flag and handle no profile case."""
		try:
			driver = request.user.driver_profile
		except AttributeError:
			return Response({
				'success': False,
				'message': 'User does not have a driver profile',
				'error_code': 'NO_DRIVER_PROFILE'
			}, status=status.HTTP_403_FORBIDDEN)
		
		# Call parent's list method for automatic pagination
		response = super().list(request, *args, **kwargs)
		
		# Wrap response in success structure
		return Response({
			'success': True,
			'count': response.data['count'],
			'next': response.data['next'],
			'previous': response.data['previous'],
			'results': response.data['results']
		}, status=status.HTTP_200_OK)


# ================================
# ORDER STATUS RETRIEVAL API VIEW
# ================================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_order_status(request, order_id):
	"""
	Function-based API view to retrieve the current status of an order.
	
	This endpoint provides a lightweight way to check order status without
	fetching all order details. Useful for order tracking and status polling.
	
	Args:
		request: The HTTP request object
		order_id (str): The unique order identifier (e.g., "ORD-A7X9K2M5")
	
	Returns:
		Response: JSON containing order ID and current status
	
	Response (Success - 200 OK):
		{
			"order_id": "ORD-A7X9K2M5",
			"status": "Processing",
			"updated_at": "2025-10-14T21:45:00Z"
		}
	
	Response (Not Found - 404):
		{
			"error": "Order not found",
			"order_id": "ORD-INVALID"
		}
	
	Examples:
		>>> GET /PerpexBistro/orders/ORD-A7X9K2M5/status/
		{
			"order_id": "ORD-A7X9K2M5",
			"status": "Completed",
			"updated_at": "2025-10-14T22:00:00Z"
		}
	"""
	try:
		# Retrieve the order with status relation for efficiency
		order = Order.objects.select_related('status').get(order_id=order_id)
		
		# Return order ID, status, and last update time
		return Response({
			'order_id': order.order_id,
			'status': order.status.name,
			'updated_at': order.updated_at
		}, status=status.HTTP_200_OK)
		
	except Order.DoesNotExist:
		# Handle case where order doesn't exist
		logger.warning('Order status retrieval failed: Order %s not found', order_id)
		return Response({
			'error': 'Order not found',
			'order_id': order_id
		}, status=status.HTTP_404_NOT_FOUND)


# ================================
# ORDER STATUS UPDATE API VIEW
# ================================

class UpdateOrderStatusView(APIView):
	"""
	API view to update the status of an order.
	
	Accepts POST or PUT request with order_id and new status. Validates the status 
	transition and updates the order in the database. Returns appropriate error messages 
	for invalid order IDs, invalid status values, or disallowed status transitions.
	
	Request Body:
		{
			"order_id": "ORD-A7X9K2M5",
			"status": "Processing"
		}
	
	Response (Success):
		{
			"success": true,
			"message": "Order status updated successfully",
			"order": {
				"order_id": "ORD-A7X9K2M5",
				"status": "Processing",
				"previous_status": "Pending",
				"updated_at": "2025-10-09T10:30:00Z"
			}
		}
	
	Response (Error):
		{
			"success": false,
			"errors": {"status": ["Invalid status transition from 'Completed' to 'Pending'"]}
		}
	"""
	permission_classes = [permissions.IsAuthenticated]  # Restrict to authenticated users only
	
	def _update_order_status(self, request):
		"""
		Common method to handle order status updates for both POST and PUT requests.
		
		Args:
			request: The HTTP request object
			
		Returns:
			Response: DRF Response object with success/error data
		"""
		serializer = UpdateOrderStatusSerializer(data=request.data)
		
		if not serializer.is_valid():
			logger.warning(f"Order status update failed validation: {serializer.errors}")
			return Response({
				'success': False,
				'errors': serializer.errors
			}, status=status.HTTP_400_BAD_REQUEST)
		
		# Get validated data
		order_id = serializer.validated_data['order_id']
		new_status_name = serializer.validated_data['status']
		
		try:
			# Get the order
			order = Order.objects.select_related('status').get(order_id=order_id)
			previous_status = order.status.name
			
			# Get or create the new status object
			new_status, created = OrderStatus.objects.get_or_create(name=new_status_name)
			
			# Update the order status (auto_now will update updated_at automatically)
			order.status = new_status
			order.save()
			
			# Refresh from database to get the updated timestamp
			order.refresh_from_db()
			
			logger.info(f"Order {order_id} status updated from '{previous_status}' to '{new_status_name}' by user {request.user.username}")
			
			return Response({
				'success': True,
				'message': 'Order status updated successfully',
				'order': {
					'order_id': order.order_id,
					'status': order.status.name,
					'previous_status': previous_status,
					'updated_at': order.updated_at.isoformat()
				}
			}, status=status.HTTP_200_OK)
			
		except Order.DoesNotExist:
			logger.error(f"Order {order_id} not found during status update")
			return Response({
				'success': False,
				'errors': {'order_id': [f"Order with ID '{order_id}' does not exist."]}
			}, status=status.HTTP_404_NOT_FOUND)
		
		except Exception as e:
			logger.error(f"Unexpected error updating order {order_id}: {str(e)}")
			return Response({
				'success': False,
				'errors': {'detail': 'An unexpected error occurred while updating the order status.'}
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
	
	def post(self, request, *args, **kwargs):
		"""Handle POST request to update order status."""
		return self._update_order_status(request)
	
	def put(self, request, *args, **kwargs):
		"""Handle PUT request to update order status."""
		return self._update_order_status(request)


# =============================================================================
# RIDE FARE CALCULATION VIEWS (Task 10B)
# =============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculate_fare(request, ride_id):
	"""
	Calculate and store fare for a completed ride.
	
	This endpoint calculates the ride fare using the Haversine distance formula
	and applies the fare calculation formula: base_fare + (distance × per_km_rate) × surge_multiplier
	
	Task 10B: Calculate & Store Ride Fare — View
	
	URL: POST /api/ride/calculate-fare/<ride_id>/
	Authentication: JWT required
	Authorization: Rider, Driver, or Admin only
	
	Request:
		No body required (ride_id is in URL)
	
	Success Response (200 OK):
		{
			"fare": 162.45,
			"message": "Fare calculated and saved."
		}
	
	Error Responses:
		404: Ride not found
		400: Ride not completed yet
		400: Fare already set
		403: User not authorized to calculate fare for this ride
	
	Authorization:
		- The rider who requested the ride
		- The driver assigned to the ride
		- Admin users (staff)
	
	Business Logic:
		1. Validates ride exists
		2. Checks ride is COMPLETED
		3. Verifies user authorization (rider/driver/admin)
		4. Checks fare not already calculated
		5. Uses FareCalculationSerializer to calculate and save fare
		6. Returns calculated fare
	
	Example:
		>>> # Using curl
		>>> curl -X POST http://localhost:8000/api/ride/calculate-fare/42/ \\
		...      -H "Authorization: Bearer <jwt_token>"
		
		>>> # Using Python requests
		>>> import requests
		>>> response = requests.post(
		...     'http://localhost:8000/api/ride/calculate-fare/42/',
		...     headers={'Authorization': f'Bearer {jwt_token}'}
		... )
		>>> print(response.json())
		{'fare': 162.45, 'message': 'Fare calculated and saved.'}
	
	Args:
		request: Django REST framework request object
		ride_id (int): ID of the ride to calculate fare for
	
	Returns:
		Response: JSON response with fare or error message
	"""
	try:
		ride = Ride.objects.get(id=ride_id)
	except Ride.DoesNotExist:
		logger.warning(f"Fare calculation attempted for non-existent ride {ride_id}")
		return Response(
			{"error": "Ride not found."},
			status=status.HTTP_404_NOT_FOUND
		)
	
	# Ride must be completed before fare calculation
	if ride.status != Ride.STATUS_COMPLETED:
		logger.info(f"Fare calculation attempted for incomplete ride {ride_id} (status: {ride.status})")
		return Response(
			{"error": "Ride must be completed before fare calculation."},
			status=status.HTTP_400_BAD_REQUEST
		)
	
	# Authorization check: Only rider, driver, or admin can calculate fare
	user = request.user
	is_driver = hasattr(user, "driver_profile") and ride.driver == user.driver_profile
	is_rider = hasattr(user, "rider_profile") and ride.rider == user.rider_profile
	is_admin = user.is_staff
	
	if not (is_driver or is_rider or is_admin):
		logger.warning(
			f"Unauthorized fare calculation attempt by user {user.username} for ride {ride_id}"
		)
		return Response(
			{"error": "You are not authorized to calculate fare for this ride."},
			status=status.HTTP_403_FORBIDDEN
		)
	
	# Check if fare already set (prevent duplicate calculation)
	if ride.fare is not None:
		logger.info(f"Fare calculation attempted for ride {ride_id} but fare already set: ₹{ride.fare}")
		return Response(
			{"error": "Fare already set."},
			status=status.HTTP_400_BAD_REQUEST
		)
	
	# Use serializer to calculate and save fare
	serializer = FareCalculationSerializer(instance=ride, data={})
	serializer.is_valid(raise_exception=True)
	
	logger.info(
		f"Fare calculated for ride {ride_id}: ₹{ride.fare} "
		f"(surge: {ride.surge_multiplier}x) by user {user.username}"
	)
	
	return Response({
		"fare": ride.fare,
		"message": "Fare calculated and saved."
	}, status=status.HTTP_200_OK)


# =============================================================================
# RIDE PAYMENT VIEWS (Task 11B)
# =============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_ride_as_paid(request, ride_id):
	"""
	Mark a completed ride as paid and record payment details.
	
	This endpoint allows riders or drivers to mark a ride as paid after completion.
	It records the payment method (CASH, UPI, or CARD) and timestamps the payment.
	
	Task 11B: Payment Flow — Create View to Mark Ride as Paid
	
	URL: POST /api/ride/payment/<ride_id>/
	Authentication: JWT required
	Authorization: Rider or Driver only (not admin for payment marking)
	
	Request Body:
		{
			"payment_method": "CASH",  // or "UPI" or "CARD"
			"payment_status": "PAID"
		}
	
	Success Response (200 OK):
		{
			"message": "Payment marked as complete.",
			"status": "PAID",
			"method": "CASH"
		}
	
	Error Responses:
		404: Ride not found
		400: Ride is not completed yet
		400: Ride is already marked as paid
		403: User not authorized to mark payment
	
	Authorization:
		- The rider who requested the ride
		- The driver assigned to the ride
		- NOT admin (admins should not mark payments on behalf of users)
	
	Business Logic:
		1. Validates ride exists
		2. Checks user is rider or driver (ownership)
		3. Uses RidePaymentSerializer to validate and update payment
		4. Records payment_method, payment_status, and paid_at timestamp
		5. Prevents modification if already paid
	
	Example:
		>>> # Driver marks ride as paid with cash
		>>> curl -X POST http://localhost:8000/api/ride/payment/42/ \\
		...      -H "Authorization: Bearer <jwt_token>" \\
		...      -H "Content-Type: application/json" \\
		...      -d '{"payment_method": "CASH", "payment_status": "PAID"}'
		
		>>> # Using Python requests
		>>> import requests
		>>> response = requests.post(
		...     'http://localhost:8000/api/ride/payment/42/',
		...     headers={
		...         'Authorization': f'Bearer {jwt_token}',
		...         'Content-Type': 'application/json'
		...     },
		...     json={'payment_method': 'UPI', 'payment_status': 'PAID'}
		... )
		>>> print(response.json())
		{'message': 'Payment marked as complete.', 'status': 'PAID', 'method': 'UPI'}
	
	Args:
		request: Django REST framework request object with payment data
		ride_id (int): ID of the ride to mark as paid
	
	Returns:
		Response: JSON response with payment confirmation or error message
	"""
	try:
		ride = Ride.objects.get(id=ride_id)
	except Ride.DoesNotExist:
		logger.warning(f"Payment marking attempted for non-existent ride {ride_id}")
		return Response(
			{"error": "Ride not found."},
			status=status.HTTP_404_NOT_FOUND
		)
	
	# Authorization check: Only rider or driver can mark as paid
	user = request.user
	is_driver = hasattr(user, "driver_profile") and ride.driver == user.driver_profile
	is_rider = hasattr(user, "rider_profile") and ride.rider == user.rider_profile
	
	if not (is_driver or is_rider):
		logger.warning(
			f"Unauthorized payment marking attempt by user {user.username} for ride {ride_id}"
		)
		return Response(
			{"error": "You are not authorized to mark this ride as paid."},
			status=status.HTTP_403_FORBIDDEN
		)
	
	# Use serializer to validate and update payment information
	serializer = RidePaymentSerializer(instance=ride, data=request.data)
	
	if serializer.is_valid():
		serializer.save()
		
		logger.info(
			f"Ride {ride_id} marked as {ride.payment_status} via {ride.payment_method} "
			f"by user {user.username} at {ride.paid_at}"
		)
		
		return Response({
			"message": "Payment marked as complete.",
			"status": ride.payment_status,
			"method": ride.payment_method
		}, status=status.HTTP_200_OK)
	
	# Return validation errors
	logger.info(f"Invalid payment data for ride {ride_id}: {serializer.errors}")
	return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ================================
# DRIVER EARNINGS SUMMARY VIEW (TASK 12B)
# ================================

class DriverEarningsSummaryView(APIView):
	"""
	API view to retrieve driver's earnings summary for the last 7 days.
	
	GET /api/driver/earnings/
	
	Requires JWT authentication and a driver profile. Returns comprehensive
	earnings data including total rides, total earnings, payment method breakdown,
	and average fare for completed, paid rides from the last 7 days.
	
	Response (Success):
		{
			"total_rides": 18,
			"total_earnings": "4850.00",
			"payment_breakdown": {
				"CASH": 8,
				"UPI": 6,
				"CARD": 4
			},
			"average_fare": "269.44"
		}
	
	Response (Error - No Driver Profile):
		{
			"success": false,
			"message": "User does not have a driver profile",
			"error_code": "NO_DRIVER_PROFILE"
		}
	"""
	
	permission_classes = [permissions.IsAuthenticated]
	
	def get(self, request):
		"""Retrieve driver's earnings summary for the last 7 days."""
		try:
			# Verify user has a driver profile
			try:
				driver = request.user.driver_profile
			except AttributeError:
				logger.warning(f"User {request.user.username} attempted to access earnings without driver profile")
				return Response({
					'success': False,
					'message': 'User does not have a driver profile',
					'error_code': 'NO_DRIVER_PROFILE'
				}, status=status.HTTP_403_FORBIDDEN)
			
			# Serialize driver's earnings data
			serializer = DriverEarningsSerializer(driver)
			
			logger.info(f"Driver {driver.user.username} retrieved earnings summary")
			
			return Response(serializer.data, status=status.HTTP_200_OK)
			
		except Exception as e:
			logger.error(f"Error retrieving earnings for user {request.user.username}: {str(e)}")
			return Response({
				'success': False,
				'message': 'An error occurred while retrieving earnings summary',
				'error_code': 'INTERNAL_ERROR'
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ================================
# DRIVER AVAILABILITY TOGGLE VIEW (TASK 13B)
# ================================

class DriverAvailabilityToggleView(APIView):
	"""
	API view for drivers to toggle their availability status.
	
	POST /api/driver/availability/
	
	Requires JWT authentication and a driver profile. Allows drivers to go
	online (available) or offline. Updates the driver's availability_status
	in the database and returns the updated status.
	
	Request Body:
		{
			"is_available": true
		}
	
	Response (Success - Going Online):
		{
			"is_available": true,
			"availability_status": "available"
		}
	
	Response (Success - Going Offline):
		{
			"is_available": false,
			"availability_status": "offline"
		}
	
	Response (Error - No Driver Profile):
		{
			"success": false,
			"message": "User does not have a driver profile. Only drivers can update availability.",
			"error_code": "NO_DRIVER_PROFILE"
		}
	
	Response (Error - Missing Field):
		{
			"is_available": ["This field is required."]
		}
	"""
	
	permission_classes = [permissions.IsAuthenticated]
	
	def post(self, request):
		"""Toggle driver's availability status."""
		try:
			# Serialize and validate the request data
			serializer = DriverAvailabilitySerializer(
				data=request.data,
				context={'request': request}
			)
			
			if serializer.is_valid():
				# Save the updated availability status
				driver = serializer.save()
				
				# Get the response representation
				response_data = serializer.to_representation(driver)
				
				action = "online" if response_data['is_available'] else "offline"
				logger.info(f"Driver {driver.user.username} went {action}")
				
				return Response(response_data, status=status.HTTP_200_OK)
			
			# Return validation errors
			logger.warning(f"Availability toggle failed for user {request.user.username}: {serializer.errors}")
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
			
		except Exception as e:
			logger.error(f"Error toggling availability for user {request.user.username}: {str(e)}")
			return Response({
				'success': False,
				'message': 'An error occurred while updating availability',
				'error_code': 'INTERNAL_ERROR'
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
