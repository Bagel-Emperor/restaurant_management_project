from rest_framework import serializers
from django.contrib.auth.models import User, BaseUserManager
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError as DjangoValidationError
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
