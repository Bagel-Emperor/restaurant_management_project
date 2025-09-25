from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Customer, Order, OrderItem, OrderStatus, UserProfile
from home.models import MenuItem
from restaurant_management.utils import is_valid_email, normalize_email, validate_email_with_details

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'phone', 'email', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_email(self, value):
        """Validate email using our custom email validation utility"""
        if value:
            # Normalize the email
            value = normalize_email(value)
            
            # Validate email format with detailed error messages
            is_valid, error_message = validate_email_with_details(value)
            if not is_valid:
                raise serializers.ValidationError(error_message)
        
        return value


class MenuItemSerializer(serializers.ModelSerializer):
    """Serializer for MenuItem used in order items"""
    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'price']


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem with nested MenuItem details"""
    menu_item = MenuItemSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'menu_item', 'quantity', 'price', 'total_price']
    
    def get_total_price(self, obj):
        return obj.quantity * obj.price


class OrderStatusSerializer(serializers.ModelSerializer):
    """Serializer for OrderStatus"""
    class Meta:
        model = OrderStatus
        fields = ['id', 'name']


# Serializer for listing orders
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'status', 'total_amount', 'created_at']
        read_only_fields = ['id', 'created_at']


class OrderHistorySerializer(serializers.ModelSerializer):
    """Comprehensive serializer for user order history with nested items"""
    order_items = OrderItemSerializer(many=True, read_only=True)
    status = OrderStatusSerializer(read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['id', 'created_at', 'total_amount', 'status', 'items_count', 'order_items']
        read_only_fields = ['id', 'created_at', 'total_amount']
    
    def get_items_count(self, obj):
        return obj.order_items.count()


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile with nested User fields.
    Allows updating both UserProfile and related User information.
    """
    # User fields that can be updated
    first_name = serializers.CharField(source='user.first_name', max_length=150, allow_blank=True)
    last_name = serializers.CharField(source='user.last_name', max_length=150, allow_blank=True)
    email = serializers.EmailField(source='user.email')
    username = serializers.CharField(source='user.username', read_only=True)
    
    # UserProfile fields
    name = serializers.CharField(max_length=100, allow_blank=True)
    phone = serializers.CharField(max_length=20, allow_blank=True)
    
    # Computed field
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'name', 'phone', 'full_name']
        read_only_fields = ['id', 'username', 'full_name']
    
    def validate_email(self, value):
        """Validate email using our custom email validation utility"""
        if value:
            # Normalize the email
            value = normalize_email(value)
            
            # Validate email format with detailed error messages
            is_valid, error_message = validate_email_with_details(value)
            if not is_valid:
                raise serializers.ValidationError(error_message)
            
            # Check if email is already taken by another user
            user = self.instance.user if self.instance else None
            if User.objects.filter(email=value).exclude(pk=user.pk if user else None).exists():
                raise serializers.ValidationError("A user with this email already exists.")
        
        return value
    
    def update(self, instance, validated_data):
        """
        Update both UserProfile and related User fields.
        """
        # Extract user data from validated_data
        user_data = validated_data.pop('user', {})
        
        # Update User fields
        user = instance.user
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()
        
        # Update UserProfile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance
    
    def get_full_name(self, obj):
        """
        Compute the full name from User's first/last name, fallback to profile name or username.
        """
        return obj.user.get_full_name() or obj.name or obj.user.username
