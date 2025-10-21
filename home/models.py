from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta

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
	discount_percentage = models.DecimalField(
		max_digits=5,
		decimal_places=2,
		default=0.00,
		validators=[
			MinValueValidator(0.00),
			MaxValueValidator(100.00)
		],
		help_text="Discount percentage for this menu item (0-100)"
	)
	created_at = models.DateTimeField(auto_now_add=True)
	image = models.ImageField(upload_to='menu_images/', blank=True, null=True)

	def __str__(self):
		return self.name
	
	def calculate_final_price(self):
		"""
		Calculate the final price of the menu item after applying any discount.
		
		Returns the discounted price if a discount percentage is set (greater than 0),
		otherwise returns the original price. The discount is calculated as:
		final_price = original_price - (original_price × discount_percentage / 100)
		
		Returns:
			Decimal: The final price after discount (rounded to 2 decimal places)
			
		Examples:
			>>> item = MenuItem(price=Decimal('10.00'), discount_percentage=Decimal('0.00'))
			>>> item.calculate_final_price()
			Decimal('10.00')
			
			>>> item = MenuItem(price=Decimal('10.00'), discount_percentage=Decimal('20.00'))
			>>> item.calculate_final_price()
			Decimal('8.00')
			
			>>> item = MenuItem(price=Decimal('15.50'), discount_percentage=Decimal('15.00'))
			>>> item.calculate_final_price()
			Decimal('13.18')
		"""
		from decimal import Decimal
		
		# If no discount, return original price
		if not self.discount_percentage or self.discount_percentage == 0:
			return self.price
		
		# Calculate discount amount: price × (discount_percentage / 100)
		discount_amount = self.price * (self.discount_percentage / Decimal('100'))
		
		# Calculate final price: original price - discount amount
		final_price = self.price - discount_amount
		
		# Ensure we return a non-negative price (safety check)
		final_price = max(final_price, Decimal('0.00'))
		
		# Round to 2 decimal places for currency precision
		return final_price.quantize(Decimal('0.01'))

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
	description = models.TextField(blank=True, help_text="Optional description of the category")

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


class UserReview(models.Model):
	"""
	Represents a user review for a menu item.
	Each review is associated with a specific user and menu item.
	"""
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
	menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='reviews')
	rating = models.IntegerField(
		validators=[MinValueValidator(1), MaxValueValidator(5)],
		help_text="Rating from 1 to 5 stars"
	)
	comment = models.TextField(help_text="Review comment or feedback")
	review_date = models.DateTimeField(auto_now_add=True, help_text="When the review was created")
	
	class Meta:
		ordering = ['-review_date']
		verbose_name = 'User Review'
		verbose_name_plural = 'User Reviews'
		constraints = [
			# Ensure a user can only review a menu item once
			models.UniqueConstraint(fields=['user', 'menu_item'], name='uniq_user_menu_item_review'),
			# Ensure rating is between 1 and 5 at database level
			models.CheckConstraint(check=models.Q(rating__gte=1, rating__lte=5), name='rating_range_1_to_5')
		]
		indexes = [
			models.Index(fields=['menu_item']),
			models.Index(fields=['user']),
			models.Index(fields=['rating']),
			models.Index(fields=['-review_date']),
		]
	
	def __str__(self):
		return f"{self.user.username}'s review of {self.menu_item.name} - {self.rating}/5"
	
	def clean(self):
		"""Validate rating is between 1 and 5."""
		if self.rating < 1 or self.rating > 5:
			raise ValidationError("Rating must be between 1 and 5")
			raise ValidationError("Rating must be between 1 and 5")


