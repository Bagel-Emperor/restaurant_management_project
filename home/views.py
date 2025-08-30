
from django.shortcuts import render
from django.conf import settings
from django.core.mail import send_mail
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .forms import FeedbackForm, ContactSubmissionForm
from .models import Restaurant, MenuItem
from .serializers import RestaurantSerializer, MenuItemSerializer

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
    context = {
        'restaurant_name': getattr(settings, 'RESTAURANT_NAME', 'Our Restaurant'),
        'restaurant_phone': getattr(settings, 'RESTAURANT_PHONE', ''),
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
