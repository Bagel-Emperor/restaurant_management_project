# Reservations page view
def reservations_view(request):
    """
    View to render the reservations page (placeholder).
    """
    return render(request, 'home/reservations.html')
# Import the render function to display templates
from django.shortcuts import render
# Import settings to access RESTAURANT_NAME
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Restaurant, MenuItem
from .serializers import RestaurantSerializer, MenuItemSerializer
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
    menu_items = [
        {'name': 'Margherita Pizza', 'price': '12.99'},
        {'name': 'Caesar Salad', 'price': '8.99'},
        {'name': 'Grilled Salmon', 'price': '16.99'},
        {'name': 'Spaghetti Carbonara', 'price': '13.99'},
        {'name': 'Chocolate Lava Cake', 'price': '6.99'},
    ]
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
    context = {
        'restaurant_name': getattr(settings, 'RESTAURANT_NAME', 'Our Restaurant'),
        'restaurant_phone': getattr(settings, 'RESTAURANT_PHONE', ''),
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
    context = {
        'restaurant_name': getattr(settings, 'RESTAURANT_NAME', 'Our Restaurant'),
        'contact_email': 'contact@perpexbistro.com',
        'contact_phone': '(555) 123-4567',
        'contact_email': 'contact@perpexbistro.com',
        'contact_phone': getattr(settings, 'RESTAURANT_PHONE', '(555) 123-4567'),
        'contact_address': '123 Main Street, Cityville, USA',
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
