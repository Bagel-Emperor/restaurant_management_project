from rest_framework import serializers
from .models import Restaurant, MenuItem

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

class MenuItemSerializer(serializers.ModelSerializer):
    """
    Serializer for MenuItem model.
    Converts MenuItem instances to JSON and validates input for creation/update.
    """
    class Meta:
        model = MenuItem
        fields = [
            'id',
            'name',
            'description',
            'price',
            'restaurant',
            'created_at',
        ]
        read_only_fields = ['created_at']