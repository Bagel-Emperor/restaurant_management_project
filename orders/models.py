from django.db import models
from .choices import OrderStatusChoices
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from home.models import MenuItem
import re


class OrderManager(models.Manager):
    """
    Custom model manager for the Order model.
    Provides convenience methods for retrieving orders based on their status.
    """
    
    def get_active_orders(self):
        """
        Returns a queryset containing only active orders.
        Active orders are defined as having a status of 'pending' or 'processing'.
        
        Returns:
            QuerySet: Orders with status 'pending' or 'processing'
        """
        return self.filter(
            status__name__in=[OrderStatusChoices.PENDING, OrderStatusChoices.PROCESSING]
        )

# UserProfile model extending Django User
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        full_name = self.user.get_full_name()
        return full_name or self.user.username

class Customer(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or self.phone or f"Customer {self.id}"


# Order model for listing and tracking orders
class Order(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='orders')
    customer = models.ForeignKey('Customer', null=True, blank=True, on_delete=models.SET_NULL, related_name='orders')
    status = models.ForeignKey('OrderStatus', null=False, on_delete=models.PROTECT, related_name='orders')
    total_amount = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Custom model manager
    objects = OrderManager()

    def save(self, *args, **kwargs):
        if not self.status_id:
            from .choices import OrderStatusChoices
            OrderStatus = self._meta.get_field('status').related_model
            default_status, _ = OrderStatus.objects.get_or_create(name=OrderStatusChoices.PENDING)
            self.status = default_status
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Order {self.id} - {self.status.name if self.status else 'No Status'}"

# OrderItem model to link Order and MenuItem with quantity and price
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name} for Order {self.order.id}"

# OrderStatus model for representing order states
class OrderStatus(models.Model):
    """
    Represents a possible status for an order (e.g., Pending, Processing, Completed, Cancelled).
    Uses OrderStatusChoices for maintainability and type safety.
    """
    name = models.CharField(
        max_length=50,
        unique=True,
        choices=OrderStatusChoices.choices,
        default=OrderStatusChoices.PENDING
    )

    class Meta:
        verbose_name = "Order Status"
        verbose_name_plural = "Order Statuses"

    def __str__(self):
        return self.name


# ================================
# RIDE-SHARING MODELS
# ================================

