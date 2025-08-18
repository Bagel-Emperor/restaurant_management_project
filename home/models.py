from django.db import models

class Restaurant(models.Model):
	name = models.CharField(max_length=100, unique=True)
	owner_name = models.CharField(max_length=100)
	email = models.EmailField(unique=True)
	phone_number = models.CharField(max_length=20)
	address = models.CharField(max_length=255)
	city = models.CharField(max_length=100)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.name

class MenuItem(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menu_items')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name