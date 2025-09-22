from rest_framework import serializers
from .models import Restaurant, MenuItem, MenuCategory

# Serializer for MenuCategory
class MenuCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuCategory
        fields = ['id', 'name']

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
    Includes custom validation for price and availability.
    """
    category_name = serializers.SerializerMethodField()
    
    class Meta:
        model = MenuItem
        fields = [
            'id',
            'name',
            'description',
            'price',
            'restaurant',
            'category',
            'category_name',
            'is_available',
            'image',
            'created_at',
        ]
        read_only_fields = ['created_at']
    
    def get_category_name(self, obj):
        """
        Get the category name, returning None if no category is assigned.
        """
        return obj.category.name if obj.category else None
    
    def validate_price(self, value):
        """
        Ensure price is a positive number.
        """
        if value <= 0:
            raise serializers.ValidationError("Price must be a positive number.")
        return value
    
    def validate_name(self, value):
        """
        Ensure name is not empty and has reasonable length.
        """
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Name cannot be empty.")
        if len(value.strip()) > 100:
            raise serializers.ValidationError("Name cannot exceed 100 characters.")
        return value.strip()