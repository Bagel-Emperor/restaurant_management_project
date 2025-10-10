from decimal import Decimal
from django.db import models
from .choices import OrderStatusChoices
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from home.models import MenuItem
import re


def get_max_vehicle_year():
    """
    Dynamic validator for maximum vehicle year.
    
    Returns the current year + 1 to allow for next year models
    while preventing unrealistic future years.
    """
    return timezone.now().year + 1


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
    updated_at = models.DateTimeField(auto_now=True)
    
    # User-friendly unique order ID for display and tracking
    order_id = models.CharField(
        max_length=20, 
        unique=True,   # ✅ Now safe to make unique after populating existing data
        blank=True,
        null=True,
        help_text="Unique alphanumeric order identifier (e.g., ORD-A7X9K2M5)"
    )
    
    # Custom model manager
    objects = OrderManager()

    def save(self, *args, **kwargs):
        # Set default status if not provided
        if not self.status_id:
            from .choices import OrderStatusChoices
            OrderStatus = self._meta.get_field('status').related_model
            default_status, _ = OrderStatus.objects.get_or_create(name=OrderStatusChoices.PENDING)
            self.status = default_status
        
        # Generate unique order ID if not provided
        if not self.order_id:
            from .utils import generate_order_number
            self.order_id = generate_order_number(model_class=Order)
        
        super().save(*args, **kwargs)
    
    def calculate_total(self):
        """
        Calculate the total cost of the order based on associated order items.
        
        This method iterates through all OrderItem instances related to this order
        and calculates the sum of (price * quantity) for each item.
        
        Returns:
            Decimal: The total cost of all items in the order.
                    Returns 0 if no items are associated with the order.
        
        Example:
            >>> order = Order.objects.get(order_id='ORD-ABC123')
            >>> total = order.calculate_total()
            >>> print(f"Order total: ${total}")
        """
        # Use select_related() to prevent N+1 queries if menu_item fields are accessed
        # and only fetch the fields we need for calculation
        total = Decimal('0.00')
        
        for item in self.order_items.select_related('menu_item'):
            item_total = item.price * item.quantity
            total += item_total
        
        return total
    
    def __str__(self):
        order_display = self.order_id if self.order_id else f"#{self.id}"
        return f"Order {order_display} - {self.status.name if self.status else 'No Status'}"

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
        max_year = get_max_vehicle_year()
        if self.vehicle_year and self.vehicle_year > max_year:
            raise ValidationError({
                'vehicle_year': f'Vehicle year cannot be more than {max_year}.'
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


class Coupon(models.Model):
    """
    Coupon model for discount promotions and marketing campaigns.
    
    Allows restaurant to create promotional codes that customers can use
    to receive discounts on their orders. Includes validation for code
    uniqueness, activation status, and validity time periods.
    """
    
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Unique coupon code (e.g., SAVE10, WELCOME20)"
    )
    
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('0.01'), message="Discount must be at least 0.01%"),
            MaxValueValidator(Decimal('100.00'), message="Discount cannot exceed 100%")
        ],
        help_text="Discount percentage (e.g., 10.00 for 10% off)"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the coupon is currently active and can be used"
    )
    
    valid_from = models.DateField(
        help_text="Date from when the coupon becomes valid"
    )
    
    valid_until = models.DateField(
        help_text="Date until when the coupon remains valid (inclusive)"
    )
    
    # Optional additional fields for better coupon management
    description = models.TextField(
        blank=True,
        help_text="Optional description of the coupon offer"
    )
    
    usage_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this coupon has been used"
    )
    
    max_usage = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of times this coupon can be used (null for unlimited)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Coupon'
        verbose_name_plural = 'Coupons'
    
    def clean(self):
        """Custom validation for Coupon model."""
        super().clean()
        
        # Ensure valid_from is not after valid_until
        if self.valid_from and self.valid_until and self.valid_from > self.valid_until:
            raise ValidationError({
                'valid_until': 'Valid until date must be after or equal to valid from date.'
            })
        
        # Ensure code is alphanumeric and uppercase
        if self.code:
            if not re.match(r'^[A-Z0-9]+$', self.code):
                raise ValidationError({
                    'code': 'Coupon code must contain only uppercase letters and numbers.'
                })
    
    def save(self, *args, **kwargs):
        """Override save to ensure validation and uppercase code."""
        # Convert code to uppercase
        if self.code:
            self.code = self.code.upper()
        
        # Run validation
        self.full_clean()
        
        super().save(*args, **kwargs)
    
    def is_valid_on_date(self, check_date=None):
        """
        Check if coupon is valid on a specific date.
        
        Args:
            check_date (date): Date to check validity for (defaults to today)
            
        Returns:
            bool: True if coupon is valid on the specified date
        """
        if check_date is None:
            check_date = timezone.now().date()
        
        return (
            self.is_active and 
            self.valid_from <= check_date <= self.valid_until
        )
    
    def is_usage_available(self):
        """
        Check if coupon has remaining usage available.
        
        Returns:
            bool: True if coupon can still be used
        """
        if self.max_usage is None:
            return True  # Unlimited usage
        
        return self.usage_count < self.max_usage
    
    def can_be_used(self, check_date=None):
        """
        Check if coupon can currently be used.
        
        Combines date validity and usage availability checks.
        
        Args:
            check_date (date): Date to check validity for (defaults to today)
            
        Returns:
            bool: True if coupon can be used
        """
        return self.is_valid_on_date(check_date) and self.is_usage_available()
    
    def increment_usage(self):
        """
        Increment the usage count for this coupon atomically.
        
        Uses database-level atomic operations to prevent race conditions
        and enforce usage limits even under concurrent requests.
        
        Should be called when a coupon is successfully applied to an order.
        
        Returns:
            bool: True if usage was successfully incremented, False if usage limit exceeded
        
        Raises:
            ValueError: If the coupon has reached its maximum usage limit
        """
        from django.db import transaction
        from django.db.models import F
        
        with transaction.atomic():
            # Select the coupon with row-level locking to prevent races
            coupon = Coupon.objects.select_for_update().get(pk=self.pk)
            
            # Check usage limits at the database level
            if coupon.max_usage is not None and coupon.usage_count >= coupon.max_usage:
                raise ValueError(f"Coupon {coupon.code} has reached its maximum usage limit of {coupon.max_usage}")
            
            # Use atomic F expression to increment usage count
            updated_count = Coupon.objects.filter(pk=self.pk).update(
                usage_count=F('usage_count') + 1
            )
            
            if updated_count == 1:
                # Refresh the instance to get the updated usage_count
                self.refresh_from_db(fields=['usage_count'])
                return True
            
        return False
    
    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.code} ({self.discount_percentage}% off) - {status}"


