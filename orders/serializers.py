from rest_framework import serializers
from django.contrib.auth.models import User, BaseUserManager
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count
from .models import Customer, Order, OrderItem, OrderStatus, UserProfile, Rider, Driver, Ride
from home.models import MenuItem
from decimal import Decimal


# Shared validation helpers
def validate_coordinates(pickup_lat, pickup_lng, drop_lat, drop_lng):
    """
    Validate ride coordinates for proper ranges and uniqueness.
    
    Uses Decimal comparison to preserve precision and avoid float artifacts.
    Consolidates validation logic used across serializers and model clean methods.
    
    Args:
        pickup_lat: Pickup latitude (Decimal or numeric)
        pickup_lng: Pickup longitude (Decimal or numeric)
        drop_lat: Dropoff latitude (Decimal or numeric)
        drop_lng: Dropoff longitude (Decimal or numeric)
        
    Returns:
        dict: Validation errors (empty if valid)
    """
    errors = {}
    
    # Convert to Decimal if not already
    pickup_lat = Decimal(str(pickup_lat))
    pickup_lng = Decimal(str(pickup_lng))
    drop_lat = Decimal(str(drop_lat))
    drop_lng = Decimal(str(drop_lng))
    
    # Validate latitude ranges
    if not (Decimal('-90') <= pickup_lat <= Decimal('90')):
        errors['pickup_lat'] = 'Latitude must be between -90 and 90'
    
    if not (Decimal('-90') <= drop_lat <= Decimal('90')):
        errors['drop_lat'] = 'Latitude must be between -90 and 90'
    
    # Validate longitude ranges
    if not (Decimal('-180') <= pickup_lng <= Decimal('180')):
        errors['pickup_lng'] = 'Longitude must be between -180 and 180'
    
    if not (Decimal('-180') <= drop_lng <= Decimal('180')):
        errors['drop_lng'] = 'Longitude must be between -180 and 180'
    
    # Validate pickup and dropoff are different
    if pickup_lat == drop_lat and pickup_lng == drop_lng:
        errors['non_field_errors'] = 'Pickup and dropoff locations must be different'
    
    return errors


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'phone', 'email', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_email(self, value):
        """Validate email using Django's built-in email validation"""
        if value:
            # Normalize the email using Django's built-in method
            value = BaseUserManager.normalize_email(value)
            
            # Validate email format using Django's built-in validator
            email_validator = EmailValidator()
            try:
                email_validator(value)
            except DjangoValidationError as e:
                raise serializers.ValidationError(str(e))
        
        return value


class MenuItemSerializer(serializers.ModelSerializer):
    """Serializer for MenuItem used in order items"""
    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'price']


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem with nested MenuItem details"""
    menu_item = MenuItemSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'menu_item', 'quantity', 'price', 'total_price']
    
    def get_total_price(self, obj):
        return obj.quantity * obj.price


class OrderStatusSerializer(serializers.ModelSerializer):
    """Serializer for OrderStatus"""
    class Meta:
        model = OrderStatus
        fields = ['id', 'name']


# Serializer for listing orders
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'order_id', 'status', 'total_amount', 'created_at']
        read_only_fields = ['id', 'order_id', 'created_at']


class OrderHistorySerializer(serializers.ModelSerializer):
    """Comprehensive serializer for user order history with nested items"""
    order_items = OrderItemSerializer(many=True, read_only=True)
    status = OrderStatusSerializer(read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['id', 'order_id', 'created_at', 'total_amount', 'status', 'items_count', 'order_items']
        read_only_fields = ['id', 'order_id', 'created_at', 'total_amount']
    
    def get_items_count(self, obj):
        return obj.order_items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for individual order retrieval.
    Includes comprehensive order information, customer details, and order items.
    """
    order_items = OrderItemSerializer(many=True, read_only=True)
    status = OrderStatusSerializer(read_only=True)
    customer = CustomerSerializer(read_only=True)
    
    # Computed fields
    items_count = serializers.SerializerMethodField()
    order_total = serializers.SerializerMethodField()
    customer_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_id', 'created_at', 'total_amount', 'status', 
            'customer', 'customer_info', 'items_count', 
            'order_total', 'order_items'
        ]
        read_only_fields = ['id', 'created_at', 'total_amount']
    
    def get_items_count(self, obj):
        """Get the total number of items in the order"""
        return obj.order_items.count()
    
    def get_order_total(self, obj):
        """Get formatted total amount"""
        return f"${obj.total_amount:.2f}"
    
    def get_customer_info(self, obj):
        """Get customer information with fallback to user info"""
        if obj.customer:
            return {
                'type': 'guest',
                'name': obj.customer.name,
                'phone': obj.customer.phone,
                'email': obj.customer.email
            }
        elif obj.user:
            return {
                'type': 'registered',
                'name': obj.user.get_full_name() or obj.user.username,
                'email': obj.user.email,
                'username': obj.user.username
            }
        else:
            return {
                'type': 'unknown',
                'name': 'Guest Customer'
            }


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile with nested User fields.
    Allows updating both UserProfile and related User information.
    """
    # User fields that can be updated
    first_name = serializers.CharField(source='user.first_name', max_length=150, allow_blank=True)
    last_name = serializers.CharField(source='user.last_name', max_length=150, allow_blank=True)
    email = serializers.EmailField(source='user.email')
    username = serializers.CharField(source='user.username', read_only=True)
    
    # UserProfile fields
    name = serializers.CharField(max_length=100, allow_blank=True)
    phone = serializers.CharField(max_length=20, allow_blank=True)
    
    # Computed field
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'name', 'phone', 'full_name']
        read_only_fields = ['id', 'username', 'full_name']
    
    def validate_email(self, value):
        """Validate email using Django's built-in email validation"""
        if value:
            # Normalize the email using Django's built-in method
            value = BaseUserManager.normalize_email(value)
            
            # Validate email format using Django's built-in validator
            email_validator = EmailValidator()
            try:
                email_validator(value)
            except DjangoValidationError as e:
                raise serializers.ValidationError(str(e))
            
            # Check if email is already taken by another user
            user = self.instance.user if self.instance else None
            if User.objects.filter(email=value).exclude(pk=user.pk if user else None).exists():
                raise serializers.ValidationError("A user with this email already exists.")
        
        return value
    
    def update(self, instance, validated_data):
        """
        Update both UserProfile and related User fields.
        """
        # Extract user data from validated_data
        user_data = validated_data.pop('user', {})
        
        # Update User fields
        user = instance.user
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()
        
        # Update UserProfile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance
    
    def get_full_name(self, obj):
        """
        Compute the full name from User's first/last name, fallback to profile name or username.
        """
        return obj.user.get_full_name() or obj.name or obj.user.username


# ================================
# REGISTRATION SERIALIZERS
# ================================

class RiderRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for rider registration.
    
    Creates both a Django User and a Rider profile with comprehensive validation.
    Handles password hashing, email uniqueness, and rider-specific fields.
    """
    
    # User fields
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    
    # Rider-specific fields
    phone = serializers.CharField(max_length=17)
    preferred_payment = serializers.ChoiceField(
        choices=[
            ('card', 'Credit/Debit Card'),
            ('cash', 'Cash'),
            ('wallet', 'Digital Wallet'),
            ('paypal', 'PayPal'),
        ],
        default='card'
    )
    default_pickup_address = serializers.CharField(max_length=255, required=False, allow_blank=True)
    default_pickup_latitude = serializers.DecimalField(
        max_digits=10, decimal_places=7, required=False, allow_null=True
    )
    default_pickup_longitude = serializers.DecimalField(
        max_digits=10, decimal_places=7, required=False, allow_null=True
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'first_name', 'last_name',
            'phone', 'preferred_payment', 'default_pickup_address',
            'default_pickup_latitude', 'default_pickup_longitude'
        ]
    
    def validate_username(self, value):
        """Validate username uniqueness."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value
    
    def validate_email(self, value):
        """Validate email format and uniqueness."""
        if value:
            # Normalize the email using Django's built-in method
            value = BaseUserManager.normalize_email(value)
            
            # Validate email format using Django's built-in validator
            email_validator = EmailValidator()
            try:
                email_validator(value)
            except DjangoValidationError as e:
                raise serializers.ValidationError(str(e))
            
            # Check uniqueness
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError("A user with this email already exists.")
        
        return value
    
    def validate_phone(self, value):
        """Validate phone number format and uniqueness among riders."""
        from .models import Rider
        import re
        
        # Validate format using regex similar to model
        phone_pattern = r'^\+?1?\d{9,15}$'
        if not re.match(phone_pattern, value):
            raise serializers.ValidationError(
                "Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        
        # Check uniqueness among riders
        if Rider.objects.filter(phone=value).exists():
            raise serializers.ValidationError("A rider with this phone number already exists.")
        
        return value
    
    def validate(self, attrs):
        """Cross-field validation."""
        # Validate coordinates are both provided or both empty
        lat = attrs.get('default_pickup_latitude')
        lng = attrs.get('default_pickup_longitude')
        
        if (lat is not None) != (lng is not None):
            raise serializers.ValidationError({
                'default_pickup_latitude': 'Both latitude and longitude must be provided together, or both left empty.',
                'default_pickup_longitude': 'Both latitude and longitude must be provided together, or both left empty.'
            })
        
        # Validate coordinates are not (0,0)
        if lat is not None and lng is not None:
            if abs(lat) < 0.0001 and abs(lng) < 0.0001:
                raise serializers.ValidationError({
                    'default_pickup_latitude': 'Coordinates cannot be (0,0) - please provide valid location.',
                    'default_pickup_longitude': 'Coordinates cannot be (0,0) - please provide valid location.'
                })
        
        return attrs
    
    def create(self, validated_data):
        """Create User and Rider instances."""
        from .models import Rider
        
        # Extract rider-specific data
        rider_data = {
            'phone': validated_data.pop('phone'),
            'preferred_payment': validated_data.pop('preferred_payment', 'card'),
            'default_pickup_address': validated_data.pop('default_pickup_address', ''),
            'default_pickup_latitude': validated_data.pop('default_pickup_latitude', None),
            'default_pickup_longitude': validated_data.pop('default_pickup_longitude', None),
        }
        
        # Create User
        user = User.objects.create_user(**validated_data)
        
        # Create Rider profile
        rider = Rider.objects.create(user=user, **rider_data)
        
        return user
    
    def to_representation(self, instance):
        """Custom representation for response."""
        rider = instance.rider_profile
        return {
            'id': instance.id,
            'username': instance.username,
            'email': instance.email,
            'first_name': instance.first_name,
            'last_name': instance.last_name,
            'full_name': instance.get_full_name(),
            'rider_profile': {
                'id': rider.id,
                'phone': rider.phone,
                'preferred_payment': rider.preferred_payment,
                'default_pickup_address': rider.default_pickup_address,
                'average_rating': str(rider.average_rating),
                'total_rides': rider.total_rides,
                'is_active': rider.is_active,
                'created_at': rider.created_at,
            }
        }


class DriverRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for driver registration.
    
    Creates both a Django User and a Driver profile with comprehensive validation.
    Handles password hashing, email uniqueness, and driver-specific fields including
    vehicle information and license validation.
    """
    
    # User fields
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    
    # Driver-specific fields
    phone = serializers.CharField(max_length=17)
    license_number = serializers.CharField(max_length=20)
    license_expiry = serializers.DateField()
    
    # Vehicle information
    vehicle_make = serializers.CharField(max_length=50)
    vehicle_model = serializers.CharField(max_length=50)
    vehicle_year = serializers.IntegerField()
    vehicle_color = serializers.CharField(max_length=30)
    vehicle_type = serializers.ChoiceField(
        choices=[
            ('sedan', 'Sedan'),
            ('suv', 'SUV'),
            ('hatchback', 'Hatchback'),
            ('motorcycle', 'Motorcycle'),
            ('van', 'Van'),
        ],
        default='sedan'
    )
    license_plate = serializers.CharField(max_length=10)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'first_name', 'last_name',
            'phone', 'license_number', 'license_expiry',
            'vehicle_make', 'vehicle_model', 'vehicle_year', 'vehicle_color',
            'vehicle_type', 'license_plate'
        ]
    
    def validate_username(self, value):
        """Validate username uniqueness."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value
    
    def validate_email(self, value):
        """Validate email format and uniqueness."""
        if value:
            # Normalize the email using Django's built-in method
            value = BaseUserManager.normalize_email(value)
            
            # Validate email format using Django's built-in validator
            email_validator = EmailValidator()
            try:
                email_validator(value)
            except DjangoValidationError as e:
                raise serializers.ValidationError(str(e))
            
            # Check uniqueness
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError("A user with this email already exists.")
        
        return value
    
    def validate_phone(self, value):
        """Validate phone number format and uniqueness among drivers."""
        from .models import Driver
        import re
        
        # Validate format using regex similar to model
        phone_pattern = r'^\+?1?\d{9,15}$'
        if not re.match(phone_pattern, value):
            raise serializers.ValidationError(
                "Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        
        # Check uniqueness among drivers
        if Driver.objects.filter(phone=value).exists():
            raise serializers.ValidationError("A driver with this phone number already exists.")
        
        return value
    
    def validate_license_number(self, value):
        """Validate license number format and uniqueness."""
        from .models import Driver
        import re
        
        # Validate format
        license_pattern = r'^[A-Z0-9]{5,20}$'
        if not re.match(license_pattern, value.upper()):
            raise serializers.ValidationError(
                "License number must be 5-20 characters, uppercase letters and numbers only."
            )
        
        # Check uniqueness
        if Driver.objects.filter(license_number=value.upper()).exists():
            raise serializers.ValidationError("A driver with this license number already exists.")
        
        return value.upper()
    
    def validate_license_plate(self, value):
        """Validate license plate format and uniqueness."""
        from .models import Driver
        import re
        
        # Validate format
        plate_pattern = r'^[A-Z0-9]{2,10}$'
        if not re.match(plate_pattern, value.upper()):
            raise serializers.ValidationError(
                "License plate must be 2-10 characters, uppercase letters and numbers only."
            )
        
        # Check uniqueness
        if Driver.objects.filter(license_plate=value.upper()).exists():
            raise serializers.ValidationError("A driver with this license plate already exists.")
        
        return value.upper()
    
    def validate_license_expiry(self, value):
        """Validate license expiry is in the future."""
        from datetime import date
        if value <= date.today():
            raise serializers.ValidationError("License expiry date must be in the future.")
        return value
    
    def validate_vehicle_year(self, value):
        """Validate vehicle year is reasonable."""
        from datetime import date
        
        if value < 1980:
            raise serializers.ValidationError("Vehicle year must be 1980 or later.")
        
        # Calculate max year inline (current year + 1 for next year models)
        max_year = date.today().year + 1
        if value > max_year:
            raise serializers.ValidationError(f"Vehicle year cannot be more than {max_year}.")
        
        return value
    
    def validate(self, attrs):
        """Cross-field validation."""
        # Ensure all required fields are not empty strings
        required_fields = ['phone', 'license_number', 'vehicle_make', 'vehicle_model', 'vehicle_color', 'license_plate']
        for field in required_fields:
            value = attrs.get(field, '')
            if not value or (isinstance(value, str) and value.strip() == ''):
                raise serializers.ValidationError({field: f'{field.replace("_", " ").title()} is required and cannot be empty.'})
        
        return attrs
    
    def create(self, validated_data):
        """Create User and Driver instances."""
        from .models import Driver
        
        # Extract driver-specific data
        driver_data = {
            'phone': validated_data.pop('phone'),
            'license_number': validated_data.pop('license_number'),
            'license_expiry': validated_data.pop('license_expiry'),
            'vehicle_make': validated_data.pop('vehicle_make'),
            'vehicle_model': validated_data.pop('vehicle_model'),
            'vehicle_year': validated_data.pop('vehicle_year'),
            'vehicle_color': validated_data.pop('vehicle_color'),
            'vehicle_type': validated_data.pop('vehicle_type', 'sedan'),
            'license_plate': validated_data.pop('license_plate'),
        }
        
        # Create User
        user = User.objects.create_user(**validated_data)
        
        # Create Driver profile
        driver = Driver.objects.create(user=user, **driver_data)
        
        return user
    
    def to_representation(self, instance):
        """Custom representation for response."""
        driver = instance.driver_profile
        return {
            'id': instance.id,
            'username': instance.username,
            'email': instance.email,
            'first_name': instance.first_name,
            'last_name': instance.last_name,
            'full_name': instance.get_full_name(),
            'driver_profile': {
                'id': driver.id,
                'phone': driver.phone,
                'license_number': driver.license_number,
                'license_expiry': driver.license_expiry,
                'vehicle': {
                    'make': driver.vehicle_make,
                    'model': driver.vehicle_model,
                    'year': driver.vehicle_year,
                    'color': driver.vehicle_color,
                    'type': driver.vehicle_type,
                    'license_plate': driver.license_plate,
                    'full_name': driver.full_vehicle_name,
                },
                'average_rating': str(driver.average_rating),
                'total_rides': driver.total_rides,
                'availability_status': driver.availability_status,
                'is_active': driver.is_active,
                'is_verified': driver.is_verified,
                'is_available_for_rides': driver.is_available_for_rides,
                'created_at': driver.created_at,
            }
        }


class CouponValidationSerializer(serializers.Serializer):
    """
    Serializer for coupon code validation requests.
    
    Provides centralized validation, input normalization, and consistent
    error formatting for coupon validation API endpoints.
    """
    
    code = serializers.CharField(
        max_length=20,
        required=True,
        allow_blank=False,
        help_text="The coupon code to validate"
    )
    
    def validate_code(self, value):
        """
        Validate and normalize the coupon code.
        
        Performs trimming, case normalization, and format validation
        to ensure consistent coupon code processing.
        
        Args:
            value (str): The raw coupon code from the request
            
        Returns:
            str: The normalized and validated coupon code
            
        Raises:
            serializers.ValidationError: If code format is invalid
        """
        if not value:
            raise serializers.ValidationError("Coupon code cannot be empty")
        
        # Trim whitespace and convert to uppercase
        normalized_code = value.strip().upper()
        
        if not normalized_code:
            raise serializers.ValidationError("Coupon code cannot be empty after trimming")
        
        # Validate format (alphanumeric only)
        import re
        if not re.match(r'^[A-Z0-9]+$', normalized_code):
            raise serializers.ValidationError("Coupon code must contain only uppercase letters and numbers")
        
        return normalized_code
    
    def to_internal_value(self, data):
        """
        Override to provide better error handling for missing or invalid data.
        """
        if not isinstance(data, dict):
            raise serializers.ValidationError("Invalid data format. Expected a JSON object.")
        
        if 'code' not in data:
            raise serializers.ValidationError({"code": "This field is required."})
        
        return super().to_internal_value(data)


class RideSerializer(serializers.ModelSerializer):
    """
    Serializer for Ride model with comprehensive field exposure and validation.
    
    Provides read-only computed fields for rider/driver information and
    handles proper field visibility for different API operations.
    """
    
    # Read-only computed fields for better API responses
    rider_name = serializers.CharField(source='rider.user.username', read_only=True)
    rider_phone = serializers.CharField(source='rider.phone', read_only=True)
    
    driver_name = serializers.CharField(source='driver.user.username', read_only=True, allow_null=True)
    driver_phone = serializers.CharField(source='driver.phone', read_only=True, allow_null=True)
    driver_vehicle = serializers.CharField(source='driver.vehicle_model', read_only=True, allow_null=True)
    # driver_license removed to prevent PII leakage in public API responses
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Ride
        fields = [
            'id',
            'rider',
            'rider_name',
            'rider_phone',
            'driver',
            'driver_name',
            'driver_phone',
            'driver_vehicle',
            'pickup_address',
            'pickup_lat',
            'pickup_lng',
            'dropoff_address',
            'drop_lat',
            'drop_lng',
            'status',
            'status_display',
            'requested_at',
            'updated_at',
            'accepted_at',
            'completed_at',
            'estimated_fare',
            'final_fare',
        ]
        read_only_fields = [
            'id',
            'rider',
            'driver',
            'status',
            'requested_at',
            'updated_at',
            'accepted_at',
            'completed_at',
            'rider_name',
            'rider_phone',
            'driver_name',
            'driver_phone',
            'driver_vehicle',
            'status_display',
        ]
    
    def validate(self, data):
        """
        Validate ride request data using shared coordinate validator.
        """
        # Use shared validator if all coordinates are present
        if all(k in data for k in ['pickup_lat', 'pickup_lng', 'drop_lat', 'drop_lng']):
            errors = validate_coordinates(
                data['pickup_lat'],
                data['pickup_lng'],
                data['drop_lat'],
                data['drop_lng']
            )
            if errors:
                raise serializers.ValidationError(errors)
        
        return data
    
    def validate_pickup_address(self, value):
        """Validate pickup address is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError('Pickup address cannot be empty')
        return value.strip()
    
    def validate_dropoff_address(self, value):
        """Validate dropoff address is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError('Dropoff address cannot be empty')
        return value.strip()


class RideRequestSerializer(serializers.ModelSerializer):
    """
    Serializer specifically for creating ride requests.
    
    Only exposes fields needed for ride booking, hiding system-managed fields.
    """
    
    class Meta:
        model = Ride
        fields = [
            'pickup_address',
            'pickup_lat',
            'pickup_lng',
            'dropoff_address',
            'drop_lat',
            'drop_lng',
        ]
    
    def validate(self, data):
        """
        Validate ride request data.
        """
        # Validate coordinates are within valid ranges
        if not (-90 <= float(data['pickup_lat']) <= 90):
            raise serializers.ValidationError({
                'pickup_lat': 'Latitude must be between -90 and 90'
            })
        
        if not (-180 <= float(data['pickup_lng']) <= 180):
            raise serializers.ValidationError({
                'pickup_lng': 'Longitude must be between -180 and 180'
            })
        
        if not (-90 <= float(data['drop_lat']) <= 90):
            raise serializers.ValidationError({
                'drop_lat': 'Latitude must be between -90 and 90'
            })
        
        if not (-180 <= float(data['drop_lng']) <= 180):
            raise serializers.ValidationError({
                'drop_lng': 'Longitude must be between -180 and 180'
            })
        
        # Validate pickup and dropoff are different
        if (data['pickup_lat'] == data['drop_lat'] and 
            data['pickup_lng'] == data['drop_lng']):
            raise serializers.ValidationError(
                'Pickup and dropoff locations must be different'
            )
        
        return data
    
    def validate_pickup_address(self, value):
        """Validate pickup address is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError('Pickup address cannot be empty')
        return value.strip()
    
    def validate_dropoff_address(self, value):
        """Validate dropoff address is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError('Dropoff address cannot be empty')
        return value.strip()


# ================================
# ORDER STATUS UPDATE SERIALIZER
# ================================

class UpdateOrderStatusSerializer(serializers.Serializer):
    """
    Serializer for updating order status.
    
    Validates order_id existence and ensures status is one of the allowed choices.
    Used by UpdateOrderStatusView to safely update order statuses.
    """
    order_id = serializers.CharField(
        max_length=20,
        required=True,
        help_text="Unique alphanumeric order identifier (e.g., ORD-A7X9K2M5)"
    )
    status = serializers.ChoiceField(
        choices=[
            ('Pending', 'Pending'),
            ('Processing', 'Processing'),
            ('Completed', 'Completed'),
            ('Cancelled', 'Cancelled'),
        ],
        required=True,
        help_text="New status for the order"
    )
    
    def validate_order_id(self, value):
        """Validate that the order exists."""
        from .models import Order
        try:
            order = Order.objects.get(order_id=value)
        except Order.DoesNotExist:
            raise serializers.ValidationError(f"Order with ID '{value}' does not exist.")
        return value
    
    def validate(self, data):
        """Additional validation for status transitions."""
        from .models import Order
        
        # Get the order
        try:
            order = Order.objects.get(order_id=data['order_id'])
        except Order.DoesNotExist:
            # This should not happen as we validate in validate_order_id, but just in case
            raise serializers.ValidationError("Order does not exist.")
        
        # Define valid status transitions
        valid_transitions = {
            'Pending': ['Processing', 'Cancelled'],
            'Processing': ['Completed', 'Cancelled'],
            'Completed': [],  # Cannot change from Completed
            'Cancelled': [],  # Cannot change from Cancelled
        }
        
        current_status = order.status.name
        new_status = data['status']
        
        # Check if transition is allowed
        if new_status not in valid_transitions.get(current_status, []):
            if current_status == new_status:
                raise serializers.ValidationError(
                    f"Order is already in '{current_status}' status."
                )
            elif current_status in ['Completed', 'Cancelled']:
                raise serializers.ValidationError(
                    f"Cannot change status from '{current_status}'. This order is finalized."
                )
            else:
                raise serializers.ValidationError(
                    f"Invalid status transition from '{current_status}' to '{new_status}'. "
                    f"Allowed transitions: {', '.join(valid_transitions[current_status])}"
                )
        
        return data


# =============================================================================
# RIDE FARE CALCULATION SERIALIZERS (Task 10A)
# =============================================================================

class FareCalculationSerializer(serializers.ModelSerializer):
    """
    Serializer for calculating and storing ride fare.
    
    This serializer handles the complete fare calculation workflow:
    1. Validates that the ride is in COMPLETED status
    2. Ensures fare hasn't already been calculated
    3. Calculates distance using Haversine formula
    4. Applies fare formula: base_fare + (distance × per_km_rate) × surge_multiplier
    5. Saves the calculated fare to the Ride model
    
    Task 10A: Calculate & Store Ride Fare — Serializer
    
    Fare Formula:
        fare = base_fare + (distance_in_km × per_km_rate) × surge_multiplier
    
    Constants:
        - base_fare: ₹50
        - per_km_rate: ₹10/km
        - surge_multiplier: 1.0 (normal) or 1.5 (peak hours)
    
    Usage:
        >>> ride = Ride.objects.get(id=42)
        >>> serializer = FareCalculationSerializer(instance=ride)
        >>> serializer.is_valid(raise_exception=True)
        >>> # Fare is automatically calculated and saved during validation
        >>> print(f"Fare: ₹{ride.fare}")
    """
    class Meta:
        model = Ride
        fields = ['fare']
        read_only_fields = ['fare']
    
    def validate(self, data):
        """
        Validate ride state and calculate fare.
        
        This method performs all validation and fare calculation logic:
        - Ensures ride is completed before calculating fare
        - Prevents re-calculation if fare already exists
        - Calculates distance between pickup and dropoff
        - Applies fare formula and saves to database
        
        Raises:
            serializers.ValidationError: If validation fails
        """
        ride = self.instance  # Get the Ride instance this serializer is bound to
        
        # Validate ride state (must be completed, fare not already set)
        self._validate_ride_state(ride)
        
        # Calculate distance using Haversine formula
        distance_km = self._calculate_distance(
            ride.pickup_latitude,
            ride.pickup_longitude,
            ride.dropoff_latitude,
            ride.dropoff_longitude
        )
        
        # Apply fare calculation formula
        base_fare = 50  # ₹50 base fare
        per_km_rate = 10  # ₹10 per kilometer
        surge_multiplier = float(ride.surge_multiplier or 1.0)  # Convert Decimal to float, default to 1.0 if not set
        
        # Calculate fare: base + (distance × rate) × surge
        fare = base_fare + (distance_km * per_km_rate) * surge_multiplier
        
        # Round to 2 decimal places and save
        ride.fare = round(fare, 2)
        ride.save(update_fields=['fare'])
        
        return data
    
    def _validate_ride_state(self, ride):
        """
        Validate that ride is in a valid state for fare calculation.
        
        Args:
            ride (Ride): The ride instance to validate
        
        Raises:
            serializers.ValidationError: If ride is not completed or fare already exists
        """
        # Ride must be completed before fare can be calculated
        if ride.status != Ride.STATUS_COMPLETED:
            raise serializers.ValidationError(
                "Ride must be completed before fare can be calculated."
            )
        
        # Prevent re-calculation if fare already exists
        if ride.fare is not None:
            raise serializers.ValidationError(
                "Fare has already been calculated for this ride."
            )
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate great-circle distance between two points using Haversine formula.
        
        The Haversine formula calculates the shortest distance over the Earth's
        surface, giving an "as-the-crow-flies" distance between points.
        
        Args:
            lat1 (float): Pickup latitude in degrees
            lon1 (float): Pickup longitude in degrees
            lat2 (float): Dropoff latitude in degrees
            lon2 (float): Dropoff longitude in degrees
        
        Returns:
            float: Distance in kilometers
        
        Formula:
            a = sin²(Δφ/2) + cos φ1 × cos φ2 × sin²(Δλ/2)
            c = 2 × atan2(√a, √(1−a))
            d = R × c
        
        Where:
            φ = latitude, λ = longitude, R = Earth's radius (6371 km)
        """
        import math
        
        R = 6371  # Earth's radius in kilometers
        
        # Convert latitude and longitude from degrees to radians
        phi1 = math.radians(float(lat1))
        phi2 = math.radians(float(lat2))
        delta_phi = math.radians(float(lat2) - float(lat1))
        delta_lambda = math.radians(float(lon2) - float(lon1))
        
        # Haversine formula
        a = (
            math.sin(delta_phi / 2) ** 2 +
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        # Distance in kilometers
        distance = R * c
        
        return distance


# =============================================================================
# RIDE PAYMENT SERIALIZERS (Task 11A)
# =============================================================================

class RidePaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for marking a ride as paid and recording payment details.
    
    This serializer handles the payment workflow:
    1. Validates that the ride is completed before accepting payment
    2. Prevents changes if the ride is already marked as paid
    3. Records the payment method (CASH, UPI, or CARD)
    4. Updates payment status to PAID
    5. Records the paid_at timestamp
    
    Task 11A: Payment Flow — Mark Ride as Paid (Serializer)
    
    Payment Methods:
        - CASH: Cash payment
        - UPI: UPI payment (PhonePe, Google Pay, etc.)
        - CARD: Credit/Debit card payment
    
    Payment Status:
        - UNPAID: Default status, payment not received
        - PAID: Payment received and confirmed
    
    Usage:
        >>> ride = Ride.objects.get(id=42)
        >>> serializer = RidePaymentSerializer(
        ...     instance=ride,
        ...     data={'payment_method': 'CASH', 'payment_status': 'PAID'}
        ... )
        >>> if serializer.is_valid():
        ...     serializer.save()
        ...     print(f"Paid via {ride.payment_method} at {ride.paid_at}")
    """
    class Meta:
        model = Ride
        fields = ['payment_method', 'payment_status']
    
    def validate(self, data):
        """
        Validate payment data and ride state.
        
        Ensures:
        - Ride is not already marked as paid (prevent duplicate payments)
        - Ride is completed before marking as paid
        - Payment method is provided when marking as paid
        
        Args:
            data (dict): Validated data containing payment_method and payment_status
        
        Returns:
            dict: Validated data
        
        Raises:
            serializers.ValidationError: If validation fails
        """
        ride = self.instance
        
        # Prevent changes if already paid (immutable after payment)
        if ride.payment_status == Ride.PAYMENT_STATUS_PAID:
            raise serializers.ValidationError(
                "Ride is already marked as paid. Payment records cannot be modified."
            )
        
        # Only allow PAID status if ride is completed
        if data.get('payment_status') == Ride.PAYMENT_STATUS_PAID:
            if ride.status != Ride.STATUS_COMPLETED:
                raise serializers.ValidationError(
                    "Ride must be completed before marking as paid."
                )
            
            # Ensure payment method is provided when marking as paid
            if not data.get('payment_method'):
                raise serializers.ValidationError(
                    "Payment method is required when marking ride as paid."
                )
        
        return data
    
    def update(self, instance, validated_data):
        """
        Update ride with payment information.
        
        Updates the payment_method and payment_status fields, and sets
        the paid_at timestamp if the status is being changed to PAID.
        
        Args:
            instance (Ride): The ride instance to update
            validated_data (dict): Validated payment data
        
        Returns:
            Ride: Updated ride instance
        """
        from django.utils import timezone
        
        # Update payment method and status
        instance.payment_method = validated_data.get(
            'payment_method',
            instance.payment_method
        )
        instance.payment_status = validated_data.get(
            'payment_status',
            instance.payment_status
        )
        
        # Set paid_at timestamp if marking as PAID
        if validated_data.get('payment_status') == Ride.PAYMENT_STATUS_PAID:
            instance.paid_at = timezone.now()
        
        # Save with specific fields to avoid unnecessary updates
        instance.save(update_fields=['payment_method', 'payment_status', 'paid_at'])
        
        return instance


class DriverEarningsSerializer(serializers.Serializer):
    """
    Serializer for calculating driver earnings summary over the last 7 days.
    
    Computes:
    - Total rides completed (COMPLETED status, PAID payment status)
    - Total earnings from fares
    - Payment method breakdown (CASH, UPI, CARD counts)
    - Average fare per ride
    
    This provides transparency for drivers to track their performance and earnings,
    similar to earnings summaries in Uber, Ola, and other ride-sharing platforms.
    
    Usage:
        driver = Driver.objects.get(id=1)
        serializer = DriverEarningsSerializer(driver)
        summary = serializer.data
    
    Example Output:
        {
            "total_rides": 18,
            "total_earnings": "4820.00",
            "payment_breakdown": {
                "CASH": 8,
                "UPI": 6,
                "CARD": 4
            },
            "average_fare": "267.78"
        }
    """
    total_rides = serializers.SerializerMethodField()
    total_earnings = serializers.SerializerMethodField()
    payment_breakdown = serializers.SerializerMethodField()
    average_fare = serializers.SerializerMethodField()
    
    def get_total_rides(self, driver):
        """
        Calculate total completed and paid rides in the last 7 days.
        
        Args:
            driver (Driver): Driver instance
        
        Returns:
            int: Count of qualifying rides
        """
        from django.utils import timezone
        from datetime import timedelta
        
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        return Ride.objects.filter(
            driver=driver,
            status=Ride.STATUS_COMPLETED,
            payment_status=Ride.PAYMENT_STATUS_PAID,
            completed_at__gte=seven_days_ago
        ).count()
    
    def get_total_earnings(self, driver):
        """
        Calculate total earnings from completed and paid rides in the last 7 days.
        
        Args:
            driver (Driver): Driver instance
        
        Returns:
            Decimal: Total fare amount (returns 0.00 if no rides)
        """
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Sum
        
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        total = Ride.objects.filter(
            driver=driver,
            status=Ride.STATUS_COMPLETED,
            payment_status=Ride.PAYMENT_STATUS_PAID,
            completed_at__gte=seven_days_ago
        ).aggregate(total=Sum('fare'))['total']
        
        return total or Decimal('0.00')
    
    def get_payment_breakdown(self, driver):
        """
        Calculate count of rides by payment method in the last 7 days.
        
        Uses Django ORM's Count aggregation to perform counting at the database level
        instead of iterating through rides in Python for better performance.
        
        Args:
            driver (Driver): Driver instance
        
        Returns:
            dict: Payment method counts, e.g., {"CASH": 5, "UPI": 3, "CARD": 2}
        """
        from django.utils import timezone
        from datetime import timedelta
        
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        # Initialize breakdown with all payment methods at 0
        breakdown = {
            Ride.PAYMENT_METHOD_CASH: 0,
            Ride.PAYMENT_METHOD_UPI: 0,
            Ride.PAYMENT_METHOD_CARD: 0,
        }
        
        # Use database-level aggregation for efficient counting
        payment_counts = (
            Ride.objects.filter(
                driver=driver,
                status=Ride.STATUS_COMPLETED,
                payment_status=Ride.PAYMENT_STATUS_PAID,
                completed_at__gte=seven_days_ago
            )
            .values('payment_method')
            .annotate(count=Count('id'))
        )
        
        # Update breakdown with actual counts from database
        for entry in payment_counts:
            method = entry['payment_method']
            if method in breakdown:
                breakdown[method] = entry['count']
        
        return breakdown
    
    def get_average_fare(self, driver):
        """
        Calculate average fare per ride in the last 7 days.
        
        Args:
            driver (Driver): Driver instance
        
        Returns:
            Decimal: Average fare (returns 0.00 if no rides)
        """
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Avg
        
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        average = Ride.objects.filter(
            driver=driver,
            status=Ride.STATUS_COMPLETED,
            payment_status=Ride.PAYMENT_STATUS_PAID,
            completed_at__gte=seven_days_ago
        ).aggregate(average=Avg('fare'))['average']
        
        if average:
            # Round to 2 decimal places
            return Decimal(str(average)).quantize(Decimal('0.01'))
        return Decimal('0.00')


class DriverAvailabilitySerializer(serializers.Serializer):
    """
    Serializer for toggling driver availability status.
    
    Allows drivers to set their availability to accept ride requests.
    This is a simple toggle between 'offline' and 'available' states,
    similar to "Go Online" / "Go Offline" features in Uber, Ola, and Lyft.
    
    The serializer:
    - Accepts boolean is_available field from the request
    - Validates that the user has an associated driver profile
    - Updates the driver's availability_status accordingly
    
    Usage:
        # In a view with authenticated driver user
        serializer = DriverAvailabilitySerializer(
            data={'is_available': True},
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
    
    Request Example:
        POST /api/driver/availability/
        {
            "is_available": true
        }
    
    Response Example:
        {
            "is_available": true,
            "availability_status": "available"
        }
    """
    is_available = serializers.BooleanField(
        required=True,
        help_text="True to go online (available), False to go offline"
    )
    availability_status = serializers.CharField(read_only=True)
    
    def validate(self, data):
        """
        Validate that the requesting user has a driver profile.
        
        Args:
            data (dict): Input data with is_available field
        
        Returns:
            dict: Validated data
        
        Raises:
            ValidationError: If user doesn't have a driver profile
        """
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or not request.user:
            raise serializers.ValidationError(
                "Authentication required to update availability."
            )
        
        if not request.user.is_authenticated:
            raise serializers.ValidationError(
                "Authentication required to update availability."
            )
        
        # Check if user has a driver profile
        if not hasattr(request.user, 'driver_profile'):
            raise serializers.ValidationError(
                "User does not have a driver profile. Only drivers can update availability."
            )
        
        return data
    
    def save(self):
        """
        Update the driver's availability_status based on is_available value.
        
        Maps boolean to availability_status:
        - True -> 'available' (ready to accept rides)
        - False -> 'offline' (not accepting rides)
        
        Returns:
            Driver: Updated driver instance
        """
        request = self.context.get('request')
        driver = request.user.driver_profile
        
        is_available = self.validated_data['is_available']
        
        # Map boolean to status choice
        if is_available:
            driver.availability_status = Driver.STATUS_AVAILABLE
        else:
            driver.availability_status = Driver.STATUS_OFFLINE
        
        driver.save(update_fields=['availability_status', 'updated_at'])
        
        return driver
    
    def to_representation(self, instance):
        """
        Customize the output representation.
        
        Args:
            instance (Driver): Driver instance
        
        Returns:
            dict: Serialized representation with is_available and availability_status
        """
        is_available = instance.availability_status == Driver.STATUS_AVAILABLE
        
        return {
            'is_available': is_available,
            'availability_status': instance.availability_status
        }


# ================================
# ORDER STATUS RETRIEVAL SERIALIZER
# ================================

class OrderStatusRetrievalSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving order status information.
    
    Provides a lightweight response focused on order status tracking,
    including the order ID, current status name, and last update timestamp.
    Designed for frontend order tracking interfaces and status polling.
    
    Fields:
        - order_id: Unique alphanumeric order identifier
        - status: Current order status name (e.g., 'Pending', 'Processing')
        - updated_at: Timestamp of last status update
        - created_at: Timestamp when order was created
    
    Example Response:
        {
            "order_id": "ORD-A7X9K2M5",
            "status": "Processing",
            "updated_at": "2025-10-23T15:30:00Z",
            "created_at": "2025-10-23T14:00:00Z"
        }
    """
    status = serializers.CharField(source='status.name', read_only=True)
    
    class Meta:
        model = Order
        fields = ['order_id', 'status', 'updated_at', 'created_at']
        read_only_fields = ['order_id', 'status', 'updated_at', 'created_at']


# ================================
# TASK 14A: RIDE MATCHING SERIALIZERS
# ================================

from math import radians, cos, sin, asin, sqrt


class LocationInputSerializer(serializers.Serializer):
    """
    Serializer for accepting pickup location coordinates for ride matching.
    
    This serializer validates latitude and longitude inputs from riders
    requesting a ride, ensuring coordinates are within valid geographical ranges.
    
    **Fields:**
        - latitude (float): Pickup latitude (-90 to 90 degrees)
        - longitude (float): Pickup longitude (-180 to 180 degrees)
    
    **Validation:**
        - Latitude must be between -90.0 and 90.0
        - Longitude must be between -180.0 and 180.0
    
    **Example Input:**
        {
            "latitude": 12.9716,
            "longitude": 77.5946
        }
    """
    latitude = serializers.FloatField(
        min_value=-90.0,
        max_value=90.0,
        help_text="Pickup latitude in decimal degrees (-90 to 90)"
    )
    longitude = serializers.FloatField(
        min_value=-180.0,
        max_value=180.0,
        help_text="Pickup longitude in decimal degrees (-180 to 180)"
    )


class NearbyDriverSerializer(serializers.Serializer):
    """
    Serializer for nearby driver data with distance calculation.
    
    This serializer provides driver information ordered by proximity to the
    rider's pickup location. Uses the Haversine formula for accurate
    geographical distance calculation between two coordinate points.
    
    **Fields:**
        - driver_id (int): Unique identifier for the driver
        - name (str): Driver's display name from User model
        - distance_km (float): Calculated distance in kilometers (rounded to 2 decimals)
    
    **Static Methods:**
        - haversine(): Calculates great-circle distance between coordinates
        - get_nearby_drivers(): Finds and sorts available drivers by distance
    
    **Example Output:**
        [
            {
                "driver_id": 4,
                "name": "Amit Kumar",
                "distance_km": 1.23
            },
            {
                "driver_id": 2,
                "name": "Fatima Ali",
                "distance_km": 2.01
            }
        ]
    """
    driver_id = serializers.IntegerField(
        help_text="Unique database ID of the driver"
    )
    name = serializers.CharField(
        help_text="Driver's full name for display"
    )
    distance_km = serializers.FloatField(
        help_text="Distance from pickup location in kilometers"
    )

    @staticmethod
    def haversine(lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance between two points on Earth.
        
        Uses the Haversine formula to compute the shortest distance over the
        earth's surface, giving an 'as-the-crow-flies' distance between points.
        
        **Formula:** 
            a = sin²(Δφ/2) + cos φ1 ⋅ cos φ2 ⋅ sin²(Δλ/2)
            c = 2 ⋅ atan2( √a, √(1−a) )
            d = R ⋅ c
        
        **Args:**
            lat1 (float): Latitude of first point in decimal degrees
            lon1 (float): Longitude of first point in decimal degrees  
            lat2 (float): Latitude of second point in decimal degrees
            lon2 (float): Longitude of second point in decimal degrees
        
        **Returns:**
            float: Distance in kilometers
        
        **Note:**
            Earth radius R = 6371 km (mean radius)
        """
        # Earth radius in kilometers
        R = 6371.0
        
        # Convert decimal degrees to radians
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        
        # Haversine formula
        a = (sin(dlat/2)**2 + 
             cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2)
        c = 2 * asin(sqrt(a))
        
        # Calculate distance
        return R * c

    @staticmethod
    def get_nearby_drivers(latitude, longitude, max_results=5):
        """
        Find available drivers near the pickup location, ordered by distance.
        
        Filters drivers by availability status and calculates distances using
        the Haversine formula. Results are sorted by proximity and limited
        to prevent excessive API response sizes.
        
        **Args:**
            latitude (float): Pickup latitude in decimal degrees
            longitude (float): Pickup longitude in decimal degrees
            max_results (int): Maximum number of drivers to return (default: 5)
        
        **Returns:**
            list: List of dictionaries containing driver data:
                - driver_id: Driver's database ID
                - name: Driver's display name  
                - distance_km: Distance in kilometers (rounded to 2 decimals)
        
        **Filtering Logic:**
            1. Only drivers with availability_status = 'available'
            2. Only drivers with valid location coordinates
            3. Sorted by ascending distance (closest first)
            4. Limited to max_results count
        
        **Example:**
            drivers = NearbyDriverSerializer.get_nearby_drivers(12.9716, 77.5946, 3)
            # Returns: [{"driver_id": 4, "name": "Amit", "distance_km": 1.23}, ...]
        """
        # Filter available drivers with valid coordinates
        drivers = Driver.objects.filter(
            availability_status=Driver.STATUS_AVAILABLE,
            current_latitude__isnull=False,
            current_longitude__isnull=False
        ).select_related('user')
        
        nearby = []
        
        # Calculate distance for each available driver
        for driver in drivers:
            # Convert Decimal coordinates to float for calculation
            driver_lat = float(driver.current_latitude)
            driver_lon = float(driver.current_longitude)
            
            # Calculate distance using Haversine formula
            dist = NearbyDriverSerializer.haversine(
                latitude, longitude, driver_lat, driver_lon
            )
            
            # Get driver name from User model
            driver_name = (driver.user.get_full_name() or 
                          driver.user.username or 
                          f"Driver {driver.id}")
            
            # Add to results list
            nearby.append({
                "driver_id": driver.id,
                "name": driver_name,
                "distance_km": round(dist, 2)
            })
        
        # Sort by distance (closest first) and limit results
        nearby.sort(key=lambda x: x["distance_km"])
        return nearby[:max_results]


# ================================
# TASK 15A: ADMIN RIDE HISTORY SERIALIZERS
# ================================

class RideHistoryFilterSerializer(serializers.Serializer):
    """
    Serializer for filtering admin ride history by various criteria.
    
    This serializer validates filter parameters for admin views to query
    ride history with flexible date ranges, status filtering, and
    driver-specific filtering for operational reporting and analytics.
    
    **Filter Fields:**
        - start_date (date, optional): Filter rides from this date onwards
        - end_date (date, optional): Filter rides up to this date
        - status (choice, optional): Filter by ride status (COMPLETED, CANCELLED)
        - driver_id (int, optional): Filter rides by specific driver ID
    
    **Validation:**
        - Ensures start_date is not after end_date
        - All fields are optional for flexible querying
        - Status choices limited to completed/cancelled for reporting
    
    **Example Input:**
        {
            "start_date": "2025-07-01",
            "end_date": "2025-07-10", 
            "status": "COMPLETED",
            "driver_id": 7
        }
    
    **Use Cases:**
        - Admin dashboard filtering
        - Revenue reports by date range
        - Driver performance analysis
        - Completed rides analytics
        - Cancelled rides investigation
    """
    
    start_date = serializers.DateField(
        required=False,
        help_text="Filter rides from this date onwards (YYYY-MM-DD format)"
    )
    end_date = serializers.DateField(
        required=False,
        help_text="Filter rides up to this date (YYYY-MM-DD format)"
    )
    status = serializers.ChoiceField(
        choices=['COMPLETED', 'CANCELLED'],
        required=False,
        help_text="Filter by ride completion status"
    )
    driver_id = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Filter rides by specific driver database ID"
    )

    def validate(self, data):
        """
        Cross-field validation for date range consistency.
        
        Ensures that start_date is not after end_date to prevent
        invalid date ranges that would return no results.
        
        **Args:**
            data (dict): Validated field data
        
        **Returns:**
            dict: Validated data with consistent date range
        
        **Raises:**
            ValidationError: If start_date > end_date
        """
        start = data.get("start_date")
        end = data.get("end_date")

        if start and end and start > end:
            raise serializers.ValidationError(
                "Start date must be before or equal to end date."
            )
        return data


class AdminRideHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for admin ride history data with detailed information.
    
    This serializer provides comprehensive ride information for admin
    reporting, analytics, and operational oversight. Includes rider/driver
    names, financial data, and completion timestamps for dashboard views.
    
    **Output Fields:**
        - ride_id: Unique database identifier for the ride
        - rider: Rider's display name from User model
        - driver: Driver's display name from User model
        - status: Current ride status (COMPLETED, CANCELLED, etc.)
        - fare: Final calculated fare amount
        - payment_method: Payment method used (UPI, CASH, CARD)
        - completed_at: Timestamp when ride was completed
    
    **Example Output:**
        {
            "ride_id": 103,
            "rider": "Aarav Kumar",
            "driver": "Riya Sharma",
            "status": "COMPLETED",
            "fare": 340.50,
            "payment_method": "UPI",
            "completed_at": "2025-07-08T14:32:12Z"
        }
    
    **Performance Optimizations:**
        - Uses select_related for rider/driver User lookups
        - Minimal field selection for faster queries
        - Indexed fields (status, completed_at) for efficient filtering
    
    **Admin Use Cases:**
        - Revenue reporting and financial analytics
        - Driver performance monitoring
        - Rider usage pattern analysis
        - Operational metrics and KPI tracking
        - Support team ride investigation
    """
    
    ride_id = serializers.IntegerField(
        source='id',
        read_only=True,
        help_text="Unique database identifier for the ride"
    )
    
    rider = serializers.SerializerMethodField(
        help_text="Rider's display name"
    )
    
    driver = serializers.SerializerMethodField(
        help_text="Driver's display name (null if not assigned)"
    )
    
    fare = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
        help_text="Final calculated fare amount"
    )
    
    class Meta:
        model = Ride
        fields = [
            'ride_id', 'rider', 'driver', 'status', 
            'fare', 'payment_method', 'completed_at'
        ]
        read_only_fields = [
            'ride_id', 'rider', 'driver', 'status',
            'fare', 'payment_method', 'completed_at'
        ]
    
    def get_rider(self, obj):
        """
        Get rider's display name from User model.
        
        Returns the rider's full name if available, otherwise username.
        Handles cases where rider might be null (edge case protection).
        
        **Args:**
            obj (Ride): Ride instance
        
        **Returns:**
            str: Rider's display name or "Unknown Rider" if null
        """
        if not obj.rider or not obj.rider.user:
            return "Unknown Rider"
        
        user = obj.rider.user
        full_name = user.get_full_name()
        return full_name if full_name else user.username
    
    def get_driver(self, obj):
        """
        Get driver's display name from User model.
        
        Returns the driver's full name if available, otherwise username.
        Returns None if no driver is assigned to the ride.
        
        **Args:**
            obj (Ride): Ride instance
        
        **Returns:**
            str or None: Driver's display name or None if not assigned
        """
        if not obj.driver or not obj.driver.user:
            return None
        
        user = obj.driver.user
        full_name = user.get_full_name()
        return full_name if full_name else user.username


# ============================================================================
# TASK 16A: TRIP RECEIPT SERIALIZER
# ============================================================================

class TripReceiptSerializer(serializers.ModelSerializer):
    """
    Serializer for generating structured trip receipts for completed rides.
    
    This serializer produces a professional, printable receipt that details
    all aspects of a completed ride including rider, driver, route, fare,
    and payment information. Designed for email delivery, PDF generation,
    or in-app receipt viewing.
    
    **Business Purpose:**
        Trip receipts build trust and transparency with riders by providing
        a detailed breakdown of charges. They serve as digital proof of
        service and reduce support tickets related to fare disputes.
    
    **Output Fields:**
        - ride_id: Unique identifier for the ride transaction
        - rider: Rider's display name
        - driver: Driver's display name
        - origin: Pickup location address
        - destination: Drop-off location address
        - fare: Total amount charged
        - payment_method: Payment method used (UPI, CASH, CARD)
        - status: Ride status (should be COMPLETED for receipts)
        - completed_at: Timestamp when ride was completed
    
    **Example Output:**
        {
            "ride_id": 72,
            "rider": "Sneha",
            "driver": "Karan",
            "origin": "Indiranagar, Bangalore",
            "destination": "HSR Layout, Bangalore",
            "fare": 275.00,
            "payment_method": "UPI",
            "status": "COMPLETED",
            "completed_at": "2025-07-10T18:15:00Z"
        }
    
    **Use Cases:**
        - Email receipts using Celery background tasks
        - In-app trip history with downloadable receipts
        - Driver proof of completed jobs
        - Audit trails for financial reconciliation
        - Customer support documentation
        - Legal/compliance record keeping
    
    **Future Enhancements:**
        - Add fare breakdown (base fare + distance fare + tax)
        - Include trip duration and distance traveled
        - Add static map preview of route
        - Generate PDF receipts for download
    
    **Read-Only Design:**
        This serializer is read-only and designed for viewing/exporting
        completed rides only. It does not support creating or updating rides.
    """
    
    ride_id = serializers.IntegerField(
        source='id',
        read_only=True,
        help_text="Unique identifier for the ride transaction"
    )
    
    rider = serializers.SerializerMethodField(
        help_text="Rider's display name (first name preferred)"
    )
    
    driver = serializers.SerializerMethodField(
        help_text="Driver's display name (first name preferred)"
    )
    
    origin = serializers.CharField(
        source='pickup_address',
        read_only=True,
        help_text="Pickup location address"
    )
    
    destination = serializers.CharField(
        source='dropoff_address',
        read_only=True,
        help_text="Drop-off location address"
    )
    
    fare = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
        help_text="Total fare amount charged for the ride"
    )
    
    class Meta:
        model = Ride
        fields = [
            'ride_id', 'rider', 'driver', 'origin', 'destination',
            'fare', 'payment_method', 'status', 'completed_at'
        ]
        read_only_fields = [
            'ride_id', 'rider', 'driver', 'origin', 'destination',
            'fare', 'payment_method', 'status', 'completed_at'
        ]
    
    def get_rider(self, obj):
        """
        Get rider's display name for receipt.
        
        Returns the rider's first name if available for a personal touch,
        otherwise falls back to full name or username. This matches the
        sample receipt format showing "Sneha" instead of full username.
        
        **Args:**
            obj (Ride): Ride instance
        
        **Returns:**
            str: Rider's display name or "Unknown Rider" if null
        
        **Example:**
            - User with first_name="Sneha" → "Sneha"
            - User with no first_name but full_name → full name
            - User with only username → username
        """
        if not obj.rider or not obj.rider.user:
            return "Unknown Rider"
        
        user = obj.rider.user
        
        # Prefer first name for receipt personalization
        if user.first_name:
            return user.first_name
        
        # Fall back to full name, then username
        full_name = user.get_full_name()
        return full_name if full_name else user.username
    
    def get_driver(self, obj):
        """
        Get driver's display name for receipt.
        
        Returns the driver's first name if available for a personal touch,
        otherwise falls back to full name or username. This matches the
        sample receipt format showing "Karan" instead of full username.
        
        **Args:**
            obj (Ride): Ride instance
        
        **Returns:**
            str: Driver's display name or "Not Assigned" if null
        
        **Example:**
            - User with first_name="Karan" → "Karan"
            - User with no first_name but full_name → full name
            - User with only username → username
        """
        if not obj.driver or not obj.driver.user:
            return "Not Assigned"
        
        user = obj.driver.user
        
        # Prefer first name for receipt personalization
        if user.first_name:
            return user.first_name
        
        # Fall back to full name, then username
        full_name = user.get_full_name()
        return full_name if full_name else user.username


