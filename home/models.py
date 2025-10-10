from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal

# Constants
SESSION_KEY_DISPLAY_LENGTH = 10

# Model to store restaurant location details, linked to Restaurant
class Restaurant(models.Model):
	name = models.CharField(max_length=100, unique=True)
	owner_name = models.CharField(max_length=100)
	email = models.EmailField(unique=True)
	phone_number = models.CharField(max_length=20)
	created_at = models.DateTimeField(auto_now_add=True)
	# Store opening hours as a JSON object (e.g., {"Monday": "9am-5pm", ...})
	opening_hours = models.JSONField(default=dict, blank=True)

	def __str__(self):
		return self.name

# Model to store contact form submissions
class ContactSubmission(models.Model):
	name = models.CharField(max_length=100)
	email = models.EmailField()
	message = models.TextField()
	submitted_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.name} <{self.email}>"

class RestaurantLocation(models.Model):
	restaurant = models.OneToOneField(Restaurant, on_delete=models.CASCADE, related_name='location')
	address = models.CharField(max_length=255)
	city = models.CharField(max_length=100)
	state = models.CharField(max_length=50)
	zip_code = models.CharField(max_length=20)

	def __str__(self):
		return f"{self.address}, {self.city}, {self.state} {self.zip_code}"
class MenuItem(models.Model):
	name = models.CharField(max_length=100)
	description = models.TextField(blank=True)
	price = models.DecimalField(max_digits=6, decimal_places=2)
	restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menu_items')
	category = models.ForeignKey('MenuCategory', on_delete=models.SET_NULL, null=True, blank=True, related_name='menu_items')
	is_available = models.BooleanField(default=True)
	is_daily_special = models.BooleanField(
		default=False,
		help_text="Mark this item as a daily special to feature it prominently"
	)
	created_at = models.DateTimeField(auto_now_add=True)
	image = models.ImageField(upload_to='menu_images/', blank=True, null=True)

	def __str__(self):
		return self.name

class Feedback(models.Model):
	comment = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Feedback {self.id} at {self.created_at}" if self.id else "Feedback"

class MenuCategory(models.Model):
	"""
	Represents a category for menu items (e.g., Appetizers, Main Courses, Desserts).
	"""
	name = models.CharField(max_length=100, unique=True)

	def __str__(self):
		return self.name

	class Meta:
		verbose_name_plural = 'Menu Categories'


class Cart(models.Model):
	"""
	Represents a shopping cart for a user.
	Supports both authenticated users and session-based anonymous users.
	"""
	user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='cart')
	session_key = models.CharField(max_length=50, null=True, blank=True, unique=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		# Ensure either user or session_key is set, but not both for the same cart
		constraints = [
			models.CheckConstraint(
				check=models.Q(user__isnull=False) | models.Q(session_key__isnull=False),
				name='cart_must_have_user_or_session'
			)
		]

	def __str__(self):
		if self.user:
			return f"Cart for {self.user.username}"
		return f"Cart for session {self.session_key[:SESSION_KEY_DISPLAY_LENGTH]}..."

	@property
	def total_items(self):
		"""Returns the total number of items in the cart."""
		return sum(item.quantity for item in self.cart_items.all())

	@property
	def total_price(self):
		"""Returns the total price of all items in the cart."""
		return sum(item.subtotal for item in self.cart_items.all())

	def clear(self):
		"""Remove all items from the cart."""
		self.cart_items.all().delete()


class CartItem(models.Model):
	"""
	Represents an individual item in a shopping cart.
	Links a menu item to a cart with a specific quantity.
	"""
	cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items')
	menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
	quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
	added_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		# Ensure unique menu item per cart (no duplicates)
		unique_together = ['cart', 'menu_item']

	def __str__(self):
		return f"{self.quantity}x {self.menu_item.name} in {self.cart}"

	@property
	def subtotal(self):
		"""Returns the subtotal for this cart item (price * quantity)."""
		return self.menu_item.price * self.quantity

	def clean(self):
		"""Ensure the menu item is available."""
		from django.core.exceptions import ValidationError
		if not self.menu_item.is_available:
			raise ValidationError(f"Menu item '{self.menu_item.name}' is not available.")


class Table(models.Model):
	"""
	Represents a table in the restaurant for seating management.
	Includes table capacity, location, and availability status.
	"""
	AVAILABILITY_CHOICES = [
		('available', 'Available'),
		('occupied', 'Occupied'),
		('reserved', 'Reserved'),
		('maintenance', 'Under Maintenance'),
	]
	
	LOCATION_CHOICES = [
		('indoor', 'Indoor'),
		('outdoor', 'Outdoor'),
		('patio', 'Patio'),
		('bar', 'Bar Area'),
		('private', 'Private Dining'),
	]
	
	# Basic table information
	number = models.PositiveIntegerField(help_text="Table number (unique per restaurant)")
	capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text="Maximum number of seats")
	location = models.CharField(max_length=20, choices=LOCATION_CHOICES, default='indoor')
	
	# Status and availability
	status = models.CharField(max_length=15, choices=AVAILABILITY_CHOICES, default='available')
	is_active = models.BooleanField(default=True, help_text="Whether the table is in service")
	
	# Additional details
	description = models.TextField(blank=True, help_text="Optional description or special features")
	restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='tables')
	
	# Timestamps
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		ordering = ['number']
		verbose_name = 'Table'
		verbose_name_plural = 'Tables'
		# Ensure table numbers are unique per restaurant, not globally
		unique_together = [['restaurant', 'number']]
		indexes = [
			models.Index(fields=['number']),
			models.Index(fields=['status']),
			models.Index(fields=['capacity']),
			models.Index(fields=['location']),
			models.Index(fields=['restaurant', 'number']),  # Index for unique constraint
		]
	
	def __str__(self):
		return f"Table {self.number} ({self.capacity} seats) - {self.get_status_display()}"
	
	@property
	def is_available(self):
		"""Check if table is available for seating."""
		return self.status == 'available' and self.is_active
	
	@property
	def status_display(self):
		"""Get human-readable status."""
		return self.get_status_display()
	
	def clean(self):
		"""Custom validation for table."""
		if self.capacity < 1:
			raise ValidationError("Table capacity must be at least 1")
		if self.number < 1:
			raise ValidationError("Table number must be positive")