from rest_framework import serializers
from .models import Customer, Order

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'phone', 'email', 'created_at']
        read_only_fields = ['id', 'created_at']


# Serializer for listing orders
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'status', 'total_amount', 'created_at']
        read_only_fields = ['id', 'created_at']
