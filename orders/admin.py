from django.contrib import admin
from django.contrib import messages
from .models import Customer, Order, OrderStatus
from .choices import OrderStatusChoices


def mark_orders_processed(modeladmin, request, queryset):
    """
    Custom admin action to mark selected orders as 'Processed' (Processing status).
    
    This action allows administrators to bulk update multiple orders to the 
    'Processing' status in one operation, streamlining order management workflows.
    
    Args:
        modeladmin: The ModelAdmin instance
        request: The current HttpRequest object
        queryset: QuerySet of selected Order objects to update
    
    Returns:
        None - Updates are applied directly and success message is displayed
    """
    # Get or create the Processing status
    processing_status, created = OrderStatus.objects.get_or_create(
        name=OrderStatusChoices.PROCESSING
    )
    
    # Count how many orders were actually updated
    updated_count = queryset.exclude(status=processing_status).count()
    
    # Update the selected orders to Processing status
    queryset.update(status=processing_status)
    
    # Provide feedback to the admin user
    if updated_count == 0:
        modeladmin.message_user(
            request,
            "All selected orders were already in 'Processing' status.",
            level=messages.WARNING
        )
    elif updated_count == 1:
        modeladmin.message_user(
            request,
            "1 order was successfully marked as 'Processing'.",
            level=messages.SUCCESS
        )
    else:
        modeladmin.message_user(
            request,
            f"{updated_count} orders were successfully marked as 'Processing'.",
            level=messages.SUCCESS
        )


# Set a user-friendly display name for the action
mark_orders_processed.short_description = "Mark selected orders as Processed"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Enhanced Django admin configuration for the Order model.
    
    Provides a comprehensive admin interface with custom actions, filtering,
    searching, and display options for efficient order management.
    """
    
    # Register the custom action
    actions = [mark_orders_processed]
    
    # Display these fields in the list view
    list_display = [
        'order_id',
        'customer',
        'user',
        'status',
        'total_amount',
        'created_at',
        'updated_at'
    ]
    
    # Add filters for easy data segmentation
    list_filter = [
        'status',
        'created_at',
        'updated_at'
    ]
    
    # Enable search functionality
    search_fields = [
        'order_id',
        'customer__name',
        'customer__email',
        'user__username',
        'user__email'
    ]
    
    # Set default ordering (most recent first)
    ordering = ['-created_at']
    
    # Make certain fields read-only
    readonly_fields = [
        'order_id',
        'created_at',
        'updated_at'
    ]
    
    # Optimize database queries
    list_select_related = ['customer', 'user', 'status']
    
    # Number of items per page
    list_per_page = 25


# Register Customer with basic admin
admin.site.register(Customer)
