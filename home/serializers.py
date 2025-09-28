from rest_framework import serializers
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Restaurant, MenuItem, MenuCategory, ContactSubmission

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


class ContactSubmissionSerializer(serializers.ModelSerializer):
    """
    Serializer for ContactSubmission model.
    Handles validation for contact form submissions via DRF API.
    Provides comprehensive validation for name, email, and message fields.
    """
    
    class Meta:
        model = ContactSubmission
        fields = ['id', 'name', 'email', 'message', 'submitted_at']
        read_only_fields = ['id', 'submitted_at']
    
    def validate_name(self, value):
        """
        Validate contact name field.
        Ensures name is present, not empty, and within reasonable length.
        """
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Name is required and cannot be empty.")
        
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long.")
        
        if len(value.strip()) > 100:
            raise serializers.ValidationError("Name cannot exceed 100 characters.")
        
        return value.strip()
    
    def validate_email(self, value):
        """
        Validate email field using Django's built-in email validation.
        Provides detailed error messages for invalid email formats.
        """
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Email is required.")
        
        # Use Django's built-in email validator
        try:
            validate_email(value)
        except DjangoValidationError:
            raise serializers.ValidationError("Please enter a valid email address.")
        
        return value.lower().strip()
    
    def validate_message(self, value):
        """
        Validate message field.
        Ensures message is present and within reasonable length limits.
        """
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Message is required and cannot be empty.")
        
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Message must be at least 10 characters long.")
        
        if len(value.strip()) > 2000:
            raise serializers.ValidationError("Message cannot exceed 2000 characters.")
        
        return value.strip()
    
    def create(self, validated_data):
        """
        Create and return a new ContactSubmission instance.
        """
        return ContactSubmission.objects.create(**validated_data)