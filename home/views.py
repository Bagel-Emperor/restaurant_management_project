from django.shortcuts import render
from django.conf import settings
from django.core.mail import send_mail
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Q
import logging
from .forms import FeedbackForm, ContactSubmissionForm
from .models import Restaurant, MenuItem, MenuCategory, Cart, CartItem, ContactSubmission, Table, UserReview
from .serializers import (
    RestaurantSerializer,
    MenuItemSerializer,
    MenuCategorySerializer,
    ContactSubmissionSerializer,
    TableSerializer,
    DailySpecialSerializer,
    UserReviewSerializer,
)

# Email configuration constants
DEFAULT_RESTAURANT_EMAIL = 'contact@perpexbistro.com'
DEFAULT_SYSTEM_EMAIL = 'noreply@perpexbistro.com'
from .cart_utils import (
    get_or_create_cart, add_to_cart, remove_from_cart, 
    update_cart_item_quantity, clear_cart, get_cart_summary
)
from rest_framework.generics import ListAPIView, RetrieveAPIView

# Configure logger
logger = logging.getLogger(__name__)

# ================================
# MENU CATEGORY CRUD API
# ================================

class MenuCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for full CRUD operations on menu categories.
    
    Provides:
    - List all categories: GET /api/menu-categories/ (public)
    - Retrieve single category: GET /api/menu-categories/<id>/ (public)
    - Create new category: POST /api/menu-categories/ (authenticated only)
    - Update category: PUT/PATCH /api/menu-categories/<id>/ (authenticated only)
    - Delete category: DELETE /api/menu-categories/<id>/ (authenticated only)
    
    Permissions:
    - Read operations (list, retrieve) are public
    - Write operations (create, update, delete) require authentication
    """
    queryset = MenuCategory.objects.all().order_by('name')
    serializer_class = MenuCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def perform_create(self, serializer):
        """Custom create logic with audit logging."""
        serializer.save()
        logger.info('Created menu category: %s', serializer.instance.name)
    
    def perform_update(self, serializer):
        """Custom update logic with audit logging."""
        serializer.save()
        logger.info('Updated menu category: %s', serializer.instance.name)
    
    def perform_destroy(self, instance):
        """Custom delete logic with audit logging."""
        category_name = instance.name
        instance.delete()
        logger.info('Deleted menu category: %s', category_name)


class DailySpecialsAPIView(ListAPIView):
    """
    API endpoint to retrieve daily specials from the restaurant.
    
    Returns a list of menu items that are marked as daily specials and are currently available.
    Uses the DailySpecialSerializer to format the response with essential information
    for displaying featured items.
    
    - Public endpoint (no authentication required)
    - Filters for items where is_daily_special=True and is_available=True
    - Orders by creation date (newest first)
    - Returns only available daily specials
    
    Response Fields:
    - id: Menu item unique identifier
    - name: Item name
    - description: Item description
    - price: Item price
    - category_name: Category name for display
    - restaurant_name: Restaurant name for display
    - image: Item image URL (if available)
    - is_available: Availability status
    
    Example Response:
    [
        {
            "id": 1,
            "name": "Grilled Salmon Special",
            "description": "Fresh Atlantic salmon with seasonal vegetables",
            "price": "24.99",
            "category_name": "Main Course",
            "restaurant_name": "Perpex Bistro",
            "image": "/media/menu_images/salmon.jpg",
            "is_available": true
        }
    ]
    """
    serializer_class = DailySpecialSerializer
    permission_classes = [permissions.AllowAny]  # Public endpoint
    
    def get_queryset(self):
        """
        Filter menu items to return only daily specials that are available.
        Uses select_related to optimize database queries for category and restaurant.
        """
        return MenuItem.objects.filter(
            is_daily_special=True,
            is_available=True
        ).select_related('category', 'restaurant').order_by('-created_at')


class MenuItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing menu items with full CRUD operations and comprehensive search.
    Provides proper authentication, validation, error handling, and search functionality.
    
    - LIST: Get all menu items with optional search and filtering
    - CREATE: Add new menu item (admin only)
    - RETRIEVE: Get specific menu item by ID
    - UPDATE: Update menu item (admin only) 
    - PARTIAL_UPDATE: Partially update menu item (admin only)
    - DELETE: Delete menu item (admin only)
    
    Search Parameters:
    - search: Text search across name and description
    - category: Filter by category ID or name
    - restaurant: Filter by restaurant ID
    - available: Filter by availability (true/false)
    - min_price: Minimum price filter
    - max_price: Maximum price filter
    - ordering: Sort results (price, name, created_at, -price, -name, -created_at)
    """
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'created_at', 'category__name']
    ordering = ['-created_at']  # Default ordering by newest first
    
    def get_permissions(self):
        """
        Set permissions based on action.
        - Read operations (list, retrieve): Allow any user
        - Write operations (create, update, delete): Require admin/staff
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAdminUser]  # IsAdminUser includes authentication check
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Filter queryset based on query parameters.
        Supports filtering by restaurant, availability, category, and text search.
        Also supports price range filtering for comprehensive search functionality.
        """
        queryset = MenuItem.objects.all().select_related('restaurant', 'category')
        
        # Text search across name and description
        search_query = self.request.query_params.get('search', None)
        if search_query is not None and search_query.strip():
            # Use Q objects for complex OR search across multiple fields
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        # Filter by restaurant if provided
        restaurant_id = self.request.query_params.get('restaurant', None)
        if restaurant_id is not None:
            try:
                restaurant_id = int(restaurant_id)
                queryset = queryset.filter(restaurant_id=restaurant_id)
            except (ValueError, TypeError):
                # Return error response for invalid restaurant ID
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'restaurant': 'Invalid restaurant ID. Must be a valid integer.'})
        
        # Filter by category if provided
        category = self.request.query_params.get('category', None)
        if category is not None:
            # Try to parse as category ID first, then fall back to name filtering
            try:
                category_id = int(category)
                queryset = queryset.filter(category_id=category_id)
            except (ValueError, TypeError):
                # If not a valid integer, filter by category name (case-insensitive)
                queryset = queryset.filter(category__name__icontains=category)
        
        # Price range filtering
        min_price = self.request.query_params.get('min_price', None)
        if min_price is not None:
            try:
                min_price = float(min_price)
                queryset = queryset.filter(price__gte=min_price)
            except (ValueError, TypeError):
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'min_price': 'Invalid minimum price. Must be a valid number.'})
        
        max_price = self.request.query_params.get('max_price', None)
        if max_price is not None:
            try:
                max_price = float(max_price)
                queryset = queryset.filter(price__lte=max_price)
            except (ValueError, TypeError):
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'max_price': 'Invalid maximum price. Must be a valid number.'})
        
        # Filter by availability if provided
        is_available = self.request.query_params.get('available', None)
        if is_available is not None:
            if is_available.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(is_available=True)
            elif is_available.lower() in ['false', '0', 'no']:
                queryset = queryset.filter(is_available=False)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Handle menu item creation with proper error handling.
        """
        try:
            with transaction.atomic():
                menu_item = serializer.save()
                logger.info(f"Menu item '{menu_item.name}' created by user {self.request.user.username}")
        except ValidationError as e:
            logger.error(f"Validation error creating menu item: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating menu item: {str(e)}")
            raise
    
    def perform_update(self, serializer):
        """
        Handle menu item updates with proper error handling and logging.
        """
        try:
            with transaction.atomic():
                old_name = serializer.instance.name
                menu_item = serializer.save()
                logger.info(f"Menu item '{old_name}' updated to '{menu_item.name}' by user {self.request.user.username}")
        except ValidationError as e:
            logger.error(f"Validation error updating menu item: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating menu item: {str(e)}")
            raise
    
    def perform_destroy(self, instance):
        """
        Handle menu item deletion with proper logging.
        """
        try:
            name = instance.name
            instance.delete()
            logger.info(f"Menu item '{name}' deleted by user {self.request.user.username}")
        except Exception as e:
            logger.error(f"Error deleting menu item: {str(e)}")
            raise
    
    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAdminUser])
    def toggle_availability(self, request, pk=None):
        """
        Custom action to toggle the availability of a menu item.
        PATCH /api/menu-items/{id}/toggle_availability/
        """
        try:
            menu_item = self.get_object()
            menu_item.is_available = not menu_item.is_available
            menu_item.save()
            
            status_text = "available" if menu_item.is_available else "unavailable"
            logger.info(f"Menu item '{menu_item.name}' marked as {status_text} by user {request.user.username}")
            
            serializer = self.get_serializer(menu_item)
            return Response({
                'message': f'Menu item is now {status_text}',
                'menu_item': serializer.data
            })
        except Exception as e:
            logger.error(f"Error toggling menu item availability: {str(e)}")
            return Response(
                {'error': 'Unable to toggle availability'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAdminUser])
    def update_availability(self, request, pk=None):
        """
        Custom action to update the availability of a menu item to a specific value.
        
        This endpoint allows explicitly setting the availability status to true or false,
        unlike toggle_availability which just flips the current state.
        
        PATCH /api/menu-items/{id}/update_availability/
        
        Request Body:
            {
                "is_available": true  // or false
            }
        
        Returns:
            Success: {
                "success": true,
                "message": "Menu item availability updated successfully",
                "menu_item": {menu_item_data}
            }
            
            Failure: {
                "success": false,
                "error": "Error message"
            }
        
        Error Handling:
            - 400: Missing or invalid is_available field
            - 404: Menu item not found (raised by get_object())
            - 500: Server error during update
        """
        # Error message constant to avoid duplication
        INVALID_BOOLEAN_ERROR = 'is_available must be a boolean (true or false)'
        
        try:
            # Validate that is_available field is present
            if 'is_available' not in request.data:
                logger.warning(f"Update availability attempt for menu item {pk} without is_available field")
                return Response(
                    {
                        'success': False,
                        'error': 'is_available field is required'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the is_available value
            is_available = request.data.get('is_available')
            
            # Validate that is_available is a boolean
            if not isinstance(is_available, bool):
                # Handle string representations of boolean
                if isinstance(is_available, str):
                    is_available_lower = is_available.lower()
                    if is_available_lower == 'true':
                        is_available = True
                    elif is_available_lower == 'false':
                        is_available = False
                    else:
                        logger.warning(
                            f"Invalid is_available value for menu item {pk}: {is_available}"
                        )
                        return Response(
                            {
                                'success': False,
                                'error': INVALID_BOOLEAN_ERROR
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )
                else:
                    logger.warning(
                        f"Invalid is_available type for menu item {pk}: {type(is_available)}"
                    )
                    return Response(
                        {
                            'success': False,
                            'error': INVALID_BOOLEAN_ERROR
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Get the menu item (raises Http404 if not found, handled by DRF)
            menu_item = self.get_object()
            
            # Store old value for logging
            old_value = menu_item.is_available
            
            # Update availability
            menu_item.is_available = is_available
            menu_item.save()
            
            # Log the change
            status_text = "available" if is_available else "unavailable"
            logger.info(
                f"Menu item '{menu_item.name}' (ID: {menu_item.id}) availability updated "
                f"from {old_value} to {is_available} by user {request.user.username}"
            )
            
            # Serialize and return
            serializer = self.get_serializer(menu_item)
            return Response(
                {
                    'success': True,
                    'message': f'Menu item availability updated successfully. Item is now {status_text}.',
                    'menu_item': serializer.data
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            # Catch any unexpected errors (get_object() Http404 is handled by DRF)
            logger.error(f"Error updating menu item availability for ID {pk}: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': 'Unable to update availability. Please try again later.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

def feedback_view(request):
    """
    View to handle feedback form submissions and render the feedback page.
    """
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'home/feedback.html', {'form': FeedbackForm(), 'success': True})
    else:
        form = FeedbackForm()
    return render(request, 'home/feedback.html', {'form': form})

def faq_view(request):
    """
    View to render the FAQ page with hardcoded questions and answers.
    """
    return render(request, 'home/faq.html')

# Reservations page view (restored)
def reservations_view(request):
    """
    View to render the reservations page (placeholder).
    """
    return render(request, 'home/reservations.html')

# --- MENU ITEM API CRUD VIEWS (one per method, as per assignment style) ---

@api_view(['POST'])
def create_menu_item(request):
    """
    Add a new menu item.
    """
    serializer = MenuItemSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def list_menu_items(request):
    """
    List all menu items, optionally filtered by restaurant ID (?restaurant=<id>).
    """
    restaurant_id = request.GET.get('restaurant')
    if restaurant_id:
        menu_items = MenuItem.objects.filter(restaurant_id=restaurant_id)
    else:
        menu_items = MenuItem.objects.all()
    serializer = MenuItemSerializer(menu_items, many=True)
    restaurant_id = request.GET.get('restaurant')
    if restaurant_id:
        try:
            restaurant_id_int = int(restaurant_id)
        except (ValueError, TypeError):
            return Response({'detail': 'Invalid restaurant id.'}, status=status.HTTP_400_BAD_REQUEST)
        menu_items = MenuItem.objects.filter(restaurant_id=restaurant_id_int)
    else:
        menu_items = MenuItem.objects.all()
    serializer = MenuItemSerializer(menu_items, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_menu_item(request, pk):
    """
    Retrieve a specific menu item by ID.
    """
    try:
        menu_item = MenuItem.objects.get(pk=pk)
    except MenuItem.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    serializer = MenuItemSerializer(menu_item)
    return Response(serializer.data)

@api_view(['PUT'])
def update_menu_item(request, pk):
    """
    Update a menu item by ID.
    """
    try:
        menu_item = MenuItem.objects.get(pk=pk)
    except MenuItem.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    serializer = MenuItemSerializer(menu_item, data=request.data, partial=False)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def delete_menu_item(request, pk):
    """
    Delete a menu item by ID.
    """
    try:
        menu_item = MenuItem.objects.get(pk=pk)
    except MenuItem.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    menu_item.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

# Menu page view
def menu_view(request):
    """
    View to render the menu page with a hardcoded list of menu items.
    Args:
        request: The HTTP request object.
    Returns:
        HttpResponse: Rendered menu page with menu items in context.
    """
    from .models import MenuItem
    menu_items = MenuItem.objects.filter(is_available=True)
    context = {
        'menu_items': menu_items,
    }
    return render(request, 'home/menu.html', context)

# This view renders the homepage using our new styled template
def home_view(request):
    """
    View to render the homepage with the restaurant's name and phone number from settings.
    Also includes shopping cart information for the current user/session.
    Args:
        request: The HTTP request object.
    Returns:
        HttpResponse: Rendered homepage with restaurant name, phone, and cart info in context.
    """
    query = request.GET.get('q', '').strip()
    # Input validation: limit query length and ignore empty/overly long queries
    MAX_QUERY_LENGTH = 50
    if len(query) > MAX_QUERY_LENGTH:
        query = ''
    menu_items = MenuItem.objects.filter(is_available=True)
    if query:
        menu_items = menu_items.filter(name__icontains=query)
    
    # Fetch the first Restaurant instance for homepage info
    restaurant = Restaurant.objects.first()
    
    # Get cart information for current user/session
    cart = get_or_create_cart(request)
    cart_total_items = cart.total_items
    
    context = {
        'restaurant_name': restaurant.name if restaurant else 'Our Restaurant',
        'restaurant_phone': restaurant.phone_number if restaurant else '',
        'menu_items': menu_items,
        'search_query': query,
        'cart_total_items': cart_total_items,  # This is the main requirement
    }
    return render(request, 'home/index.html', context)

# Custom 404 error handler view
def custom_404_view(request, exception):
	"""
	Custom view to render the 404 error page using the 404.html template.
	Args:
		request: The HTTP request object.
		exception: The exception that triggered the 404.
	Returns:
		HttpResponse: Rendered 404 error page.
	"""
	return render(request, 'home/404.html', status=404)
    
# About page view
def about_view(request):
    """
    View to render the about page for the restaurant.
    Args:
        request: The HTTP request object.
    Returns:
        HttpResponse: Rendered about page.
    """
    context = {
        'restaurant_name': getattr(settings, 'RESTAURANT_NAME', 'Our Restaurant'),
        'restaurant_description': (
            'Perpex Bistro is a modern restaurant dedicated to providing a delightful dining experience. '
            'Our menu features a blend of classic and contemporary dishes, crafted with fresh, local ingredients. '
            'Whether you\'re here for a quick lunch or a special dinner, we strive to make every visit memorable.'
        ),
    }
    return render(request, 'home/about.html', context)

# Contact page view
def contact_view(request):
    """
    View to render the contact page for the restaurant.
    Args:
        request: The HTTP request object.
    Returns:
        HttpResponse: Rendered contact page.
    """
    success = False
    if request.method == 'POST':
        form = ContactSubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save()
            # Send email notification to restaurant
            restaurant_email = getattr(settings, 'RESTAURANT_EMAIL', DEFAULT_RESTAURANT_EMAIL)
            system_email = getattr(settings, 'DEFAULT_FROM_EMAIL', DEFAULT_SYSTEM_EMAIL)
            subject = f"New Contact Submission from {submission.name}"
            message = f"Name: {submission.name}\nEmail: {submission.email}\nMessage: {submission.message}"
            send_mail(
                subject,
                message,
                system_email,  # from email
                [restaurant_email],  # to email
                fail_silently=True,
            )
            success = True
            form = ContactSubmissionForm()  # Reset form after success
    else:
        form = ContactSubmissionForm()
    context = {
        'restaurant_name': getattr(settings, 'RESTAURANT_NAME', 'Our Restaurant'),
        'contact_email': getattr(settings, 'RESTAURANT_EMAIL', DEFAULT_RESTAURANT_EMAIL),
        'contact_phone': getattr(settings, 'RESTAURANT_PHONE', '(555) 123-4567'),
        'contact_address': '123 Main Street, Cityville, USA',
        'form': form,
        'success': success,
    }
    return render(request, 'home/contact.html', context)

# --- RESTAURANT API CRUD VIEWS (one per method, as per assignment style) ---
@api_view(['POST'])
def create_restaurant(request):
    """
    Register a new restaurant.
    """
    serializer = RestaurantSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def list_restaurants(request):
    """
    List all restaurants.
    """
    restaurants = Restaurant.objects.all()
    serializer = RestaurantSerializer(restaurants, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_restaurant(request, pk):
    """
    Retrieve a restaurant by ID.
    """
    try:
        restaurant = Restaurant.objects.get(pk=pk)
    except Restaurant.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    serializer = RestaurantSerializer(restaurant)
    return Response(serializer.data)

@api_view(['PUT'])
def update_restaurant(request, pk):
    """
    Update a restaurant by ID.
    """
    try:
        restaurant = Restaurant.objects.get(pk=pk)
    except Restaurant.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    serializer = RestaurantSerializer(restaurant, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def restaurant_info(request):
    """
    Retrieve comprehensive information about the restaurant.
    
    Returns all relevant information including name, address, phone number,
    opening hours, and other important details about the restaurant.
    
    This endpoint is designed to provide complete information about the main
    restaurant (Perpex Bistro) for display on the frontend or mobile apps.
    
    GET /api/restaurant-info/
    
    Returns:
        200 OK: {
            "success": true,
            "restaurant": {
                "id": 1,
                "name": "Perpex Bistro",
                "owner_name": "John Doe",
                "email": "contact@perpexbistro.com",
                "phone_number": "555-0100",
                "opening_hours": {
                    "Monday": "9:00 AM - 10:00 PM",
                    "Tuesday": "9:00 AM - 10:00 PM",
                    ...
                },
                "address": "123 Main Street",
                "city": "New York",
                "state": "NY",
                "zip_code": "10001",
                "full_address": "123 Main Street, New York, NY 10001",
                "created_at": "2025-01-01T00:00:00Z"
            }
        }
        
        404 Not Found: {
            "success": false,
            "error": "Restaurant information not found. Please contact support."
        }
        
        500 Internal Server Error: {
            "success": false,
            "error": "Unable to retrieve restaurant information. Please try again later."
        }
    
    Features:
    - Public endpoint (no authentication required)
    - Returns the first restaurant in the database (main restaurant)
    - Includes location details from RestaurantLocation model
    - Properly formatted opening hours JSON
    - Full address string for easy display
    - Comprehensive error handling
    - Logging for debugging
    
    Usage Example:
        response = requests.get('http://localhost:8000/PerpexBistro/api/restaurant-info/')
        data = response.json()
        if data['success']:
            restaurant = data['restaurant']
            print(f"Name: {restaurant['name']}")
            print(f"Phone: {restaurant['phone_number']}")
            print(f"Address: {restaurant['full_address']}")
    """
    try:
        # Get the first/main restaurant
        # In a single-restaurant setup, this returns the main restaurant
        restaurant = Restaurant.objects.select_related('location').first()
        
        if not restaurant:
            logger.warning("Restaurant information requested but no restaurant exists in database")
            return Response(
                {
                    'success': False,
                    'error': 'Restaurant information not found. Please contact support.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Serialize the restaurant data
        from .serializers import RestaurantInfoSerializer
        serializer = RestaurantInfoSerializer(restaurant)
        
        logger.info(f"Restaurant information retrieved successfully for: {restaurant.name}")
        
        return Response(
            {
                'success': True,
                'restaurant': serializer.data
            },
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error retrieving restaurant information: {str(e)}")
        return Response(
            {
                'success': False,
                'error': 'Unable to retrieve restaurant information. Please try again later.'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =============================================================================
# Shopping Cart API Endpoints
# =============================================================================

@api_view(['GET'])
def cart_summary(request):
    """
    Get the current cart summary for the user/session.
    
    Returns:
        dict: Cart information including items, totals, and metadata
    """
    result = get_cart_summary(request)
    if result['success']:
        return Response(result, status=status.HTTP_200_OK)
    return Response(result, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def add_to_cart_api(request):
    """
    Add a menu item to the cart.
    
    Expected data:
        - menu_item_id: ID of the menu item to add
        - quantity: Quantity to add (optional, defaults to 1)
    
    Returns:
        dict: Success/error message and updated cart info
    """
    menu_item_id = request.data.get('menu_item_id')
    quantity = request.data.get('quantity', 1)
    
    if not menu_item_id:
        return Response({'success': False, 'error': 'menu_item_id is required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        return Response({'success': False, 'error': 'Invalid quantity'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    result = add_to_cart(request, menu_item_id, quantity)
    if result['success']:
        return Response(result, status=status.HTTP_200_OK)
    return Response(result, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def remove_from_cart_api(request, menu_item_id):
    """
    Remove a menu item from the cart completely.
    
    Args:
        menu_item_id: ID of the menu item to remove
    
    Returns:
        dict: Success/error message and updated cart info
    """
    result = remove_from_cart(request, menu_item_id)
    if result['success']:
        return Response(result, status=status.HTTP_200_OK)
    return Response(result, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def update_cart_item_api(request, menu_item_id):
    """
    Update the quantity of a cart item.
    
    Expected data:
        - quantity: New quantity (if 0, item will be removed)
    
    Args:
        menu_item_id: ID of the menu item to update
    
    Returns:
        dict: Success/error message and updated cart info
    """
    quantity = request.data.get('quantity')
    
    if quantity is None:
        return Response({'success': False, 'error': 'quantity is required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        return Response({'success': False, 'error': 'Invalid quantity'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    result = update_cart_item_quantity(request, menu_item_id, quantity)
    if result['success']:
        return Response(result, status=status.HTTP_200_OK)
    return Response(result, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def clear_cart_api(request):
    """
    Clear all items from the cart.
    
    Returns:
        dict: Success/error message
    """
    result = clear_cart(request)
    if result['success']:
        return Response(result, status=status.HTTP_200_OK)
    return Response(result, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def delete_restaurant(request, pk):
    """
    Delete a restaurant by ID.
    """
    try:
        restaurant = Restaurant.objects.get(pk=pk)
    except Restaurant.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    restaurant.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# Contact Form API Views
class ContactSubmissionCreateAPIView(CreateAPIView):
    """
    DRF API view for creating contact form submissions.
    
    Accepts POST requests with contact form data (name, email, message)
    and creates a new ContactSubmission record in the database.
    
    Features:
    - Comprehensive input validation via ContactSubmissionSerializer
    - Email sending functionality to restaurant
    - Detailed error handling and logging
    - No authentication required (public endpoint)
    """
    queryset = ContactSubmission.objects.all()
    serializer_class = ContactSubmissionSerializer
    permission_classes = [permissions.AllowAny]  # Public endpoint
    
    def perform_create(self, serializer):
        """
        Save the contact submission and send email notification.
        """
        # Save the submission to database
        submission = serializer.save()
        
        # Log the submission
        logger.info(f"New contact submission from {submission.email}")
        
        # Send email notification to restaurant
        try:
            restaurant_email = getattr(settings, 'RESTAURANT_EMAIL', DEFAULT_RESTAURANT_EMAIL)
            system_email = getattr(settings, 'DEFAULT_FROM_EMAIL', DEFAULT_SYSTEM_EMAIL)
            
            subject = f"New Contact Submission from {submission.name}"
            message = f"Name: {submission.name}\nEmail: {submission.email}\nMessage: {submission.message}"
            
            send_mail(
                subject,
                message,
                system_email,  # from email
                [restaurant_email],  # to email
                fail_silently=False,
            )
            logger.info(f"Contact form email sent successfully for submission {submission.id}")
            
        except Exception as e:
            # Log email error but don't fail the API request
            logger.error(f"Failed to send contact form email for submission {submission.id}: {str(e)}")
    
    def create(self, request, *args, **kwargs):
        """
        Override create method to provide custom response messages.
        """
        response = super().create(request, *args, **kwargs)
        
        # Customize success response
        if response.status_code == 201:
            response.data.update({
                'message': 'Thank you for your message! We will get back to you soon.',
                'success': True
            })
        
        return response


# ================================
# TABLE MANAGEMENT API VIEWS
# ================================

class TableListAPIView(ListAPIView):
    """
    API view for listing all tables.
    
    Provides a list of all restaurant tables with their details including:
    - Table number and capacity
    - Current status and availability
    - Location within restaurant
    - Restaurant information
    
    Supports filtering by:
    - status: Filter by table status (available, occupied, reserved, maintenance)
    - capacity: Filter by minimum capacity
    - location: Filter by table location (indoor, outdoor, patio, etc.)
    - restaurant: Filter by restaurant ID
    
    Example usage:
    - GET /api/tables/ - List all tables
    - GET /api/tables/?status=available - List available tables only
    - GET /api/tables/?capacity=4 - List tables with 4+ capacity
    """
    queryset = Table.objects.all().select_related('restaurant')
    serializer_class = TableSerializer
    
    def get_queryset(self):
        """
        Filter queryset based on query parameters.
        """
        queryset = super().get_queryset()
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by minimum capacity
        capacity = self.request.query_params.get('capacity')
        if capacity:
            try:
                capacity = int(capacity)
                queryset = queryset.filter(capacity__gte=capacity)
            except ValueError:
                pass  # Ignore invalid capacity values
        
        # Filter by location
        location = self.request.query_params.get('location')
        if location:
            queryset = queryset.filter(location=location)
        
        # Filter by restaurant
        restaurant_id = self.request.query_params.get('restaurant')
        if restaurant_id:
            try:
                restaurant_id = int(restaurant_id)
                queryset = queryset.filter(restaurant_id=restaurant_id)
            except ValueError:
                pass  # Ignore invalid restaurant IDs
        
        # Filter by active status
        if self.request.query_params.get('active_only', '').lower() == 'true':
            queryset = queryset.filter(is_active=True)
        
        return queryset.order_by('number')


class TableDetailAPIView(RetrieveAPIView):
    """
    API view for retrieving a single table's details.
    
    Provides detailed information about a specific table including:
    - Complete table information (number, capacity, location)
    - Current status and availability
    - Restaurant details
    - Creation and update timestamps
    
    The table is identified by its primary key (ID) in the URL.
    
    Example usage:
    - GET /api/tables/1/ - Get details for table with ID 1
    
    Returns 404 if table doesn't exist.
    """
    queryset = Table.objects.all().select_related('restaurant')
    serializer_class = TableSerializer
    
    def get_object(self):
        """
        Override to add custom error handling and logging.
        """
        try:
            obj = super().get_object()
            logger.info(f"Table {obj.number} details accessed")
            return obj
        except Table.DoesNotExist:
            logger.warning(f"Table with ID {self.kwargs['pk']} not found")
            raise


class AvailableTablesAPIView(ListAPIView):
    """
    API view for retrieving only available tables.
    
    This endpoint provides a filtered list of tables that are currently available
    for reservation or seating. A table is considered available when:
    - status is 'available' 
    - is_active is True
    
    This is essential for reservation systems and real-time table management.
    
    Provides information including:
    - Table number and capacity
    - Location within restaurant  
    - Restaurant details
    - Availability status confirmation
    
    Supports additional filtering:
    - capacity: Minimum capacity required (e.g., ?capacity=4)
    - location: Filter by location type (e.g., ?location=outdoor)
    - restaurant: Filter by specific restaurant ID (e.g., ?restaurant=1)
    
    Example usage:
    - GET /api/tables/available/ - List all available tables
    - GET /api/tables/available/?capacity=4 - Available tables for 4+ people
    - GET /api/tables/available/?location=outdoor - Available outdoor tables
    - GET /api/tables/available/?restaurant=1&capacity=2 - Available tables for 2+ at restaurant 1
    
    Returns paginated results with table details in JSON format.
    """
    serializer_class = TableSerializer
    
    def get_queryset(self):
        """
        Return only tables that are currently available.
        Also supports additional filtering by capacity, location, and restaurant.
        """
        # Base queryset: only available tables
        queryset = Table.objects.filter(
            status='available',
            is_active=True
        ).select_related('restaurant')
        
        # Additional filtering options
        capacity = self.request.query_params.get('capacity')
        if capacity:
            try:
                capacity = int(capacity)
                queryset = queryset.filter(capacity__gte=capacity)
                logger.info(f"Filtering available tables by capacity >= {capacity}")
            except ValueError:
                logger.warning(f"Invalid capacity parameter: {capacity}")
        
        location = self.request.query_params.get('location')
        if location:
            queryset = queryset.filter(location=location)
            logger.info(f"Filtering available tables by location: {location}")
        
        restaurant_id = self.request.query_params.get('restaurant')
        if restaurant_id:
            try:
                restaurant_id = int(restaurant_id)
                queryset = queryset.filter(restaurant_id=restaurant_id)
                logger.info(f"Filtering available tables by restaurant ID: {restaurant_id}")
            except ValueError:
                logger.warning(f"Invalid restaurant parameter: {restaurant_id}")
        
        # Log the query count only in debug mode to avoid performance overhead
        if settings.DEBUG:
            available_count = queryset.count()
            logger.info(f"Available tables query returned {available_count} tables")
        
        return queryset.order_by('restaurant__name', 'number')


# ================================
# USER REVIEWS API
# ================================

class UserReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint for full CRUD operations on user reviews.
    
    Provides:
    - List all reviews: GET /api/reviews/ (public, supports filtering by menu_item)
    - Retrieve single review: GET /api/reviews/<id>/ (public)
    - Create new review: POST /api/reviews/ (authenticated only)
    - Update review: PUT/PATCH /api/reviews/<id>/ (authenticated, own reviews only)
    - Delete review: DELETE /api/reviews/<id>/ (authenticated, own reviews only)
    
    Authentication:
    - Read operations (list, retrieve): Public access
    - Write operations (create, update, delete): Authenticated users only
    - Users can only update/delete their own reviews
    
    Filtering:
    - Filter by menu_item: GET /api/reviews/?menu_item=<menu_item_id>
    - Filter by rating: GET /api/reviews/?rating=5
    - Filter by user: GET /api/reviews/?user=<user_id>
    
    Validation:
    - Rating must be between 1 and 5
    - Comment must be at least 10 characters
    - Users can only review each menu item once
    - Menu item must be available for review
    """
    queryset = UserReview.objects.select_related('user', 'menu_item').all()
    serializer_class = UserReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """
        Filter reviews by menu_item, rating, or user if provided in query params.
        """
        queryset = super().get_queryset()
        
        # Filter by menu_item
        menu_item_id = self.request.query_params.get('menu_item')
        if menu_item_id:
            queryset = queryset.filter(menu_item_id=menu_item_id)
            logger.info('Filtered reviews for menu_item ID: %s', menu_item_id)
        
        # Filter by rating
        rating = self.request.query_params.get('rating')
        if rating:
            try:
                rating_int = int(rating)
                queryset = queryset.filter(rating=rating_int)
                logger.info('Filtered reviews by rating: %s', rating_int)
            except ValueError:
                logger.warning('Invalid rating parameter: %s', rating)
        
        # Filter by user
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            logger.info('Filtered reviews by user ID: %s', user_id)
        
        return queryset.order_by('-review_date')
    
    def perform_create(self, serializer):
        """
        Automatically set the user to the authenticated user when creating a review.
        """
        user = self.request.user
        menu_item = serializer.validated_data['menu_item']
        serializer.save(user=user)
        logger.info('User %s created review for menu item: %s', user.username, menu_item.name)
    
    def perform_update(self, serializer):
        """
        Log when a review is updated.
        """
        review = serializer.instance
        logger.info('User %s updated review ID: %s', self.request.user.username, review.id)
        serializer.save()
    
    def perform_destroy(self, instance):
        """
        Log when a review is deleted.
        """
        logger.info('User %s deleted review ID: %s', self.request.user.username, instance.id)
        instance.delete()
    
    def update(self, request, *args, **kwargs):
        """
        Ensure users can only update their own reviews.
        """
        instance = self.get_object()
        if instance.user != request.user:
            logger.warning('User %s attempted to update review owned by %s', 
                         request.user.username, instance.user.username)
            return Response(
                {"detail": "You can only update your own reviews."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        """
        Ensure users can only partially update their own reviews.
        """
        instance = self.get_object()
        if instance.user != request.user:
            logger.warning('User %s attempted to update review owned by %s', 
                         request.user.username, instance.user.username)
            return Response(
                {"detail": "You can only update your own reviews."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """
        Ensure users can only delete their own reviews.
        """
        instance = self.get_object()
        if instance.user != request.user:
            logger.warning('User %s attempted to delete review owned by %s', 
                         request.user.username, instance.user.username)
            return Response(
                {"detail": "You can only delete your own reviews."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_reviews(self, request):
        """
        Custom action to get all reviews by the authenticated user.
        Endpoint: GET /api/reviews/my_reviews/
        """
        user_reviews = self.get_queryset().filter(user=request.user)
        page = self.paginate_queryset(user_reviews)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(user_reviews, many=True)
        logger.info('User %s retrieved their reviews', request.user.username)
        return Response(serializer.data)

