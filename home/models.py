from django.db import models

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
	is_available = models.BooleanField(default=True)
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