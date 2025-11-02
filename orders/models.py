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
    
    def get_by_status(self, status_name):
        """
        Returns a queryset containing orders with the specified status.
        
        Args:
            status_name (str): The name of the status to filter by (e.g., 'Pending', 'Processing')
        
        Returns:
            QuerySet: Orders with the specified status
            
        Example:
            >>> pending_orders = Order.objects.get_by_status('Pending')
            >>> processing_orders = Order.objects.get_by_status('Processing')
        """
        return self.filter(status__name=status_name)
    
    def get_pending(self):
        """
        Returns a queryset containing all pending orders.
        
        Returns:
            QuerySet: Orders with 'Pending' status
            
        Example:
            >>> pending = Order.objects.get_pending()
        """
        return self.get_by_status(OrderStatusChoices.PENDING)
    
    def get_processing(self):
        """
        Returns a queryset containing all processing orders.
        
        Returns:
            QuerySet: Orders with 'Processing' status
            
        Example:
            >>> processing = Order.objects.get_processing()
        """
        return self.get_by_status(OrderStatusChoices.PROCESSING)
    
    def get_completed(self):
        """
        Returns a queryset containing all completed orders.
        
        Returns:
            QuerySet: Orders with 'Completed' status
            
        Example:
            >>> completed = Order.objects.get_completed()
        """
        return self.get_by_status(OrderStatusChoices.COMPLETED)
    
    def get_cancelled(self):
        """
        Returns a queryset containing all cancelled orders.
        
        Returns:
            QuerySet: Orders with 'Cancelled' status
            
        Example:
            >>> cancelled = Order.objects.get_cancelled()
        """
        return self.get_by_status(OrderStatusChoices.CANCELLED)
    
    def get_active_orders(self):
        """
        Returns a queryset containing only active orders.
        Active orders are defined as having a status of 'pending' or 'processing'.
        
        Returns:
            QuerySet: Orders with status 'pending' or 'processing'
            
        Example:
            >>> active = Order.objects.get_active_orders()
        """
        return self.filter(
            status__name__in=[OrderStatusChoices.PENDING, OrderStatusChoices.PROCESSING]
        )
    
    def get_finalized_orders(self):
        """
        Returns a queryset containing finalized orders (completed or cancelled).
        These orders are in a terminal state and cannot be modified.
        
        Returns:
            QuerySet: Orders with 'Completed' or 'Cancelled' status
            
        Example:
            >>> finalized = Order.objects.get_finalized_orders()
        """
        return self.filter(
            status__name__in=[OrderStatusChoices.COMPLETED, OrderStatusChoices.CANCELLED]
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


class LoyaltyProgram(models.Model):
    """
    Represents different tiers or levels of a customer loyalty program.
    
    Each tier has specific benefits including point requirements and discount
    percentages. Examples include Bronze, Silver, Gold, or Platinum tiers.
    
    The loyalty discount is applied after any coupon discounts, providing an
    additional benefit for loyal customers on top of promotional offers.
    """
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Name of the loyalty tier (e.g., 'Silver Member')"
    )
    points_required = models.IntegerField(
        unique=True,
        validators=[MinValueValidator(0)],
        help_text="Minimum number of loyalty points required to reach this tier (must be 0 or greater)"
    )
    points_per_dollar_spent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=1.0,
        help_text="How many loyalty points a customer earns for each dollar spent (e.g., 1.0 for 1 point per dollar)"
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage discount for customers in this tier (0-100%, e.g., 5.00 for 5%)"
    )
    description = models.TextField(
        help_text="Brief explanation of the benefits for this tier"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Flag to indicate if the program is currently active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Loyalty Program"
        verbose_name_plural = "Loyalty Programs"
        ordering = ['points_required']  # Order by points required (lowest to highest)

    def __str__(self):
        return f"{self.name} ({self.points_required} points - {self.discount_percentage}% discount)"


# Order model for listing and tracking orders
class Order(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='orders')
    customer = models.ForeignKey('Customer', null=True, blank=True, on_delete=models.SET_NULL, related_name='orders')
    status = models.ForeignKey('OrderStatus', null=False, on_delete=models.PROTECT, related_name='orders')
    coupon = models.ForeignKey(
        'Coupon',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='orders',
        help_text="Optional coupon for discount on this order"
    )
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

    def clean(self):
        """
        Custom validation for Order model.
        
        Validates:
        - Coupon cannot be changed on finalized orders (Completed/Cancelled)
        - Coupon must be valid and usable when assigned
        - Only one coupon per order (enforced by ForeignKey, but validated here)
        """
        super().clean()
        
        from .choices import OrderStatusChoices
        
        # If this is an existing order (has pk), check if coupon is being changed
        if self.pk:
            try:
                old_order = Order.objects.get(pk=self.pk)
                
                # Prevent coupon changes on finalized orders
                if old_order.status and old_order.status.name in [
                    OrderStatusChoices.COMPLETED,
                    OrderStatusChoices.CANCELLED
                ]:
                    if old_order.coupon != self.coupon:
                        raise ValidationError({
                            'coupon': f'Cannot change coupon on {old_order.status.name.lower()} orders.'
                        })
            except Order.DoesNotExist:
                # New order, no validation needed for changes
                pass
        
        # Validate coupon if one is assigned
        if self.coupon:
            # Check if coupon can be used (active, valid date range, usage limit)
            if not self.coupon.can_be_used():
                error_messages = []
                
                if not self.coupon.is_active:
                    error_messages.append('Coupon is not active.')
                
                if not self.coupon.is_valid_on_date():
                    error_messages.append('Coupon is expired or not yet valid.')
                
                if not self.coupon.is_usage_available():
                    error_messages.append(f'Coupon has reached its maximum usage limit.')
                
                raise ValidationError({
                    'coupon': ' '.join(error_messages)
                })

    def save(self, *args, **kwargs):
        """
        Override save to set defaults and run validation.
        
        Note: This method calls full_clean() by default, which validates
        the model before saving. This ensures data integrity but may cause
        performance issues in bulk operations.
        
        For bulk operations, use QuerySet.update() or pass skip_validation=True:
            Order.objects.filter(pk=order.pk).update(field=value)  # Bypasses validation
            order.save(skip_validation=True)  # Bypasses validation
        
        Args:
            skip_validation (bool): If True, skips full_clean() validation.
                                   Use with caution in bulk operations only.
        """
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
        
        # Run validation before saving (unless explicitly skipped for bulk operations)
        skip_validation = kwargs.pop('skip_validation', False)
        if not skip_validation:
            self.full_clean()
        
        super().save(*args, **kwargs)
    
    def calculate_total(self):
        """
        Calculate the total cost of the order based on associated order items.
        
        This method calculates the order total in two steps:
        1. Calculate the subtotal (sum of all item prices × quantities)
        2. Apply any discount from an associated coupon
        
        The discount is calculated using the calculate_discount utility function,
        which validates the coupon and applies the appropriate discount percentage.
        
        Returns:
            Decimal: The final total cost after applying any discount.
                    Returns 0 if no items are associated with the order.
        
        Example:
            >>> order = Order.objects.get(order_id='ORD-ABC123')
            >>> total = order.calculate_total()
            >>> print(f"Order total: ${total}")
            
            >>> # Order with coupon
            >>> order.coupon = Coupon.objects.get(code='SAVE10')
            >>> total = order.calculate_total()  # Applies 10% discount
        
        Notes:
            - Uses select_related() to prevent N+1 queries
            - Discount is only applied if coupon is valid and active
            - Returns subtotal if no coupon is applied
            - Final total is quantized to 2 decimal places (cent precision)
        """
        from .utils import calculate_discount
        
        # Calculate subtotal from all order items
        subtotal = Decimal('0.00')
        
        for item in self.order_items.select_related('menu_item'):
            item_total = item.price * item.quantity
            subtotal += item_total
        
        # Apply discount if coupon is present
        discount_amount = calculate_discount(subtotal, self.coupon)
        
        # Calculate final total
        final_total = subtotal - discount_amount
        
        # Defensive programming: Ensure total is never negative
        # This handles edge cases like:
        # - Manual database updates that bypass Coupon validation (max 100% discount)
        # - Race conditions during concurrent coupon updates
        # - Data corruption or migration issues
        # While Coupon.discount_percentage is validated (max 100%), this ensures
        # calculate_total() remains robust even if invalid data exists in the database.
        final_total = max(final_total, Decimal('0.00'))
        
        return final_total
    
    def get_unique_item_names(self):
        """
        Get a list of unique menu item names associated with this order.
        
        This method retrieves all OrderItem instances related to this order,
        extracts the name of each associated MenuItem, and returns a list
        containing only unique names. This is useful for:
        - Displaying order contents in summaries
        - Search functionality (finding orders by item name)
        - Order filtering and categorization
        - Generating order descriptions
        
        Returns:
            list: A list of unique menu item names (strings) in alphabetical order.
                  Returns an empty list if no items are associated with the order.
        
        Example:
            >>> order = Order.objects.get(order_id='ORD-ABC123')
            >>> items = order.get_unique_item_names()
            >>> print(items)
            ['Caesar Salad', 'Margherita Pizza', 'Tiramisu']
            
            >>> # Order with duplicate items (multiple quantities)
            >>> order2 = Order.objects.get(order_id='ORD-XYZ789')
            >>> # Has: 2x Pizza, 1x Salad, 3x Pizza (different order items)
            >>> items2 = order2.get_unique_item_names()
            >>> print(items2)
            ['Pizza', 'Salad']  # Only unique names, duplicates removed
        
        Notes:
            - Uses select_related('menu_item') to optimize database queries
            - Returns names in alphabetical order for consistency
            - Handles edge case of orders with no items (returns empty list)
            - Preserves original item name casing
        
        Performance:
            - Single database query with join (efficient)
            - O(n) time complexity where n is number of order items
            - Suitable for orders with hundreds of items
        """
        # Use a set to collect unique names (automatically removes duplicates)
        unique_names = set()
        
        # Iterate through related order items with optimized query
        for order_item in self.order_items.select_related('menu_item'):
            unique_names.add(order_item.menu_item.name)
        
        # sorted() returns a list directly, no need for list() conversion
        return sorted(unique_names)
    
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
    
    STATUS_CHOICES = [
        (STATUS_OFFLINE, 'Offline'),
        (STATUS_AVAILABLE, 'Available'),
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
    
    # Property aliases for compatibility with fare calculation code
    @property
    def pickup_latitude(self):
        """Alias for pickup_lat to match fare calculation API."""
        return self.pickup_lat
    
    @property
    def pickup_longitude(self):
        """Alias for pickup_lng to match fare calculation API."""
        return self.pickup_lng
    
    @property
    def dropoff_latitude(self):
        """Alias for drop_lat to match fare calculation API."""
        return self.drop_lat
    
    @property
    def dropoff_longitude(self):
        """Alias for drop_lng to match fare calculation API."""
        return self.drop_lng
    
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
    
    # Fare Calculation Fields (Task 10A/10B)
    fare = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Calculated fare using distance and surge multiplier"
    )
    
    surge_multiplier = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.0,
        help_text="Surge multiplier for peak hours (1.0 = normal, 1.5 = 50% surge)"
    )
    
    # Payment Fields (Task 11A/11B)
    PAYMENT_STATUS_UNPAID = 'UNPAID'
    PAYMENT_STATUS_PAID = 'PAID'
    
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_STATUS_UNPAID, 'Unpaid'),
        (PAYMENT_STATUS_PAID, 'Paid'),
    ]
    
    PAYMENT_METHOD_CASH = 'CASH'
    PAYMENT_METHOD_UPI = 'UPI'
    PAYMENT_METHOD_CARD = 'CARD'
    
    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_METHOD_CASH, 'Cash'),
        (PAYMENT_METHOD_UPI, 'UPI'),
        (PAYMENT_METHOD_CARD, 'Card'),
    ]
    
    payment_status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_STATUS_UNPAID,
        db_index=True,
        help_text="Payment status of the ride"
    )
    
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHOD_CHOICES,
        null=True,
        blank=True,
        help_text="Method used for payment (Cash, UPI, Card)"
    )
    
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when payment was marked as complete"
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
