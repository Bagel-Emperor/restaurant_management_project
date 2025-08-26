
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from home.models import MenuItem

# UserProfile model extending Django User
class UserProfile(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
	name = models.CharField(max_length=100, blank=True)
	phone = models.CharField(max_length=20, blank=True)

	def __str__(self):
		return self.name or self.user.username

class Customer(models.Model):
	name = models.CharField(max_length=100, blank=True, null=True)
	phone = models.CharField(max_length=20, blank=True, null=True)
	email = models.EmailField(blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.name or self.phone or f"Customer {self.id}"


# Order model for listing and tracking orders


class Order(models.Model):
	STATUS_CHOICES = [
		("pending", "Pending"),
		("completed", "Completed"),
		("canceled", "Canceled"),
	]
	user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='orders')
	customer = models.ForeignKey('Customer', null=True, blank=True, on_delete=models.SET_NULL, related_name='orders')
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
	total_amount = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Order {self.id} - {self.status}"


# OrderItem model to link Order and MenuItem with quantity and price
class OrderItem(models.Model):
	order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
	menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
	quantity = models.PositiveIntegerField(default=1)
	price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])

	def __str__(self):
		return f"{self.quantity} x {self.menu_item.name} for Order {self.order.id}"