class Reservation(models.Model):
	"""
	Represents a table reservation made by a customer.
	Includes methods for finding available time slots and preventing past reservations.
	"""
	STATUS_CHOICES = [
		('pending', 'Pending'),
		('confirmed', 'Confirmed'),
		('cancelled', 'Cancelled'),
		('completed', 'Completed'),
		('no_show', 'No Show'),
	]
	
	# Customer information
	customer_name = models.CharField(max_length=100, help_text="Full name of the customer")
	customer_email = models.EmailField(help_text="Email address for confirmation")
	customer_phone = models.CharField(max_length=20, help_text="Phone number for contact")
	
	# Reservation details
	table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='reservations')
	party_size = models.PositiveIntegerField(
		validators=[MinValueValidator(1)],
		help_text="Number of people in the party"
	)
	reservation_date = models.DateField(help_text="Date of the reservation")
	reservation_time = models.TimeField(help_text="Time of the reservation")
	duration_minutes = models.PositiveIntegerField(
		default=120,
		validators=[MinValueValidator(30)],
		help_text="Expected duration in minutes (default: 2 hours)"
	)
	
	# Status and tracking
	status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
	special_requests = models.TextField(blank=True, help_text="Any special requests or notes")
	
	# User relationship (optional - for registered users)
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='reservations',
		help_text="Linked user account (if registered)"
	)
	
	# Timestamps
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	
	class Meta:
		ordering = ['reservation_date', 'reservation_time']
		verbose_name = 'Reservation'
		verbose_name_plural = 'Reservations'
		indexes = [
			models.Index(fields=['reservation_date', 'reservation_time']),
			models.Index(fields=['table']),
			models.Index(fields=['status']),
			models.Index(fields=['customer_email']),
			models.Index(fields=['user']),
		]
		constraints = [
			# Prevent same table being reserved at exact same date and start time
			models.UniqueConstraint(
				fields=['table', 'reservation_date', 'reservation_time'],
				name='unique_table_datetime'
			)
		]
	
	def __str__(self):
		return f"{self.customer_name} - Table {self.table.number} on {self.reservation_date} at {self.reservation_time}"
	
	@property
	def reservation_datetime(self):
		"""Combine date and time into a single datetime object."""
		return timezone.make_aware(
			datetime.combine(self.reservation_date, self.reservation_time)
		)
	
	@property
	def end_datetime(self):
		"""Calculate when the reservation ends."""
		return self.reservation_datetime + timedelta(minutes=self.duration_minutes)
	
	@property
	def is_past(self):
		"""Check if reservation is in the past."""
		return self.reservation_datetime < timezone.now()
	
	@property
	def is_upcoming(self):
		"""Check if reservation is in the future."""
		return self.reservation_datetime > timezone.now()
	
	def clean(self):
		"""
		Validate reservation data.
		Prevents reservations in the past and ensures party size doesn't exceed table capacity.
		"""
		# Prevent reservations in the past
		if hasattr(self, 'reservation_date') and hasattr(self, 'reservation_time'):
			reservation_dt = timezone.make_aware(
				datetime.combine(self.reservation_date, self.reservation_time)
			)
			if reservation_dt < timezone.now():
				raise ValidationError("Cannot create a reservation for a past date and time.")
		
		# Ensure party size doesn't exceed table capacity
		if hasattr(self, 'table') and hasattr(self, 'party_size'):
			if self.party_size > self.table.capacity:
				raise ValidationError(
					f"Party size ({self.party_size}) exceeds table capacity ({self.table.capacity})."
				)
		
		# Validate duration is reasonable
		if hasattr(self, 'duration_minutes'):
			if self.duration_minutes < 30:
				raise ValidationError("Reservation duration must be at least 30 minutes.")
			if self.duration_minutes > 480:  # 8 hours max
				raise ValidationError("Reservation duration cannot exceed 8 hours.")
	
	def save(self, *args, **kwargs):
		"""Override save to run validation."""
		self.full_clean()
		super().save(*args, **kwargs)
	
	@classmethod
	def find_available_slots(cls, table, start_datetime, end_datetime, duration_minutes=120, slot_interval_minutes=30):
		"""
		Find available reservation time slots for a specific table within a date/time range.
		
		This method efficiently identifies time slots where the table is not already reserved,
		taking into account existing reservations and their durations.
		
		Args:
			table: Table instance to check availability for
			start_datetime: Start of the search range (datetime object)
			end_datetime: End of the search range (datetime object)
			duration_minutes: Duration of the desired reservation (default: 120 minutes)
			slot_interval_minutes: Interval between potential slots (default: 30 minutes)
		
		Returns:
			List of dictionaries containing available slots with start and end times:
			[
				{
					'start_time': datetime object,
					'end_time': datetime object,
					'formatted_start': '2025-01-15 18:00',
					'formatted_end': '2025-01-15 20:00'
				},
				...
			]
		
		Example:
			>>> from datetime import datetime
			>>> from django.utils import timezone
			>>> table = Table.objects.get(number=5)
			>>> start = timezone.make_aware(datetime(2025, 1, 15, 17, 0))
			>>> end = timezone.make_aware(datetime(2025, 1, 15, 22, 0))
			>>> slots = Reservation.find_available_slots(table, start, end, duration_minutes=120)
			>>> print(slots)
			[
				{'start_time': datetime(...), 'end_time': datetime(...), ...},
				...
			]
		"""
		# Ensure we're working with aware datetimes
		if timezone.is_naive(start_datetime):
			start_datetime = timezone.make_aware(start_datetime)
		if timezone.is_naive(end_datetime):
			end_datetime = timezone.make_aware(end_datetime)
		
		# Don't allow searching for slots in the past
		now = timezone.now()
		if start_datetime < now:
			start_datetime = now
		
		# If the entire range is in the past, return empty list
		if end_datetime <= now:
			return []
		
		# Get all confirmed/pending reservations for this table in the date range
		# Expand the date range by one day on each side to catch reservations that
		# start the previous day but extend into our search window (overnight overlaps)
		search_start_date = start_datetime.date() - timedelta(days=1)
		search_end_date = end_datetime.date() + timedelta(days=1)
		
		existing_reservations = cls.objects.filter(
			table=table,
			reservation_date__gte=search_start_date,
			reservation_date__lte=search_end_date,
			status__in=['pending', 'confirmed']
		).select_related('table')
		
		# Build a list of occupied time ranges
		occupied_ranges = []
		for reservation in existing_reservations:
			res_start = reservation.reservation_datetime
			res_end = reservation.end_datetime
			occupied_ranges.append((res_start, res_end))
		
		# Generate potential time slots
		available_slots = []
		current_slot_start = start_datetime
		slot_duration = timedelta(minutes=duration_minutes)
		slot_interval = timedelta(minutes=slot_interval_minutes)
		
		while current_slot_start + slot_duration <= end_datetime:
			slot_end = current_slot_start + slot_duration
			
			# Check if this slot overlaps with any existing reservation
			is_available = True
			for occupied_start, occupied_end in occupied_ranges:
				# Check for overlap: slot overlaps if it starts before occupied ends
				# and ends after occupied starts
				if (current_slot_start < occupied_end and slot_end > occupied_start):
					is_available = False
					break
			
			if is_available:
				available_slots.append({
					'start_time': current_slot_start,
					'end_time': slot_end,
					'formatted_start': current_slot_start.strftime('%Y-%m-%d %H:%M'),
					'formatted_end': slot_end.strftime('%Y-%m-%d %H:%M'),
				})
			
			# Move to next potential slot
			current_slot_start += slot_interval
		
		return available_slots
