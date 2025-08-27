from django.db import models

# Model to store restaurant location details, linked to Restaurant
class Restaurant(models.Model):
	name = models.CharField(max_length=100, unique=True)
	owner_name = models.CharField(max_length=100)
	email = models.EmailField(unique=True)
	phone_number = models.CharField(max_length=20)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.name

# Model to store contact form submissions
class ContactSubmission(models.Model):
	name = models.CharField(max_length=100)
	email = models.EmailField()
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
from django.db import models


class MenuItem(models.Model):
	name = models.CharField(max_length=100)
	description = models.TextField(blank=True)
	price = models.DecimalField(max_digits=6, decimal_places=2)
	restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menu_items')
	is_available = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.name

class Feedback(models.Model):
	comment = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Feedback {self.id} at {self.created_at}" if self.id else "Feedback"