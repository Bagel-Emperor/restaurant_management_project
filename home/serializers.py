from rest_framework import serializers
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Restaurant, RestaurantLocation, MenuItem, MenuCategory, ContactSubmission, Table, UserReview, Ingredient

# Serializer for MenuCategory
class MenuCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuCategory
        fields = ['id', 'name', 'description']


# Serializer for Ingredient
class IngredientSerializer(serializers.ModelSerializer):
    """
    Serializer for Ingredient model.
    
    Provides detailed information about ingredients including dietary flags
    (allergen, vegetarian, vegan) to help customers make informed choices.
    """
    class Meta:
        model = Ingredient
        fields = [
            'id',
            'name',
            'description',
            'is_allergen',
            'is_vegetarian',
            'is_vegan'
        ]
        read_only_fields = ['id']


class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = [
            'id',
            'name',
            'owner_name',
            'email',
            'phone_number',
            'address',
            'city',
            'created_at',
        ]
        read_only_fields = ['created_at']


class RestaurantInfoSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for restaurant information.
    
    Includes all relevant details about the restaurant including location data
    and opening hours. Designed for the restaurant-info endpoint that provides
    complete information about the restaurant.
    """
    # Include location fields from RestaurantLocation model
    address = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    zip_code = serializers.SerializerMethodField()
    full_address = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaurant
        fields = [
            'id',
            'name',
            'owner_name',
            'email',
            'phone_number',
            'opening_hours',
            'has_delivery',
            'address',
            'city',
            'state',
            'zip_code',
            'full_address',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_address(self, obj):
        """Get street address from related RestaurantLocation."""
        if hasattr(obj, 'location') and obj.location:
            return obj.location.address
        return None
    
    def get_city(self, obj):
        """Get city from related RestaurantLocation."""
        if hasattr(obj, 'location') and obj.location:
            return obj.location.city
        return None
    
    def get_state(self, obj):
        """Get state from related RestaurantLocation."""
        if hasattr(obj, 'location') and obj.location:
            return obj.location.state
        return None
    
    def get_zip_code(self, obj):
        """Get zip code from related RestaurantLocation."""
        if hasattr(obj, 'location') and obj.location:
            return obj.location.zip_code
        return None
    
    def get_full_address(self, obj):
        """Get formatted full address string."""
        if hasattr(obj, 'location') and obj.location:
            location = obj.location
            return f"{location.address}, {location.city}, {location.state} {location.zip_code}"
        return None

class MenuItemSerializer(serializers.ModelSerializer):
    """
    Serializer for MenuItem model.
    Converts MenuItem instances to JSON and validates input for creation/update.
    Includes custom validation for price and availability.
    """
    category_name = serializers.SerializerMethodField()
    
    class Meta:
        model = MenuItem
        fields = [
            'id',
            'name',
            'description',
            'price',
            'restaurant',
            'category',
            'category_name',
            'is_available',
            'image',
            'created_at',
        ]
        read_only_fields = ['created_at']
    
    def get_category_name(self, obj):
        """
        Get the category name, returning None if no category is assigned.
        """
        return obj.category.name if obj.category else None
    
    def validate_price(self, value):
        """
        Ensure price is a positive number.
        """
        if value <= 0:
            raise serializers.ValidationError("Price must be a positive number.")
        return value
    
    def validate_name(self, value):
        """
        Ensure name is not empty and has reasonable length.
        """
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Name cannot be empty.")
        if len(value.strip()) > 100:
            raise serializers.ValidationError("Name cannot exceed 100 characters.")
        return value.strip()


class ContactSubmissionSerializer(serializers.ModelSerializer):
    """
    Serializer for ContactSubmission model.
    Handles validation for contact form submissions via DRF API.
    Provides comprehensive validation for name, email, and message fields.
    """
    
    class Meta:
        model = ContactSubmission
        fields = ['id', 'name', 'email', 'message', 'submitted_at']
        read_only_fields = ['id', 'submitted_at']
    
    def validate_name(self, value):
        """
        Validate contact name field.
        Ensures name is present, not empty, and within reasonable length.
        """
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Name is required and cannot be empty.")
        
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long.")
        
        if len(value.strip()) > 100:
            raise serializers.ValidationError("Name cannot exceed 100 characters.")
        
        return value.strip()
    
    def validate_email(self, value):
        """
        Validate email field using Django's built-in email validation.
        Provides detailed error messages for invalid email formats.
        """
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Email is required.")
        
        # Use Django's built-in email validator
        try:
            validate_email(value)
        except DjangoValidationError:
            raise serializers.ValidationError("Please enter a valid email address.")
        
        return value.lower().strip()
    
    def validate_message(self, value):
        """
        Validate message field.
        Ensures message is present and within reasonable length limits.
        """
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Message is required and cannot be empty.")
        
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Message must be at least 10 characters long.")
        
        if len(value.strip()) > 2000:
            raise serializers.ValidationError("Message cannot exceed 2000 characters.")
        
        return value.strip()
    
    def create(self, validated_data):
        """
        Create and return a new ContactSubmission instance.
        """
        return ContactSubmission.objects.create(**validated_data)


class TableSerializer(serializers.ModelSerializer):
    """
    Serializer for Table model.
    Provides table information including number, capacity, location, and status.
    Includes computed fields for availability and human-readable status.
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    location_display = serializers.CharField(source='get_location_display', read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = Table
        fields = [
            'id',
            'number',
            'capacity',
            'location',
            'location_display',
            'status',
            'status_display',
            'is_active',
            'is_available',
            'description',
            'restaurant',
            'restaurant_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'is_available']
    
    def validate_number(self, value):
        """Validate table number is positive."""
        if value < 1:
            raise serializers.ValidationError("Table number must be positive.")
        return value
    
    def validate_capacity(self, value):
        """Validate table capacity is reasonable."""
        if value < 1:
            raise serializers.ValidationError("Table capacity must be at least 1.")
        if value > 20:
            raise serializers.ValidationError("Table capacity cannot exceed 20 seats.")
        return value
    
    def validate(self, data):
        """Custom validation for table data."""
        # Note: Table number uniqueness per restaurant is handled by the model's 
        # unique_together constraint, which provides proper database-level validation
        # and better error handling than duplicate serializer validation
        return data


class DailySpecialSerializer(serializers.ModelSerializer):
    """
    Serializer for daily specials menu items.
    Returns only essential information for displaying featured daily specials.
    Includes category name for better presentation.
    """
    category_name = serializers.SerializerMethodField()
    restaurant_name = serializers.SerializerMethodField()
    
    class Meta:
        model = MenuItem
        fields = [
            'id',
            'name',
            'description',
            'price',
            'category_name',
            'restaurant_name',
            'image',
            'is_available',
        ]
    
    def get_category_name(self, obj):
        """
        Get the category name for display.
        Returns None if no category is assigned.
        """
        return obj.category.name if obj.category else None
    
    def get_restaurant_name(self, obj):
        """
        Get the restaurant name for display.
        Useful for multi-restaurant systems.
        """
        return obj.restaurant.name if obj.restaurant else None


class UserReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for UserReview model.
    Handles creation and retrieval of user reviews for menu items.
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    
    class Meta:
        model = UserReview
        fields = [
            'id',
            'user',
            'user_username',
            'menu_item',
            'menu_item_name',
            'rating',
            'comment',
            'review_date',
        ]
        read_only_fields = ['id', 'user', 'user_username', 'menu_item_name', 'review_date']
    
    def validate_rating(self, value):
        """Validate rating is between 1 and 5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value
    
    def validate_comment(self, value):
        """Validate comment is not empty or just whitespace"""
        if not value or not value.strip():
            raise serializers.ValidationError("Comment cannot be empty")
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Comment must be at least 10 characters long")
        return value.strip()
    
    def validate_menu_item(self, value):
        """Validate menu item exists and is available"""
        if not value.is_available:
            raise serializers.ValidationError("Cannot review an unavailable menu item")
        return value
    
    def validate(self, data):
        """Validate that user hasn't already reviewed this menu item"""
        # Get user from context (set in view)
        user = self.context.get('request').user if self.context.get('request') else None
        menu_item = data.get('menu_item')
        
        # Only check for duplicates on create (not update)
        if not self.instance and user and menu_item:
            if UserReview.objects.filter(user=user, menu_item=menu_item).exists():
                raise serializers.ValidationError(
                    "You have already reviewed this menu item. Please update your existing review instead."
                )
        
        return data


class RestaurantOpeningHoursSerializer(serializers.ModelSerializer):
    """
    Serializer for restaurant opening hours.
    
    Returns only the opening hours information for the restaurant,
    formatted as a JSON object with days of the week as keys and
    opening/closing times as values.
    
    Example output:
    {
        "restaurant_name": "Perpex Bistro",
        "opening_hours": {
            "Monday": "9:00 AM - 10:00 PM",
            "Tuesday": "9:00 AM - 10:00 PM",
            "Wednesday": "9:00 AM - 10:00 PM",
            "Thursday": "9:00 AM - 11:00 PM",
            "Friday": "9:00 AM - 11:00 PM",
            "Saturday": "10:00 AM - 11:00 PM",
            "Sunday": "10:00 AM - 9:00 PM"
        }
    }
    """
    restaurant_name = serializers.CharField(source='name', read_only=True)
    
    class Meta:
        model = Restaurant
        fields = ['restaurant_name', 'opening_hours']
        read_only_fields = ['restaurant_name', 'opening_hours']


class MenuItemSearchSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for menu item search results.
    
    Returns only essential fields needed for frontend search functionality:
    - id: Menu item identifier for navigation/linking
    - name: Item name for display
    - image: Image URL for visual display (optional)
    
    This serializer is optimized for quick search responses and reduces
    payload size compared to the full MenuItemSerializer.
    
    Example Response:
    {
        "id": 1,
        "name": "Margherita Pizza",
        "image": "/media/menu_images/pizza.jpg"
    }
    """
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'image']
        read_only_fields = ['id', 'name', 'image']
    
    def get_image(self, obj):
        """
        Return the full URL for the image if it exists, otherwise None.
        """
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