class Ride(models.Model):
    """
    Ride model for ride-sharing booking system.
    
    Represents a ride request from a rider to a driver, tracking the complete
    lifecycle from request through completion or cancellation. Implements status
    state machine with proper transitions and race condition prevention.
    
    Status Flow:
        REQUESTED -> ONGOING -> COMPLETED
                  -> CANCELLED (from any state)
    """
    
    # Status choices for ride lifecycle
    STATUS_REQUESTED = 'REQUESTED'
    STATUS_ONGOING = 'ONGOING'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'
    
    STATUS_CHOICES = [
        (STATUS_REQUESTED, 'Requested'),
        (STATUS_ONGOING, 'Ongoing'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    
    # Relationships
    rider = models.ForeignKey(
        Rider,
        on_delete=models.CASCADE,
        related_name='rides',
        help_text="Rider who requested this ride"
    )
    
    driver = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        related_name='rides',
        null=True,
        blank=True,
        help_text="Driver assigned to this ride (null until accepted)"
    )
    
    # Pickup Location
    pickup_address = models.CharField(
        max_length=500,
        help_text="Human-readable pickup address"
    )
    pickup_lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Pickup latitude coordinate"
    )
    pickup_lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Pickup longitude coordinate"
    )
    
    # Dropoff Location
    dropoff_address = models.CharField(
        max_length=500,
        help_text="Human-readable dropoff address"
    )
    drop_lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Dropoff latitude coordinate"
    )
    drop_lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Dropoff longitude coordinate"
    )
    
    # Status and Timestamps
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_REQUESTED,
        db_index=True,
        help_text="Current status of the ride"
    )
    
    requested_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the ride was requested"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last time the ride was updated"
    )
    
    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the driver accepted the ride"
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the ride was completed"
    )
    
    # Future fields for fare calculation (to be implemented later)
    estimated_fare = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated fare for the ride"
    )
    
    final_fare = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Final calculated fare after completion"
    )
    
    class Meta:
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['status', 'requested_at']),
            models.Index(fields=['rider', 'status']),
            models.Index(fields=['driver', 'status']),
        ]
        verbose_name = 'Ride'
        verbose_name_plural = 'Rides'
    
    def clean(self):
        """Validate ride data before saving using shared validation logic."""
        from django.core.exceptions import ValidationError
        
        # Import shared validator to avoid duplication
        from .serializers import validate_coordinates
        
        # Use shared coordinate validator
        errors = validate_coordinates(
            self.pickup_lat,
            self.pickup_lng,
            self.drop_lat,
            self.drop_lng
        )
        
        if errors:
            raise ValidationError(errors)
    
    def accept_ride(self, driver):
        """
        Accept a ride and assign it to a driver.
        
        This method should be called within a transaction to prevent race conditions.
        Returns True if successful, False if ride was already accepted.
        """
        from django.utils import timezone
        
        if self.status != self.STATUS_REQUESTED:
            return False
        
        if self.driver is not None:
            return False
        
        self.driver = driver
        self.status = self.STATUS_ONGOING
        self.accepted_at = timezone.now()
        self.save(update_fields=['driver', 'status', 'accepted_at', 'updated_at'])
        
        return True
    
    def complete_ride(self, final_fare=None):
        """Mark ride as completed (to be expanded in future tasks)."""
        from django.utils import timezone
        
        if self.status != self.STATUS_ONGOING:
            return False
        
        self.status = self.STATUS_COMPLETED
        self.completed_at = timezone.now()
        
        if final_fare is not None:
            self.final_fare = final_fare
        
        self.save(update_fields=['status', 'completed_at', 'final_fare', 'updated_at'])
        return True
    
    def cancel_ride(self):
        """Cancel a ride (can be done from any status except completed)."""
        if self.status == self.STATUS_COMPLETED:
            return False
        
        self.status = self.STATUS_CANCELLED
        self.save(update_fields=['status', 'updated_at'])
        return True
    
    def __str__(self):
        return f"Ride #{self.pk} - {self.rider.user.username} -> {self.status}"
    
    def __repr__(self):
        return (f"<Ride id={self.pk} rider={self.rider.user.username} "
                f"driver={self.driver.user.username if self.driver else 'None'} "
                f"status={self.status}>")
