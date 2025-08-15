from rest_framework import serializers
from .models import Restaurant

class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = [
            'id',
            'name',
            'owner_name',
            'email',
            'phone_number',
            'address',
            'city',
            'created_at',
        ]
        read_only_fields = ['created_at']