class Rider(models.Model):
    """
    Rider model for ride-sharing application.
    
    Extends Django User with rider-specific fields including payment preferences,
    saved locations, and profile information. Implements comprehensive validation
    for data integrity and security.
    """
    
    # Payment method choices
    PAYMENT_CASH = 'cash'
    PAYMENT_CARD = 'card'
    PAYMENT_WALLET = 'wallet'
    PAYMENT_PAYPAL = 'paypal'
    
    PAYMENT_CHOICES = [
        (PAYMENT_CASH, 'Cash'),
        (PAYMENT_CARD, 'Credit/Debit Card'),
        (PAYMENT_WALLET, 'Digital Wallet'),
        (PAYMENT_PAYPAL, 'PayPal'),
    ]
    
    # OneToOne relationship with Django User
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='rider_profile',
        help_text="Associated Django User account for authentication"
    )
    
    # Contact Information
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone = models.CharField(
        validators=[phone_regex], 
        max_length=17, 
        help_text="Contact phone number for ride notifications"
    )
    
    # Payment & Preferences
    preferred_payment = models.CharField(
        max_length=10,
        choices=PAYMENT_CHOICES,
        default=PAYMENT_CARD,
        help_text="Default payment method for rides"
    )
    
    # Location Preferences
    default_pickup_address = models.CharField(
        max_length=255,
        blank=True,
        help_text="Most frequently used pickup location"
    )
    
    default_pickup_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(-90.0, message="Latitude must be between -90 and 90 degrees"),
            MaxValueValidator(90.0, message="Latitude must be between -90 and 90 degrees")
        ],
        help_text="Latitude coordinate for default pickup location"
    )
    
    default_pickup_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(-180.0, message="Longitude must be between -180 and 180 degrees"),
            MaxValueValidator(180.0, message="Longitude must be between -180 and 180 degrees")
        ],
        help_text="Longitude coordinate for default pickup location"
    )
    
    # Profile & Ratings
    profile_photo = models.ImageField(
        upload_to='rider_profiles/',
        null=True,
        blank=True,
        help_text="Profile photo for driver identification"
    )
    
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=5.00,
        validators=[
            MinValueValidator(0.00, message="Rating cannot be negative"),
            MaxValueValidator(5.00, message="Rating cannot exceed 5.00")
        ],
        help_text="Average rating from drivers (0.00 to 5.00)"
    )
    
    total_rides = models.PositiveIntegerField(
        default=0,
        help_text="Total number of completed rides"
    )
    
    # Account Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the rider account is active"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Rider"
        verbose_name_plural = "Riders"
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]
    
    def clean(self):
        """Custom validation for Rider model."""
        super().clean()
        
        # Validate phone number is not empty
        if not self.phone or self.phone.strip() == '':
            raise ValidationError({'phone': 'Phone number is required and cannot be empty.'})
        
        # Validate coordinates are both provided or both empty
        has_lat = self.default_pickup_latitude is not None
        has_lng = self.default_pickup_longitude is not None
        
        if has_lat != has_lng:
            raise ValidationError({
                'default_pickup_latitude': 'Both latitude and longitude must be provided together, or both left empty.',
                'default_pickup_longitude': 'Both latitude and longitude must be provided together, or both left empty.'
            })
        
        # If coordinates are provided, validate they're reasonable
        if has_lat and has_lng:
            if abs(self.default_pickup_latitude) < 0.0001 and abs(self.default_pickup_longitude) < 0.0001:
                raise ValidationError({
                    'default_pickup_latitude': 'Coordinates cannot be (0,0) - please provide valid location.',
                    'default_pickup_longitude': 'Coordinates cannot be (0,0) - please provide valid location.'
                })
    
    def save(self, *args, **kwargs):
        """Override save to ensure validation."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Rider: {self.user.get_full_name() or self.user.username} ({self.phone})"


class Driver(models.Model):
    """
    Driver model for ride-sharing application.
    
    Extends Django User with driver-specific fields including vehicle information,
    license details, location tracking, and availability status. Implements
    comprehensive validation for regulatory compliance and data integrity.
    """
    
    # Vehicle type choices
    VEHICLE_SEDAN = 'sedan'
    VEHICLE_SUV = 'suv'
    VEHICLE_HATCHBACK = 'hatchback'
    VEHICLE_MOTORCYCLE = 'motorcycle'
    VEHICLE_VAN = 'van'
    
    VEHICLE_CHOICES = [
        (VEHICLE_SEDAN, 'Sedan'),
        (VEHICLE_SUV, 'SUV'),
        (VEHICLE_HATCHBACK, 'Hatchback'),
        (VEHICLE_MOTORCYCLE, 'Motorcycle'),
        (VEHICLE_VAN, 'Van'),
    ]
    
    # Availability status choices
    STATUS_OFFLINE = 'offline'
    STATUS_AVAILABLE = 'available'
    STATUS_BUSY = 'busy'
    STATUS_ON_TRIP = 'on_trip'
    
    STATUS_CHOICES = [
        (STATUS_OFFLINE, 'Offline'),
        (STATUS_AVAILABLE, 'Available'),
        (STATUS_BUSY, 'Busy'),
        (STATUS_ON_TRIP, 'On Trip'),
    ]
    
    # OneToOne relationship with Django User
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='driver_profile',
        help_text="Associated Django User account for authentication"
    )
    
    # Contact Information
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone = models.CharField(
        validators=[phone_regex],
        max_length=17,
        help_text="Contact phone number for ride coordination"
    )
    
    # License Information
    license_regex = RegexValidator(
        regex=r'^[A-Z0-9]{5,20}$',
        message="License number must be 5-20 characters, uppercase letters and numbers only."
    )
    license_number = models.CharField(
        validators=[license_regex],
        max_length=20,
        unique=True,
        help_text="Driver's license number (must be unique)"
    )
    
    license_expiry = models.DateField(
        help_text="Driver's license expiration date"
    )
    
    # Vehicle Information
    vehicle_make = models.CharField(
        max_length=50,
        help_text="Vehicle manufacturer (e.g., Toyota, Honda)"
    )
    
    vehicle_model = models.CharField(
        max_length=50,
        help_text="Vehicle model (e.g., Camry, Civic)"
    )
    
    vehicle_year = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1980, message="Vehicle year must be 1980 or later"),
            MaxValueValidator(2030, message="Vehicle year cannot be in the future")
        ],
        help_text="Vehicle manufacturing year"
    )
    
    vehicle_color = models.CharField(
        max_length=30,
        help_text="Vehicle color for rider identification"
    )
    
    vehicle_type = models.CharField(
        max_length=15,
        choices=VEHICLE_CHOICES,
        default=VEHICLE_SEDAN,
        help_text="Type of vehicle for ride matching"
    )
    
    license_plate_regex = RegexValidator(
        regex=r'^[A-Z0-9]{2,10}$',
        message="License plate must be 2-10 characters, uppercase letters and numbers only."
    )
    license_plate = models.CharField(
        validators=[license_plate_regex],
        max_length=10,
        unique=True,
        help_text="Vehicle license plate number (must be unique)"
    )
    
    # Current Location & Status
    current_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(-90.0, message="Latitude must be between -90 and 90 degrees"),
            MaxValueValidator(90.0, message="Latitude must be between -90 and 90 degrees")
        ],
        help_text="Current latitude for ride matching"
    )
    
    current_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(-180.0, message="Longitude must be between -180 and 180 degrees"),
            MaxValueValidator(180.0, message="Longitude must be between -180 and 180 degrees")
        ],
        help_text="Current longitude for ride matching"
    )
    
    availability_status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default=STATUS_OFFLINE,
        help_text="Current availability for accepting rides"
    )
    
    last_location_update = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of last location update"
    )
    
    # Profile & Ratings
    profile_photo = models.ImageField(
        upload_to='driver_profiles/',
        null=True,
        blank=True,
        help_text="Profile photo for rider identification"
    )
    
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=5.00,
        validators=[
            MinValueValidator(0.00, message="Rating cannot be negative"),
            MaxValueValidator(5.00, message="Rating cannot exceed 5.00")
        ],
        help_text="Average rating from riders (0.00 to 5.00)"
    )
    
    total_rides = models.PositiveIntegerField(
        default=0,
        help_text="Total number of completed rides"
    )
    
    # Account Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the driver account is active"
    )
    
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether driver documents have been verified"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Driver"
        verbose_name_plural = "Drivers"
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['license_number']),
            models.Index(fields=['license_plate']),
            models.Index(fields=['availability_status']),
            models.Index(fields=['is_active', 'is_verified']),
            models.Index(fields=['current_latitude', 'current_longitude']),
            models.Index(fields=['created_at']),
        ]
    
    def clean(self):
        """Custom validation for Driver model."""
        super().clean()
        
        # Validate required fields are not empty
        required_fields = {
            'phone': 'Phone number is required and cannot be empty.',
            'license_number': 'License number is required and cannot be empty.',
            'vehicle_make': 'Vehicle make is required and cannot be empty.',
            'vehicle_model': 'Vehicle model is required and cannot be empty.',
            'vehicle_color': 'Vehicle color is required and cannot be empty.',
            'license_plate': 'License plate is required and cannot be empty.',
        }
        
        errors = {}
        for field_name, error_message in required_fields.items():
            field_value = getattr(self, field_name, None)
            if not field_value or (isinstance(field_value, str) and field_value.strip() == ''):
                errors[field_name] = error_message
        
        if errors:
            raise ValidationError(errors)
        
        # Validate license expiry is in the future
        from django.utils import timezone
        if self.license_expiry and self.license_expiry <= timezone.now().date():
            raise ValidationError({
                'license_expiry': 'License expiry date must be in the future.'
            })
        
        # Validate vehicle year is reasonable
        current_year = timezone.now().year
        if self.vehicle_year and self.vehicle_year > current_year + 1:
            raise ValidationError({
                'vehicle_year': f'Vehicle year cannot be more than {current_year + 1}.'
            })
        
        # Validate coordinates are both provided or both empty
        has_lat = self.current_latitude is not None
        has_lng = self.current_longitude is not None
        
        if has_lat != has_lng:
            raise ValidationError({
                'current_latitude': 'Both latitude and longitude must be provided together, or both left empty.',
                'current_longitude': 'Both latitude and longitude must be provided together, or both left empty.'
            })
        
        # If coordinates are provided, validate they're reasonable
        if has_lat and has_lng:
            if abs(self.current_latitude) < 0.0001 and abs(self.current_longitude) < 0.0001:
                raise ValidationError({
                    'current_latitude': 'Coordinates cannot be (0,0) - please provide valid location.',
                    'current_longitude': 'Coordinates cannot be (0,0) - please provide valid location.'
                })
    
    def save(self, *args, **kwargs):
        """Override save to ensure validation."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def full_vehicle_name(self):
        """Return formatted vehicle name."""
        return f"{self.vehicle_year} {self.vehicle_make} {self.vehicle_model}"
    
    @property
    def is_available_for_rides(self):
        """Check if driver is available for new rides."""
        return (
            self.is_active and 
            self.is_verified and 
            self.availability_status == self.STATUS_AVAILABLE
        )
    
    def __str__(self):
        return f"Driver: {self.user.get_full_name() or self.user.username} ({self.full_vehicle_name})"