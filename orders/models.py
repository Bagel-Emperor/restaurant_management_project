
from django.db import models

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
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
	total_amount = models.DecimalField(max_digits=8, decimal_places=2)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Order {self.id} - {self.status}"
