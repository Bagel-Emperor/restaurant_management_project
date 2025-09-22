from django.shortcuts import render
from django.conf import settings
from django.core.mail import send_mail
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from django.db import transaction
from django.core.exceptions import ValidationError
import logging
from .forms import FeedbackForm, ContactSubmissionForm
from .models import Restaurant, MenuItem, MenuCategory
from .serializers import RestaurantSerializer, MenuItemSerializer, MenuCategorySerializer
from rest_framework.generics import ListAPIView

# Configure logger
logger = logging.getLogger(__name__)

# DRF API endpoint for listing all menu categories

class MenuCategoryListAPIView(ListAPIView):
    queryset = MenuCategory.objects.all()
    serializer_class = MenuCategorySerializer


class MenuItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing menu items with full CRUD operations.
    Provides proper authentication, validation, and error handling.
    
    - LIST: Get all menu items
    - CREATE: Add new menu item (admin only)
    - RETRIEVE: Get specific menu item by ID
    - UPDATE: Update menu item (admin only) 
    - PARTIAL_UPDATE: Partially update menu item (admin only)
    - DELETE: Delete menu item (admin only)
    """
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    
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
        Supports filtering by restaurant, availability, and category.
        """
        queryset = MenuItem.objects.all().select_related('restaurant', 'category')
        
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
    Args:
        request: The HTTP request object.
    Returns:
        HttpResponse: Rendered homepage with restaurant name and phone in context.
    """
    from .models import MenuItem
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
    context = {
        'restaurant_name': restaurant.name if restaurant else 'Our Restaurant',
        'restaurant_phone': restaurant.phone_number if restaurant else '',
        'menu_items': menu_items,
        'search_query': query,
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
            restaurant_email = getattr(settings, 'RESTAURANT_EMAIL', 'contact@perpexbistro.com')
            system_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@perpexbistro.com')
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
        'contact_email': 'contact@perpexbistro.com',
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
