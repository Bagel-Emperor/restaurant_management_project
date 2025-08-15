from django.db import models

class Restaurant(models.Model):
	name = models.CharField(max_length=100)
	owner_name = models.CharField(max_length=100)
	email = models.EmailField(unique=True)
	phone_number = models.CharField(max_length=20)
	address = models.CharField(max_length=255)
	city = models.CharField(max_length=100)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.name
