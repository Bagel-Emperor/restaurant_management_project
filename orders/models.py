from django.db import models
from .choices import OrderStatusChoices
from django.conf import settings
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from home.models import MenuItem


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