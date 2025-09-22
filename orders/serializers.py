from rest_framework import serializers
from .models import Customer, Order, OrderItem, OrderStatus
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
